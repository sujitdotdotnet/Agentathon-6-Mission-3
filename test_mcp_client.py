"""
test_mcp_client.py - Test MultiServerMCPClient connection to hr_mcp_server.py over stdio
"""
import asyncio
import os
import sys
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent

load_dotenv()

SERVER_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hr_mcp_server.py")

SERVERS = {
    "nexura_hr_mcp": {
        "command": sys.executable,
        "args": [SERVER_SCRIPT],
        "transport": "stdio",
    }
}

async def main():
    print("[1] Connecting to MCP Server via stdio...")
    client = MultiServerMCPClient(SERVERS)
    tools = await client.get_tools()
    print(f"[2] Success! Retrieved {len(tools)} tools from MCP server:")
    for t in tools:
        print(f"  - {t.name}")

    print("\n[3] Testing tool execution via MCP client...")
    # Test calling a tool directly
    test_result = await tools[0].ainvoke({"identifier": "EMP101"})
    print("Tool result output:\n", test_result)

    print("\n[4] Building agent with DeepSeek...")
    agent = create_agent(
        model="deepseek:deepseek-chat",
        tools=tools,
        system_prompt="You are an HR agent. Today is Saturday 2026-11-07. Answer briefly using tools.",
    )

    print("\n[5] Invoking agent: 'Who is EMP101?'...")
    res = await agent.ainvoke({"messages": [{"role": "user", "content": "Who is EMP101 and what is their role?"}]})
    print("Agent reply:\n", res["messages"][-1].content)

if __name__ == "__main__":
    asyncio.run(main())

