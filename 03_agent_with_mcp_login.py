"""
03 - Give your agent tools from an MCP server that needs you to LOG IN.

LESSON: compare with 02. The address is still just a web address. The only new line is "auth":
when you run this file, your BROWSER opens so you can sign in and click Allow. The server then knows
who you are and only ever shows YOUR details. The app never sees your password.
Here the example is Ascent, the Future Proof India member app (sign in with your member email).
The sign-in steps are written out in mcp_login.py if you want to read how they work.

The file has three blocks. Read 1 and 2. Block 3 is the chat page and is the same in every file.

Run:  uv run 03_agent_with_mcp_login.py
      Sign in in the browser that opens, then open http://127.0.0.1:7860
Try:  Show my Ascent profile
      What is my Ascent progress?
      Update my headline to "Building agents with MCP"
      Show me another member's profile      (it will refuse - the login keeps you to your own data)
"""

import asyncio
import datetime
import os
from zoneinfo import ZoneInfo

import gradio as gr
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

from mcp_login import browser_login

load_dotenv()
if not os.getenv("DEEPSEEK_API_KEY"):
    raise SystemExit("Put your DEEPSEEK_API_KEY in the .env file first.")


# =============================================================================
# 1. THE MCP SERVER  -  same as 02, plus ONE extra line: "auth"
# =============================================================================
ASCENT_URL = "https://ascent.futureproofindia.com/api/mcp/member"

SERVERS = {
    "ascent": {
        "url": ASCENT_URL,
        "transport": "streamable_http",
        "auth": browser_login(ASCENT_URL),  # opens your browser so you can sign in
    }
}


# =============================================================================
# 2. THE AGENT  -  an AI model plus the tools it discovers on the server
# =============================================================================

# "async" and "await": signing in and talking to a server take a moment, so we wait for them.
# Read "await" as "wait here until this finishes".
async def build_agent():
    client = MultiServerMCPClient(SERVERS)

    # Ask the server: what tools do you have? The sign-in happens here, once.
    tools = await client.get_tools()
    print("Tools found on the server:")
    for tool in tools:
        print("  -", tool.name)

    # Today's date in India, for example "Saturday 2026-11-07". The AI has no clock, so we tell it.
    today = datetime.datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%A %Y-%m-%d")

    return create_agent(
        model="deepseek:deepseek-chat",
        tools=tools,
        system_prompt="Use the tools to help the user. Today is " + today + ". Answer briefly in plain text.",
    )


# Sign in and connect now, BEFORE the chat page opens
agent = asyncio.run(build_agent())


# =============================================================================
# 3. THE CHAT PAGE (Gradio)  -  the same in every file. Skip it on your first read.
# =============================================================================
async def chat(message, history):
    # Build the whole conversation so far, in the format the agent expects
    messages = []
    for item in history:
        messages.append({"role": item["role"], "content": item["content"]})
    messages.append({"role": "user", "content": message})

    # Ask the agent. It may call some tools before it answers.
    result = await agent.ainvoke({"messages": messages})

    # Show which tools the AI used, then its answer
    steps = ""
    for item in result["messages"]:
        if hasattr(item, "tool_calls"):
            for call in item.tool_calls:
                steps = steps + "Used tool: " + call["name"] + " " + str(call["args"]) + "\n\n"
    answer = result["messages"][-1].content
    return steps + answer


page = gr.ChatInterface(
    chat,
    type="messages",
    title="My Ascent Agent",
    description="An AI agent using your own Ascent details, through a login-protected MCP server.",
    examples=["Show my Ascent profile", "What is my Ascent progress?"],
)
page.launch()
