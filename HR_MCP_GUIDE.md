# Nexura Technologies — Enterprise HR Operations & Policy MCP Agent

This project implements a complete **Model Context Protocol (MCP)** application for a **Software Services Company** domain and **HR Policies & Operations** sub-domain, powered by the **DeepSeek API** and **Gradio**.

---

## 🚀 Quick Start

### 1. Web Chatbot (Gradio)
The Gradio application is running live at:
👉 **http://127.0.0.1:7860**

To start it manually at any time:
```bash
uv run hr_agent_app.py
```

### 2. Standalone MCP Server
The MCP server can be run independently using any of the following transports:

* **stdio** (default, standard I/O for local clients):
  ```bash
  uv run hr_mcp_server.py --transport stdio
  ```

* **Server-Sent Events (SSE)** (accessible over HTTP):
  ```bash
  uv run hr_mcp_server.py --transport sse --port 8001
  ```

* **Streamable HTTP**:
  ```bash
  uv run hr_mcp_server.py --transport streamable-http --port 8001
  ```

---

## 🔌 Connecting to Antigravity IDE (No Code)

You can also use this exact same HR MCP server directly inside Antigravity's chat panel!

1. Open your Antigravity MCP configuration:
   - Click the **...** menu at the top of the agent panel -> **MCP Servers** -> **Manage MCP Servers** -> **View raw config** (`mcp_config.json`).
2. Add the `nexura-hr-policy` entry to `mcpServers`:

```json
{
  "mcpServers": {
    "nexura-hr-policy": {
      "command": "uv",
      "args": ["run", "hr_mcp_server.py", "--transport", "stdio"]
    }
  }
}
```

3. Refresh your MCP Servers list. You will immediately see all 7 HR tools available inside Antigravity!

---

## 🗄️ Database Architecture (`hr_portal.db`)

Seeded via `seed_hr_db.py`:

| Table Name | Description |
|---|---|
| `employees` | Employee IDs, names, emails, roles, departments, career bands (L3–L6), base locations, joining dates, employment status, manager names, monthly gross salaries. |
| `leave_balances` | Real-time PTO, Sick/Casual, Maternity, Paternity, Bereavement, and Floating holiday days remaining. |
| `hr_policies` | Company policies with exact clause text: `POL-WFH-01`, `POL-LV-02`, `POL-NOT-03`, `POL-EXP-04`, `POL-INS-05`, `POL-APP-06`. |
| `office_holidays` | 2026 holiday schedules for Bengaluru, Pune, Hyderabad, and Sunnyvale centers. |
| `leave_applications` | Transactional table recording leave requests, business days deducted, approval status, and timestamps. |
| `expense_claims` | Transactional table recording WFH setup, internet, per diem, and cloud certification reimbursement claims. |

---

## 🛠️ The 7 MCP Tools

1. **`get_employee_info(identifier)`**:
   Fetches employee details by employee ID (e.g. `EMP101`) or name (e.g. `Priya Sharma`).
2. **`get_leave_balance(emp_id)`**:
   Provides breakdown of all remaining leaves, plus automated policy advisories for employees in probation or serving notice period.
3. **`apply_for_leave(emp_id, leave_type, start_date, end_date, reason)`**:
   Enforces policy rules:
   - Rejects annual PTO for probationary employees under `POL-LV-02` (only max 2 emergency days allowed).
   - Automatically excludes weekend days (Saturday & Sunday) when calculating deducted business days.
   - Rejects requests exceeding available balance.
   - Commits approved leaves directly to the SQLite database.
4. **`search_company_policies(query)`**:
   Full keyword and clause search across the company handbook. Cites exact policy numbers.
5. **`calculate_notice_buyout(emp_id, shortfall_days)`**:
   Computes exact financial buyout: `(Monthly Gross Salary / 30) * Shortfall Days`, and notes Delivery Unit Head KT sign-off prerequisites.
6. **`get_office_holidays_calendar(location)`**:
   Retrieves mandatory and optional floating holidays for any development center.
7. **`submit_expense_reimbursement(emp_id, category, amount_inr, description)`**:
   Validates claim amount against employee career band limits (e.g. ₹25,000 WFH setup for L5/L6 vs ₹15,000 for L3/L4; ₹50,000 for AWS/GCP certifications) and auto-flags exceptions for VP HR review.

---

## 💡 Why This Makes a Strong Case for MCP

1. **Deterministic Accuracy Over Hallucination:** 
   LLMs often guess or approximate leave rules and financial numbers. With MCP, calculations (notice buyout, business day counting, policy caps) are executed deterministically by code and live SQLite records.
2. **Decoupled Architecture:** 
   The LLM agent never needs hardcoded SQL or tight coupling to the database schema. The MCP protocol provides an isolated, standardized contract.
3. **Auditability & Transactions:** 
   Every leave approval and expense submission updates the database with reference IDs and timestamps.
4. **Cross-Client Interoperability:** 
   The same `hr_mcp_server.py` works out of the box with Gradio, Antigravity IDE, Claude Desktop, Cursor, or any custom client without modifying a single line of backend logic.

