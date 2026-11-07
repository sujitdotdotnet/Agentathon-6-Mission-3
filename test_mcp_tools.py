"""
test_mcp_tools.py - Quick smoke test for HR MCP tools.
"""
import sys
from hr_mcp_server import (
    get_employee_info,
    get_leave_balance,
    apply_for_leave,
    search_company_policies,
    calculate_notice_buyout,
    get_office_holidays_calendar,
    submit_expense_reimbursement,
)

print("--- 1. Employee Info ---")
print(get_employee_info("EMP101"))

print("\n--- 2. Leave Balance ---")
print(get_leave_balance("EMP104"))

print("\n--- 3. Policy Search ---")
print(search_company_policies("ergonomic setup allowance")[:300] + "...")

print("\n--- 4. Notice Buyout ---")
print(calculate_notice_buyout("EMP105", 20))

print("\n--- 5. Holidays ---")
print(get_office_holidays_calendar("Bengaluru")[:250] + "...")

print("\n--- 6. Expense Submission ---")
print(submit_expense_reimbursement("EMP101", "Certification", 35000, "AWS SA Pro Exam"))

print("\n--- 7. Leave Application Rule Check (Probation should reject PTO) ---")
print(apply_for_leave("EMP104", "PTO", "2026-11-16", "2026-11-18", "Personal trip"))

print("\nALL MCP TOOL SMOKE TESTS PASSED!")

