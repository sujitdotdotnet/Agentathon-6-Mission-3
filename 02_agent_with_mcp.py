"""
02 - Give your agent tools from an MCP SERVER.

LESSON: in 01 you wrote the tools yourself. Here you write NONE. Someone else runs an MCP server;
you give your agent its web address, ask "what tools do you have?", and use them.
Here the example is Future Proof India's calendar. No login is needed.

The file has three blocks. Read 1 and 2. Block 3 is the chat page and is the same in every file.

Run:  uv run 02_agent_with_mcp.py      then open http://127.0.0.1:7860
Try:  What is on the FPI schedule this week?
      When is the next AI Agentathon?
      Which sessions are only for Diamond members this month?
"""

import asyncio
import datetime
import os
from zoneinfo import ZoneInfo

import gradio as gr
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()
if not os.getenv("DEEPSEEK_API_KEY"):
    raise SystemExit("Put your DEEPSEEK_API_KEY in the .env file first.")


# =============================================================================
# 1. THE MCP SERVER  -  where the tools live. There is no tool code in this file at all.
# =============================================================================

# A dictionary of the servers we want to use. Each one has a name and a web address.
SERVERS = {
    "calendar": {
        "url": "https://schedule.futureproofindia.com/mcp",
        "transport": "streamable_http",
    }
}


# =============================================================================
# 2. THE AGENT  -  an AI model plus the tools it discovers on the server
# =============================================================================

# "async" and "await": talking to a server over the internet takes a moment, so we wait for it.
# Read "await" as "wait here until this finishes".
async def build_agent():
    client = MultiServerMCPClient(SERVERS)

    # Ask the server: what tools do you have?
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


# Connect to the server now, BEFORE the chat page opens
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
    title="FPI Calendar Agent",
    description="An AI agent using the tools of FPI's calendar MCP server.",
    examples=["What is on the FPI schedule this week?", "When is the next AI Agentathon?"],
)
page.launch()
