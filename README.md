# Mission 3: Give your AI agent tools, with MCP

An agent becomes useful when it can use tools. You can write the tools yourself, or borrow them from an
MCP server that someone else runs. These three exercises show both, each as a chat page you can talk to.

Every file has three blocks: the tools (or the server), the agent, and the chat page.
Read the first two. The chat page (Gradio) is the same in every file, so you can skip it.

## Set up (once)

```
uv sync
uv run 00_setup_check.py
```

Put your DeepSeek key in the `.env` file. Run the check until it says ALL GOOD.

## Run in this order

Each one opens a chat page at http://127.0.0.1:7860. Stop one (Ctrl+C) before starting the next.

| File | What you learn |
|---|---|
| `01_agent_custom_tools.py` | An agent with your own tools: plain Python functions. |
| `02_agent_with_mcp.py` | Borrow tools from an MCP server. You write no tools at all. |
| `03_agent_with_mcp_login.py` | The same, for a server that makes you sign in through your browser first. |
| `mcp_login.py` | Optional. How the browser sign-in works, written out. |

## Your capstone

Pick a topic of your own. Write its tools the way you did in 01, and add MCP servers the way you did in 02 and 03.

## Want to build and deploy your own MCP server?

That is the Diamond MCP workshop on 29 Nov.

## Using the same servers from Antigravity (no code)

See `ANTIGRAVITY_SETUP.md`.
