"""
hr_agent_app.py - MCP-Powered HR Intelligence Chatbot for Software Services.
Domain: Software Service Company
Sub-Domain: HR Policies

Connects to the local FastMCP server (hr_mcp_server.py) over the Model Context Protocol (MCP),
discovers tools dynamically, uses DeepSeek API via LangChain, and provides a rich Gradio interface.
"""

import asyncio
import datetime
import json
import os
import sys
import warnings
from zoneinfo import ZoneInfo

# Suppress noisy Pydantic V1 compatibility warning on Python 3.14
warnings.filterwarnings("ignore", category=UserWarning)

import gradio as gr
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

from seed_hr_db import DB_PATH, init_and_seed_db

# Load environment variables (.env file)
load_dotenv()
if not os.getenv("DEEPSEEK_API_KEY"):
    print("[WARNING] DEEPSEEK_API_KEY is not set in environment or .env file.")

# Ensure DB is created and seeded
if not os.path.exists(DB_PATH):
    init_and_seed_db(DB_PATH)

# Path to the MCP server script
SERVER_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hr_mcp_server.py")

# MCP Server connection configuration (Standard I/O Process)
SERVERS = {
    "nexura_hr_mcp": {
        "command": sys.executable,
        "args": [SERVER_SCRIPT],
        "transport": "stdio",
    }
}


async def init_mcp_agent():
    """Connect to the MCP server, discover tools, and initialize the LangChain ReAct agent."""
    print("[MCP] Connecting to Nexura HR MCP Server via stdio...")
    client = MultiServerMCPClient(SERVERS)

    # Discover tools exposed by the MCP server
    tools = await client.get_tools()
    print(f"[MCP] Successfully connected! Discovered {len(tools)} tools:")
    for t in tools:
        print(f"  * {t.name}: {t.description[:60]}...")

    today = datetime.datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%A %Y-%m-%d")

    system_prompt = (
        "You are the Nexura Technologies HR Intelligence & Operations AI Assistant. "
        "Nexura Technologies is a premier global software services & engineering consultancy.\n\n"
        "YOUR CORE PRINCIPLES:\n"
        "1. ALWAYS use the provided MCP tools to fetch employee details, check leave balances, "
        "   search company policies, calculate notice period buyouts, check holidays, or submit expense claims.\n"
        "2. Ground every policy answer strictly on data returned by the tools. Never hallucinate or assume company rules.\n"
        "3. Always cite relevant Policy Codes (e.g. POL-WFH-01, POL-LV-02, POL-NOT-03, POL-EXP-04, POL-INS-05, POL-APP-06).\n"
        "4. When an employee asks to apply for leave or submit an expense, execute the corresponding tool, "
        "   check policy limits, and inform them of the approval or rejection status with clear reasoning.\n"
        f"5. Today is {today}. Answer professionally, accurately, and with clear structured formatting."
    )

    agent = create_agent(
        model="deepseek:deepseek-chat",
        tools=tools,
        system_prompt=system_prompt,
    )

    return client, tools, agent


# Initialize the agent and tools once at startup
mcp_client, discovered_tools, hr_agent = asyncio.run(init_mcp_agent())


# =============================================================================
# GRADIO CHAT HANDLER
# =============================================================================

async def respond(message, history):
    """Processes user queries, invokes the MCP agent, and surfaces tool calls."""
    if not message.strip():
        return ""

    # Build conversation history
    messages = []
    for item in history:
        messages.append({"role": item["role"], "content": item["content"]})
    messages.append({"role": "user", "content": message})

    try:
        result = await hr_agent.ainvoke({"messages": messages})

        # Collect tool invocation steps to clearly display MCP execution
        tool_steps = []
        for item in result.get("messages", []):
            if hasattr(item, "tool_calls") and item.tool_calls:
                for call in item.tool_calls:
                    args_str = json.dumps(call.get("args", {}), indent=2)
                    tool_steps.append(
                        f"⚙️ **MCP Tool Call**: `{call['name']}`\n```json\n{args_str}\n```"
                    )

        steps_display = ""
        if tool_steps:
            steps_display = "### 🔌 MCP Action Trace\n" + "\n\n".join(tool_steps) + "\n\n---\n\n"

        # Extract the final AI message content
        final_reply = ""
        for item in reversed(result.get("messages", [])):
            if getattr(item, "type", "") == "ai" and item.content:
                final_reply = item.content
                break
        if not final_reply and result.get("messages"):
            final_reply = str(result["messages"][-1].content)

        return steps_display + final_reply

    except Exception as e:
        return f"❌ Error invoking HR Agent: {str(e)}"


# =============================================================================
# GRADIO UI SETUP
# =============================================================================

tools_info_md = "### 🛠️ Discovered MCP Tools on `nexura_hr_mcp`:\n\n"
for t in discovered_tools:
    tools_info_md += f"- **`{t.name}`**: {t.description}\n"

custom_css = """
.mcp-badge {
    background: linear-gradient(135deg, #1e3a8a, #3b82f6);
    color: white;
    padding: 12px 18px;
    border-radius: 8px;
    margin-bottom: 12px;
}
.mcp-tag {
    background: #dbeafe;
    color: #1e40af;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 6px;
    font-size: 0.85em;
    border: 1px solid #93c5fd;
}
.server-card {
    background: #f8fafc;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 14px 18px;
}
"""

with gr.Blocks(title="Nexura Tech HR Agent (MCP Powered)", css=custom_css, theme=gr.themes.Soft(primary_hue="blue")) as demo:
    gr.HTML("""
    <div style="text-align: center; padding: 15px 0;">
        <h1 style="color: #1e3a8a; margin-bottom: 5px;">🏢 Nexura Technologies — HR Operations & Policy Agent</h1>
        <h3 style="color: #475569; font-weight: normal; margin-top: 0;">
            Enterprise AI Assistant powered by <b>Model Context Protocol (MCP)</b> & <b>DeepSeek</b>
        </h3>
    </div>
    """)

    with gr.Row():
        with gr.Column(scale=12):
            gr.HTML("""
            <div class="server-card">
                <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
                    <div>
                        <span style="font-size: 1.1em; font-weight: bold; color: #0f172a;">🔌 Connected MCP Server: <code>nexura_hr_mcp</code></span>
                        <span class="mcp-tag" style="margin-left: 10px;">STATUS: ONLINE 🟢</span>
                    </div>
                    <div>
                        <span style="font-size: 0.9em; color: #475569;">Transport: <b>stdio (Process JSON-RPC)</b></span>
                    </div>
                </div>
                <div style="margin-top: 8px; font-size: 0.9em; color: #334155; line-height: 1.5;">
                    🗄️ <b>Local Relational Database:</b> SQLite (<code>hr_portal.db</code>) with 6 active tables: 
                    <i>employees, leave_balances, hr_policies, office_holidays, leave_applications, expense_claims</i>.
                </div>
            </div>
            """)

    with gr.Accordion("📋 View Connected MCP Tools & Schemas (Click to Expand)", open=False):
        gr.Markdown(tools_info_md)
        gr.Markdown("""
        > **Why MCP makes a strong case here:**
        > 1. **Decoupled Architecture:** The LLM does not need custom API wrappers or hardcoded SQL. The MCP server encapsulates all database logic and validation rules.
        > 2. **Authoritative Grounding:** Company policies (probation limits, sandwich rules, buyout math) are calculated authoritatively by tool code, eliminating hallucinations.
        > 3. **Auditable Transactions:** Every leave approval and expense submission updates the SQLite database with full traceability.
        """)

    with gr.Row():
        with gr.Column(scale=8):
            chatbot = gr.Chatbot(
                type="messages",
                height=520,
                show_copy_button=True,
                avatar_images=(None, "https://api.dicebear.com/7.x/bottts/svg?seed=HRBot")
            )
            with gr.Row():
                msg_input = gr.Textbox(
                    placeholder="Ask about HR policies, check employee leave balance, apply for leave, or compute notice buyout...",
                    show_label=False,
                    scale=9,
                    autofocus=True
                )
                submit_btn = gr.Button("Send", variant="primary", scale=1)

            with gr.Row():
                clear_btn = gr.ClearButton([chatbot, msg_input], value="Clear Conversation")

        with gr.Column(scale=4):
            gr.Markdown("### 💡 Quick Prompt Suggestions")
            gr.Markdown("Click any sample query to test real MCP tool execution:")

            example_1 = gr.Button("🏖️ Priya Sharma's Leave Balance & PTO", size="sm")
            example_2 = gr.Button("⚠️ Probation Leave Restriction (Ananya)", size="sm")
            example_3 = gr.Button("🏠 WFH Allowance & Internet Reimbursement", size="sm")
            example_4 = gr.Button("💼 Calculate Notice Buyout (Devansh)", size="sm")
            example_5 = gr.Button("📅 2026 Bengaluru Office Holidays", size="sm")
            example_6 = gr.Button("💳 Expense Claim (Certification Reimbursement)", size="sm")

            gr.HTML("""
            <div style="margin-top: 20px; padding: 12px; background: #eff6ff; border-radius: 8px; font-size: 0.85em; color: #1e40af; border: 1px solid #bfdbfe;">
                <b>👥 Sample Seeded Employees:</b><br/>
                • <code>EMP101</code>: Aarav Mehta (L5, Confirmed, Bengaluru)<br/>
                • <code>EMP102</code>: Priya Sharma (L6 Architect, Confirmed, Pune)<br/>
                • <code>EMP104</code>: Ananya Iyer (L3, <b>Probation</b>, Bengaluru)<br/>
                • <code>EMP105</code>: Devansh Gupta (L5, <b>Notice Period</b>, Bengaluru)
            </div>
            """)

    # Interactive example button handlers
    def set_ex1():
        return "Can you check Priya Sharma's (EMP102) current leave balance? She wants to know if she has enough PTO days to take a 4-day vacation next month."

    def set_ex2():
        return "Ananya Iyer (EMP104) wants to take 5 days of Paid Time Off (PTO) next week. Can she apply for it under our HR policy?"

    def set_ex3():
        return "What are the exact policy limits for home office ergonomic setup allowance and monthly internet reimbursement for an L5 Senior Engineer?"

    def set_ex4():
        return "Devansh Gupta (EMP105) is serving notice and wants an early release with a 20-day shortfall. What will be his buyout amount under POL-NOT-03?"

    def set_ex5():
        return "What are the upcoming mandatory and optional floating holidays for our Bengaluru development center in 2026?"

    def set_ex6():
        return "Submit an expense claim of INR 35,000 for AWS Solutions Architect Professional certification for Aarav Mehta (EMP101). Is it within policy limits?"

    example_1.click(set_ex1, outputs=[msg_input])
    example_2.click(set_ex2, outputs=[msg_input])
    example_3.click(set_ex3, outputs=[msg_input])
    example_4.click(set_ex4, outputs=[msg_input])
    example_5.click(set_ex5, outputs=[msg_input])
    example_6.click(set_ex6, outputs=[msg_input])

    # Chat execution events
    async def user_submit(user_msg, chat_history):
        if not user_msg.strip():
            return "", chat_history
        chat_history = chat_history + [{"role": "user", "content": user_msg}]
        bot_response = await respond(user_msg, chat_history[:-1])
        chat_history.append({"role": "assistant", "content": bot_response})
        return "", chat_history

    msg_input.submit(user_submit, [msg_input, chatbot], [msg_input, chatbot])
    submit_btn.click(user_submit, [msg_input, chatbot], [msg_input, chatbot])


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("NEXURA TECHNOLOGIES HR MCP CHATBOT")
    print("====================================================================")
    print("Starting Gradio Web Application...")
    demo.launch(server_name="127.0.0.1", server_port=7860, inbrowser=False)
