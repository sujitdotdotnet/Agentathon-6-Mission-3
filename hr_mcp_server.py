"""
hr_mcp_server.py - FastMCP Server for Nexura Technologies HR Policies & Operations.
Domain: Software Service Company
Sub-domain: HR Policies

Connects to the local SQLite database 'hr_portal.db' and exposes 7 high-impact MCP tools.
Can run standalone via stdio or SSE/Streamable HTTP.
"""

import datetime
import os
import sqlite3
from typing import Optional

from mcp.server.fastmcp import FastMCP

from seed_hr_db import DB_PATH, init_and_seed_db

# Ensure database is seeded
if not os.path.exists(DB_PATH):
    init_and_seed_db(DB_PATH)

# Initialize FastMCP Server
mcp = FastMCP("Nexura-HR-Policy-Server")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# =============================================================================
# MCP TOOLS
# =============================================================================

@mcp.tool()
def get_employee_info(identifier: str) -> str:
    """Fetch profile and employment details of an employee.
    
    Args:
        identifier: Employee ID (e.g. 'EMP101', 'EMP104') or employee name (e.g. 'Priya Sharma', 'Aarav').
    
    Returns:
        Formatted summary with employee ID, name, role, department, band (L3-L6), location,
        employment status (Confirmed/Probation/Notice Period), joining date, and manager.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
    SELECT * FROM employees 
    WHERE LOWER(emp_id) = LOWER(?) 
       OR LOWER(name) LIKE LOWER(?)
    """
    cursor.execute(query, (identifier.strip(), f"%{identifier.strip()}%"))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return f"No employee found matching '{identifier}'. Please check the employee ID (e.g., EMP101 to EMP106) or name."

    results = []
    for row in rows:
        info = (
            f"Employee Profile:\n"
            f"- Employee ID: {row['emp_id']}\n"
            f"- Name: {row['name']} ({row['email']})\n"
            f"- Role: {row['role']}\n"
            f"- Department: {row['department']}\n"
            f"- Career Band: {row['band']} (L3=Associate, L4=Software Eng, L5=Senior Eng, L6=Principal/Architect)\n"
            f"- Base Location: {row['location']}\n"
            f"- Joining Date: {row['joining_date']}\n"
            f"- Employment Status: {row['employment_status']}\n"
            f"- Reporting Manager: {row['manager_name']}\n"
            f"- Monthly Gross Salary: INR {row['monthly_gross_inr']:,}"
        )
        results.append(info)

    return "\n\n---\n\n".join(results)


@mcp.tool()
def get_leave_balance(emp_id: str) -> str:
    """Check remaining leave balances across all leave categories for an employee.
    
    Args:
        emp_id: The employee ID (e.g. 'EMP101', 'EMP102', 'EMP104').
    
    Returns:
        Detailed breakdown of PTO, Sick/Casual leave, Floating holidays, Maternity/Paternity,
        Bereavement leaves, along with probation rule status.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT e.emp_id, e.name, e.role, e.employment_status, e.band,
           l.pto_days, l.sick_days, l.maternity_days, l.paternity_days,
           l.bereavement_days, l.floating_holidays
    FROM employees e
    JOIN leave_balances l ON e.emp_id = l.emp_id
    WHERE LOWER(e.emp_id) = LOWER(?)
    """, (emp_id.strip(),))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return f"Employee ID '{emp_id}' not found in the leave management system."

    status_warning = ""
    if row["employment_status"] == "Probation":
        status_warning = (
            "\n\n[!] POLICY NOTICE (POL-LV-02): Employee is currently under probation. "
            "Annual PTO accrual is locked until confirmation. Only up to 2 emergency casual days "
            "can be availed with manager approval."
        )
    elif row["employment_status"] == "Notice Period":
        status_warning = (
            "\n\n[!] POLICY NOTICE (POL-NOT-03): Employee is serving notice period. "
            "Availing PTO during the final 30 calendar days is restricted without VP HR approval."
        )

    return (
        f"Leave Balances for {row['name']} ({row['emp_id']} - {row['role']}):\n"
        f"- Employment Status: {row['employment_status']}\n"
        f"- Paid Time Off (PTO / Vacation): {row['pto_days']} days\n"
        f"- Casual / Sick Leave: {row['sick_days']} days\n"
        f"- Floating / Optional Holidays: {row['floating_holidays']} days\n"
        f"- Paternity Leave: {row['paternity_days']} days\n"
        f"- Maternity Leave: {row['maternity_days']} days\n"
        f"- Bereavement Leave: {row['bereavement_days']} days"
        f"{status_warning}"
    )


@mcp.tool()
def apply_for_leave(emp_id: str, leave_type: str, start_date: str, end_date: str, reason: str) -> str:
    """Validate and submit a leave application according to company HR policy rules.
    
    Evaluates policy restrictions (probation limits, working days calculation excluding weekends,
    available balance check) and updates the database upon approval.
    
    Args:
        emp_id: The employee ID (e.g. 'EMP101', 'EMP104').
        leave_type: 'PTO', 'Sick', 'Floating', 'Paternity', 'Maternity', or 'Bereavement'.
        start_date: Start date in YYYY-MM-DD format (e.g. '2026-11-16').
        end_date: End date in YYYY-MM-DD format (e.g. '2026-11-20').
        reason: Purpose or justification for taking leave.
    
    Returns:
        Structured approval or rejection notice citing specific HR policy clauses.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM employees WHERE LOWER(emp_id) = LOWER(?)", (emp_id.strip(),))
    emp = cursor.fetchone()
    if not emp:
        conn.close()
        return f"Error: Employee '{emp_id}' does not exist in records."

    cursor.execute("SELECT * FROM leave_balances WHERE LOWER(emp_id) = LOWER(?)", (emp_id.strip(),))
    bal = cursor.fetchone()
    if not bal:
        conn.close()
        return f"Error: Leave balance record not found for '{emp_id}'."

    # Parse dates and count business days (excluding Sat and Sun)
    try:
        s_date = datetime.datetime.strptime(start_date.strip(), "%Y-%m-%d").date()
        e_date = datetime.datetime.strptime(end_date.strip(), "%Y-%m-%d").date()
    except ValueError:
        conn.close()
        return "Error: Invalid date format. Please provide dates in YYYY-MM-DD format (e.g. 2026-11-16)."

    if e_date < s_date:
        conn.close()
        return f"Error: End date ({end_date}) cannot be earlier than start date ({start_date})."

    working_days = 0
    cur_date = s_date
    while cur_date <= e_date:
        if cur_date.weekday() < 5:  # Monday to Friday
            working_days += 1
        cur_date += datetime.timedelta(days=1)

    if working_days == 0:
        conn.close()
        return f"Selected date range ({start_date} to {end_date}) falls entirely on weekends. No working days to deduct."

    # Normalize leave type
    l_type = leave_type.strip().lower()
    balance_column = None
    if "pto" in l_type or "vacation" in l_type or "annual" in l_type:
        balance_column = "pto_days"
        leave_name = "Paid Time Off (PTO)"
    elif "sick" in l_type or "casual" in l_type:
        balance_column = "sick_days"
        leave_name = "Sick/Casual Leave"
    elif "float" in l_type or "optional" in l_type:
        balance_column = "floating_holidays"
        leave_name = "Floating Holiday"
    elif "paternity" in l_type:
        balance_column = "paternity_days"
        leave_name = "Paternity Leave"
    elif "maternity" in l_type:
        balance_column = "maternity_days"
        leave_name = "Maternity Leave"
    elif "bereave" in l_type:
        balance_column = "bereavement_days"
        leave_name = "Bereavement Leave"
    else:
        conn.close()
        return f"Error: Unrecognized leave type '{leave_type}'. Allowed types: PTO, Sick, Floating, Paternity, Maternity, Bereavement."

    # Rule 1: Probation restrictions from POL-LV-02
    if emp["employment_status"] == "Probation":
        if balance_column == "pto_days":
            conn.close()
            return (
                f"[REJECTED] Policy POL-LV-02 Violation: Employee {emp['name']} is currently on Probation. "
                f"Employees on probation are NOT permitted to avail annual PTO/vacation days. "
                f"Only emergency casual/sick leave (max 2 days) is allowed with manager approval."
            )
        if balance_column == "sick_days" and working_days > 2:
            conn.close()
            return (
                f"[REJECTED] Policy POL-LV-02 Violation: Requested {working_days} days of Sick Leave exceeds the 2-day "
                f"maximum emergency limit allowed for employees during the probation period."
            )

    # Rule 2: Notice period restrictions from POL-NOT-03
    if emp["employment_status"] == "Notice Period" and balance_column == "pto_days":
        conn.close()
        return (
            f"[REJECTED] Policy POL-NOT-03 Violation: Employee {emp['name']} is serving notice period. "
            f"PTO is frozen during notice period to facilitate critical project knowledge transfer (KT)."
        )

    # Rule 3: Balance check
    current_bal = bal[balance_column]
    if current_bal < working_days:
        conn.close()
        return (
            f"[REJECTED] Insufficient Leave Balance: You requested {working_days} working day(s) of {leave_name}, "
            f"but current available balance is only {current_bal} day(s)."
        )

    # All checks passed: Deduct balance and record application
    new_bal = current_bal - working_days
    cursor.execute(f"UPDATE leave_balances SET {balance_column} = ? WHERE emp_id = ?", (new_bal, emp["emp_id"]))

    today_str = datetime.date.today().isoformat()
    cursor.execute("""
    INSERT INTO leave_applications (emp_id, leave_type, start_date, end_date, days_requested, reason, status, applied_on)
    VALUES (?, ?, ?, ?, ?, ?, 'Approved', ?)
    """, (emp["emp_id"], leave_name, start_date, end_date, working_days, reason, today_str))

    app_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return (
        f"[APPROVED] Leave Application #{app_id} Confirmed:\n"
        f"- Employee: {emp['name']} ({emp['emp_id']})\n"
        f"- Leave Type: {leave_name}\n"
        f"- Duration: {start_date} to {end_date} ({working_days} working day(s))\n"
        f"- Reason: {reason}\n"
        f"- Updated {leave_name} Balance: {new_bal} days remaining\n"
        f"- Automated Notification: Sent to Manager {emp['manager_name']}"
    )


@mcp.tool()
def search_company_policies(query: str) -> str:
    """Search official Nexura Technologies HR policy documents, clauses, and employee handbooks.
    
    Args:
        query: Search keywords or question (e.g. 'WFH ergonomic allowance', 'notice period buyout',
               'medical insurance parental', 'merit hike percentage', 'sandwich rule', 'probation').
    
    Returns:
        Matching policy codes, titles, summaries, and full clause texts.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    keywords = query.strip().split()
    conditions = []
    params = []
    for kw in keywords:
        conditions.append("(LOWER(title) LIKE LOWER(?) OR LOWER(summary) LIKE LOWER(?) OR LOWER(full_text) LIKE LOWER(?) OR LOWER(category) LIKE LOWER(?))")
        p = f"%{kw}%"
        params.extend([p, p, p, p])

    where_clause = " OR ".join(conditions) if conditions else "1=1"
    cursor.execute(f"SELECT * FROM hr_policies WHERE {where_clause}", params)
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return f"No policies found matching query '{query}'. Try searching for: 'wfh', 'leave', 'notice', 'travel', 'insurance', or 'appraisal'."

    output = []
    for row in rows:
        output.append(
            f"=== [{row['policy_code']}] {row['title']} ===\n"
            f"Category: {row['category']}\n"
            f"Summary: {row['summary']}\n\n"
            f"Official Clauses:\n{row['full_text']}"
        )

    return "\n\n" + ("=" * 70) + "\n\n".join(output)


@mcp.tool()
def calculate_notice_buyout(emp_id: str, shortfall_days: int) -> str:
    """Calculate the financial buyout amount for an employee requesting early release from notice period.
    
    Implements policy POL-NOT-03 buyout formula: (Monthly Gross Salary / 30) * Shortfall Days.
    
    Args:
        emp_id: The employee ID (e.g. 'EMP101', 'EMP102', 'EMP105').
        shortfall_days: Number of days the employee wants to leave early before fulfilling notice period.
    
    Returns:
        Detailed calculation breakdown including daily rate, total buyout amount, and approval prerequisites.
    """
    if shortfall_days <= 0:
        return "Error: Shortfall days must be greater than zero."

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM employees WHERE LOWER(emp_id) = LOWER(?)", (emp_id.strip(),))
    emp = cursor.fetchone()
    conn.close()

    if not emp:
        return f"Error: Employee '{emp_id}' not found."

    gross = emp["monthly_gross_inr"]
    daily_rate = gross / 30.0
    total_buyout = round(daily_rate * shortfall_days)

    standard_notice = 30 if emp["employment_status"] == "Probation" else 90

    return (
        f"Notice Period Shortfall Buyout Calculation for {emp['name']} ({emp['emp_id']}):\n"
        f"- Career Band: {emp['band']} | Role: {emp['role']}\n"
        f"- Employment Status: {emp['employment_status']}\n"
        f"- Mandatory Notice Period: {standard_notice} calendar days\n"
        f"- Requested Shortfall: {shortfall_days} days\n"
        f"- Monthly Gross Salary: INR {gross:,}\n"
        f"- Daily Gross Rate (Gross/30): INR {daily_rate:,.2f}\n"
        f"--------------------------------------------------\n"
        f"TOTAL ESTIMATED BUYOUT COST: INR {total_buyout:,}\n"
        f"--------------------------------------------------\n"
        f"Compliance Notes (POL-NOT-03):\n"
        f"1. Notice buyout is contingent upon complete Knowledge Transfer (KT) signoff by Manager {emp['manager_name']}.\n"
        f"2. The buyout amount is either recovered in Full & Final (F&F) settlement or paid by the new employer.\n"
        f"3. Applicable taxes (GST) will be calculated in the final exit voucher."
    )


@mcp.tool()
def get_office_holidays_calendar(location: str) -> str:
    """Get the official 2026 holiday calendar for a specific software development center.
    
    Args:
        location: City of the office: 'Bengaluru', 'Pune', 'Hyderabad', or 'Sunnyvale'.
    
    Returns:
        List of mandatory and optional/floating holidays with dates.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT holiday_date, holiday_name, holiday_type
    FROM office_holidays
    WHERE LOWER(location) = LOWER(?)
    ORDER BY holiday_date ASC
    """, (location.strip(),))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return f"No holiday records found for location '{location}'. Available centers: Bengaluru, Pune, Hyderabad, Sunnyvale."

    mandatory = []
    floating = []
    for r in rows:
        item = f"  * {r['holiday_date']} - {r['holiday_name']}"
        if r['holiday_type'] == 'Mandatory':
            mandatory.append(item)
        else:
            floating.append(item)

    result = [f"Official 2026 Holiday Schedule for {location.title()} Development Center:"]
    result.append("\n[Mandatory Holidays - Office Closed]:")
    result.extend(mandatory if mandatory else ["  * None recorded"])

    if floating:
        result.append("\n[Optional / Floating Holidays (Choose up to 2 per year)]:")
        result.extend(floating)

    return "\n".join(result)


@mcp.tool()
def submit_expense_reimbursement(emp_id: str, category: str, amount_inr: float, description: str) -> str:
    """Validate and log an expense claim against company policy caps (POL-EXP-04 & POL-WFH-01).
    
    Checks band-specific limits for Home Office Setup, Broadband Internet, Travel Hotel/Food,
    and Cloud Certifications.
    
    Args:
        emp_id: The employee ID (e.g. 'EMP101', 'EMP104').
        category: 'WFH Setup', 'Internet', 'Travel Hotel', 'Travel Food', or 'Certification'.
        amount_inr: Claim amount in Indian Rupees (INR).
        description: Merchant, itemized details, or bill invoice reference.
    
    Returns:
        Claim status (Auto-Approved for Payroll vs. Flagged for VP Approval) with policy citations.
    """
    if amount_inr <= 0:
        return "Error: Expense amount must be greater than zero."

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM employees WHERE LOWER(emp_id) = LOWER(?)", (emp_id.strip(),))
    emp = cursor.fetchone()
    if not emp:
        conn.close()
        return f"Error: Employee '{emp_id}' not found."

    band = emp["band"]
    cat = category.strip().lower()

    limit = 0.0
    policy_code = "POL-EXP-04"
    category_label = category

    if "wfh" in cat or "ergonomic" in cat or "home" in cat:
        policy_code = "POL-WFH-01"
        category_label = "Home Office Ergonomic Setup"
        limit = 25000.0 if band in ["L5", "L6"] else 15000.0
    elif "internet" in cat or "broadband" in cat or "wifi" in cat:
        policy_code = "POL-WFH-01"
        category_label = "Monthly Broadband Internet"
        limit = 1500.0
    elif "hotel" in cat or "stay" in cat or "accommodation" in cat:
        policy_code = "POL-EXP-04"
        category_label = "Travel Accommodation (Per Night)"
        limit = 9500.0 if band in ["L6"] else 6500.0
    elif "food" in cat or "meal" in cat or "per diem" in cat:
        policy_code = "POL-EXP-04"
        category_label = "Daily Food Allowance"
        limit = 1500.0
    elif "cert" in cat or "course" in cat or "exam" in cat:
        policy_code = "POL-EXP-04"
        category_label = "Technical Cloud Certification"
        limit = 50000.0
    else:
        conn.close()
        return (
            f"Error: Unknown expense category '{category}'. "
            f"Valid categories: 'WFH Setup', 'Internet', 'Travel Hotel', 'Travel Food', 'Certification'."
        )

    status = "Approved for Payroll" if amount_inr <= limit else "Flagged: Requires VP HR Exception Approval"

    today_str = datetime.date.today().isoformat()
    cursor.execute("""
    INSERT INTO expense_claims (emp_id, category, amount_inr, description, status, submitted_on)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (emp["emp_id"], category_label, amount_inr, description, status, today_str))

    claim_id = cursor.lastrowid
    conn.commit()
    conn.close()

    verdict_icon = "[OK]" if "Approved" in status else "[!]"
    return (
        f"{verdict_icon} Expense Claim #{claim_id} Recorded:\n"
        f"- Employee: {emp['name']} ({emp['emp_id']} - Band {band})\n"
        f"- Category: {category_label} ({policy_code})\n"
        f"- Claim Amount: INR {amount_inr:,.2f}\n"
        f"- Policy Cap for Band {band}: INR {limit:,.2f}\n"
        f"- Status: {status}\n"
        f"- Item Description: {description}"
    )


# =============================================================================
# Standalone execution
# =============================================================================
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Nexura HR Policy MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="MCP transport protocol (stdio, sse, streamable-http)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8001,
        help="Port for SSE or Streamable HTTP transport (default: 8001)"
    )
    args = parser.parse_args()

    if args.transport in ["sse", "streamable-http"]:
        mcp.settings.port = args.port
        mcp.settings.host = "127.0.0.1"
        print(f"[MCP] Starting {mcp.name} on http://127.0.0.1:{args.port} with {args.transport} transport...")

    mcp.run(transport=args.transport)


