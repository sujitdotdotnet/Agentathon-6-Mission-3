"""
seed_hr_db.py - Initialize and seed local SQLite database for Nexura Technologies HR Operations.
Software Service Company domain, HR Policies sub-domain.
"""

import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hr_portal.db")


def init_and_seed_db(db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Employees table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        emp_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        role TEXT NOT NULL,
        department TEXT NOT NULL,
        band TEXT NOT NULL,
        location TEXT NOT NULL,
        joining_date TEXT NOT NULL,
        employment_status TEXT NOT NULL,
        manager_name TEXT NOT NULL,
        monthly_gross_inr INTEGER NOT NULL
    )
    """)

    # 2. Leave balances table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS leave_balances (
        emp_id TEXT PRIMARY KEY,
        pto_days REAL NOT NULL,
        sick_days REAL NOT NULL,
        maternity_days INTEGER NOT NULL,
        paternity_days INTEGER NOT NULL,
        bereavement_days INTEGER NOT NULL,
        floating_holidays INTEGER NOT NULL,
        FOREIGN KEY (emp_id) REFERENCES employees(emp_id)
    )
    """)

    # 3. HR Policies table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS hr_policies (
        policy_code TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        summary TEXT NOT NULL,
        full_text TEXT NOT NULL
    )
    """)

    # 4. Office Holidays table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS office_holidays (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        location TEXT NOT NULL,
        holiday_date TEXT NOT NULL,
        holiday_name TEXT NOT NULL,
        holiday_type TEXT NOT NULL
    )
    """)

    # 5. Leave Applications table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS leave_applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        emp_id TEXT NOT NULL,
        leave_type TEXT NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT NOT NULL,
        days_requested REAL NOT NULL,
        reason TEXT NOT NULL,
        status TEXT NOT NULL,
        applied_on TEXT NOT NULL,
        FOREIGN KEY (emp_id) REFERENCES employees(emp_id)
    )
    """)

    # 6. Expense Claims table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS expense_claims (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        emp_id TEXT NOT NULL,
        category TEXT NOT NULL,
        amount_inr REAL NOT NULL,
        description TEXT NOT NULL,
        status TEXT NOT NULL,
        submitted_on TEXT NOT NULL,
        FOREIGN KEY (emp_id) REFERENCES employees(emp_id)
    )
    """)

    # Seed Employees (Clear and re-seed if empty)
    cursor.execute("SELECT COUNT(*) FROM employees")
    if cursor.fetchone()[0] == 0:
        employees_data = [
            ("EMP101", "Aarav Mehta", "aarav.mehta@nexuratech.com", "Senior Full-Stack Engineer", "Engineering", "L5", "Bengaluru", "2022-03-15", "Confirmed", "Vikram Malhotra", 185000),
            ("EMP102", "Priya Sharma", "priya.sharma@nexuratech.com", "Principal Solutions Architect", "Architecture", "L6", "Pune", "2021-08-01", "Confirmed", "Siddharth Verma", 260000),
            ("EMP103", "Rohan Kulkarni", "rohan.kulkarni@nexuratech.com", "QA Automation Engineer", "Quality Engineering", "L4", "Hyderabad", "2024-02-10", "Confirmed", "Neha Sen", 95000),
            ("EMP104", "Ananya Iyer", "ananya.iyer@nexuratech.com", "Associate Software Engineer", "Frontend", "L3", "Bengaluru", "2026-08-01", "Probation", "Aarav Mehta", 65000),
            ("EMP105", "Devansh Gupta", "devansh.gupta@nexuratech.com", "Senior DevOps Engineer", "Platform Infrastructure", "L5", "Bengaluru", "2023-11-20", "Notice Period", "Vikram Malhotra", 175000),
            ("EMP106", "Jessica Taylor", "jessica.taylor@nexuratech.com", "Technical Client Partner", "Client Solutions", "L5", "Sunnyvale", "2022-06-15", "Confirmed", "Rachel Adams", 450000),
        ]
        cursor.executemany("""
        INSERT INTO employees VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, employees_data)

        # Seed Leave Balances
        leave_data = [
            ("EMP101", 14.5, 7.0, 0, 15, 5, 2),
            ("EMP102", 22.0, 9.5, 180, 0, 5, 1),
            ("EMP103", 11.0, 4.0, 0, 15, 5, 2),
            ("EMP104", 0.0, 2.0, 0, 0, 5, 0),   # In probation: 0 PTO accrual until confirmation, 2 days emergency sick
            ("EMP105", 3.0, 1.0, 0, 15, 5, 0),   # Notice period
            ("EMP106", 18.0, 8.0, 180, 0, 5, 2),
        ]
        cursor.executemany("""
        INSERT INTO leave_balances VALUES (?, ?, ?, ?, ?, ?, ?)
        """, leave_data)

        # Seed HR Policies
        policies_data = [
            (
                "POL-WFH-01",
                "Hybrid Work, Remote Attendance & Home Office Setup",
                "Remote Work",
                "Guidelines for 3 days in-office / 2 days WFH, core hours, ergonomic allowance, and internet reimbursement.",
                """1. HYBRID MODEL: Nexura Technologies operates on a 3:2 hybrid model. All software engineering and delivery personnel must work from their designated base development center at least 3 days per week (Tuesday to Thursday mandatory for co-located sprints). Mondays and Fridays are flexible work-from-home days.
2. CORE COLLABORATION HOURS: All remote and in-office staff must be available on Slack and Google Meet during core collaboration hours: 10:30 AM to 4:30 PM IST.
3. ERGONOMIC SETUP ALLOWANCE:
   - Band L5 (Senior Engineer) & L6 (Principal/Architect): Up to INR 25,000 one-time reimbursement for external monitors, ergonomic chair, desk, or power UPS.
   - Band L3 & L4 (Associate & Software Engineer): Up to INR 15,000 one-time reimbursement.
   - Bills must be submitted within 60 days of joining or policy announcement.
4. MONTHLY INTERNET REIMBURSEMENT: Up to INR 1,500 per month for high-speed home broadband (minimum 100 Mbps connection). Invoices must be submitted via the expense portal by the 25th of each month."""
            ),
            (
                "POL-LV-02",
                "Comprehensive Leave Policy, Accrual & Sandwich Rule",
                "Leave & Absence",
                "Entitlements for Paid Time Off (PTO), Sick Leave, Sandwich Rule, and probation restrictions.",
                """1. PAID TIME OFF (PTO): Full-time confirmed employees receive 20 days of PTO per calendar year, accrued at 5 days per quarter. Up to 15 unused PTO days can be rolled over to the next calendar year. Any excess beyond 15 days is automatically encashed at basic salary rates on December 31.
2. CASUAL & SICK LEAVE: 10 days credited at the start of the calendar year. A medical certificate from a registered MBBS practitioner is mandatory for sick leaves exceeding 2 consecutive working days.
3. PROBATIONARY EMPLOYEES: Employees in their initial 6-month probation period do NOT accrue usable annual PTO. During probation, employees are eligible for a maximum of 2 days emergency casual leave. Taking unearned leaves requires VP HR approval and is treated as Loss of Pay (LOP).
4. SANDWICH RULE: When leave is taken on Friday and Monday, intervening weekends (Saturday and Sunday) are NOT deducted if the employee has sufficient approved PTO balance. However, if the leave is unpaid (LOP), weekends ARE counted as sandwich days and deducted from pay.
5. ADVANCE NOTICE: Planned leaves of 3 or more consecutive working days must be submitted at least 10 working days in advance in the portal."""
            ),
            (
                "POL-NOT-03",
                "Resignation, Notice Period & Shortfall Buyout Guidelines",
                "Separation & Notice",
                "Rules regarding 90-day notice periods, early release buyouts, and exit clearance.",
                """1. STANDARD NOTICE PERIOD:
   - Confirmed Employees (Bands L3 to L6): 90 calendar days mandatory notice period.
   - Employees in Probation: 30 calendar days notice period.
2. NOTICE SHORTFALL BUYOUT: If an employee requests an early release before completing their notice period:
   - Buyout Formula: Shortfall Cost = (Monthly Gross Salary / 30) * Shortfall Days.
   - Buyout is NOT an unconditional right of the employee. It requires explicit written approval from the Delivery Unit Head (DUH) and Project Manager confirming 100% Knowledge Transfer (KT) completion and client signoff.
3. LEAVES DURING NOTICE: Employees serving notice are NOT permitted to avail PTO during their final 30 calendar days, except for verified medical emergencies approved by HR."""
            ),
            (
                "POL-EXP-04",
                "Travel, Client Visits, Meals & Certification Reimbursements",
                "Travel & Expense",
                "Per diem rates, hotel booking caps, domestic client travel, and technical certification sponsorship.",
                """1. DOMESTIC TRAVEL & ACCOMMODATION:
   - Tier-1 Metro Cities (Bengaluru, Mumbai, Delhi-NCR, Hyderabad): Hotel room tariff capped at INR 6,500/night for Bands L3-L5; INR 9,500/night for Band L6+.
   - Tier-2 Cities (Pune, Kochi, Jaipur, Chandigarh): Capped at INR 4,500/night for all engineering bands.
2. DAILY FOOD PER DIEM: Daily meal allowance of INR 1,500 per day during official travel. Individual bills are required. Alcohol is strictly non-reimbursable.
3. PROFESSIONAL CERTIFICATIONS: Nexura encourages professional growth. Confirmed employees can claim 100% reimbursement up to INR 50,000 per financial year for approved cloud certifications (AWS Solutions Architect, Google Cloud Professional Architect, CKA/CKAD, Azure Solutions Architect) upon submitting a passing score certificate."""
            ),
            (
                "POL-INS-05",
                "Group Health Insurance, Parental Coverage & Wellness",
                "Health & Benefits",
                "Medical coverage limits, parental insurance add-ons, and outpatient dental/optical benefits.",
                """1. BASE HEALTH INSURANCE: Company provides 100% employer-sponsored Group Mediclaim Insurance of INR 5,00,000 family floater coverage covering Employee, Spouse, and up to 2 dependent children.
2. PARENTAL COVERAGE: Employees can enroll dependent parents or parents-in-law for an additional floater sum insured of INR 5,00,000 or INR 10,00,000. Nexura subsidizes 80% of the parental premium; 20% is deducted in monthly payroll installments. 1-year waiting period for pre-existing conditions is waived.
3. OUTPATIENT (OPD) DENTAL & OPTICAL: Annual outpatient dental and vision allowance of INR 12,000 per family reimbursable against clinic bills.
4. ANNUAL EXECUTIVE HEALTH CHECKUP: Free comprehensive annual health checkup at partner diagnostic chains (Apollo, Manipal, Suburban Diagnostics) for all employees aged 30 and above."""
            ),
            (
                "POL-APP-06",
                "Annual Performance Review, Merit Hikes & Promotion Criteria",
                "Performance & Appraisal",
                "Appraisal timeline, evaluation ratings 1-5, hike brackets, and promotion eligibility.",
                """1. PERFORMANCE CYCLE: The annual appraisal cycle runs from April 1 to March 31. Mid-year check-ins occur in October, self-evaluations open in April, and revised compensation becomes effective July 1 with arrears from April.
2. TENURE ELIGIBILITY: Employees must have completed at least 6 months of continuous service prior to March 31 to participate in the current merit hike cycle.
3. RATING SCALE & MERIT HIKE BRACKETS:
   - Rating 5 (Outstanding / Top 10%): 18% to 25% salary hike + performance bonus.
   - Rating 4 (Exceeds Expectations): 12% to 17% salary hike.
   - Rating 3 (Meets Expectations / Solid Contributor): 8% to 11% salary hike.
   - Rating 2 (Partially Meets): 0% to 4% salary hike + 60-day development plan.
   - Rating 1 (Unsatisfactory): 0% hike + immediate 30-day Performance Improvement Plan (PIP)."""
            )
        ]
        cursor.executemany("""
        INSERT INTO hr_policies VALUES (?, ?, ?, ?, ?)
        """, policies_data)

        # Seed Office Holidays for 2026
        holidays_data = [
            # Bengaluru
            ("Bengaluru", "2026-01-26", "Republic Day", "Mandatory"),
            ("Bengaluru", "2026-03-04", "Holi", "Mandatory"),
            ("Bengaluru", "2026-03-20", "Ugadi / Gudi Padwa", "Mandatory"),
            ("Bengaluru", "2026-05-01", "May Day", "Mandatory"),
            ("Bengaluru", "2026-08-15", "Independence Day", "Mandatory"),
            ("Bengaluru", "2026-09-14", "Ganesh Chaturthi", "Mandatory"),
            ("Bengaluru", "2026-10-02", "Gandhi Jayanti", "Mandatory"),
            ("Bengaluru", "2026-10-20", "Dussehra / Vijaya Dashami", "Mandatory"),
            ("Bengaluru", "2026-11-01", "Kannada Rajyotsava", "Mandatory"),
            ("Bengaluru", "2026-11-09", "Diwali / Deepavali", "Mandatory"),
            ("Bengaluru", "2026-12-25", "Christmas", "Mandatory"),
            ("Bengaluru", "2026-04-14", "Dr. Ambedkar Jayanti", "Floating"),
            ("Bengaluru", "2026-11-10", "Diwali Balipadyami", "Floating"),

            # Pune
            ("Pune", "2026-01-26", "Republic Day", "Mandatory"),
            ("Pune", "2026-03-04", "Holi / Dhulivandan", "Mandatory"),
            ("Pune", "2026-03-20", "Gudi Padwa", "Mandatory"),
            ("Pune", "2026-05-01", "Maharashtra Day", "Mandatory"),
            ("Pune", "2026-08-15", "Independence Day", "Mandatory"),
            ("Pune", "2026-09-14", "Ganesh Chaturthi", "Mandatory"),
            ("Pune", "2026-10-02", "Gandhi Jayanti", "Mandatory"),
            ("Pune", "2026-10-20", "Dussehra", "Mandatory"),
            ("Pune", "2026-11-09", "Diwali Laxmi Pujan", "Mandatory"),
            ("Pune", "2026-12-25", "Christmas", "Mandatory"),

            # Hyderabad
            ("Hyderabad", "2026-01-26", "Republic Day", "Mandatory"),
            ("Hyderabad", "2026-03-04", "Holi", "Mandatory"),
            ("Hyderabad", "2026-03-20", "Ugadi", "Mandatory"),
            ("Hyderabad", "2026-06-02", "Telangana Formation Day", "Mandatory"),
            ("Hyderabad", "2026-08-15", "Independence Day", "Mandatory"),
            ("Hyderabad", "2026-10-02", "Gandhi Jayanti", "Mandatory"),
            ("Hyderabad", "2026-10-20", "Vijaya Dashami", "Mandatory"),
            ("Hyderabad", "2026-11-09", "Diwali", "Mandatory"),
            ("Hyderabad", "2026-12-25", "Christmas", "Mandatory"),

            # Sunnyvale
            ("Sunnyvale", "2026-01-01", "New Year's Day", "Mandatory"),
            ("Sunnyvale", "2026-01-19", "Martin Luther King Jr. Day", "Mandatory"),
            ("Sunnyvale", "2026-05-25", "Memorial Day", "Mandatory"),
            ("Sunnyvale", "2026-06-19", "Juneteenth", "Mandatory"),
            ("Sunnyvale", "2026-07-03", "Independence Day Observed", "Mandatory"),
            ("Sunnyvale", "2026-09-07", "Labor Day", "Mandatory"),
            ("Sunnyvale", "2026-11-26", "Thanksgiving Day", "Mandatory"),
            ("Sunnyvale", "2026-11-27", "Day After Thanksgiving", "Mandatory"),
            ("Sunnyvale", "2026-12-25", "Christmas Day", "Mandatory"),
        ]
        cursor.executemany("""
        INSERT INTO office_holidays (location, holiday_date, holiday_name, holiday_type)
        VALUES (?, ?, ?, ?)
        """, holidays_data)

    conn.commit()
    conn.close()
    print(f"[OK] Database seeded successfully at: {db_path}")


if __name__ == "__main__":
    init_and_seed_db()

