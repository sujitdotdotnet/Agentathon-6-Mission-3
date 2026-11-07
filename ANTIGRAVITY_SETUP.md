# Connect Antigravity to real MCP servers (no code)

This is the fun part. In 5 minutes your AI agent will use live FPI tools.

## 1. Open the MCP config

In Antigravity: click the **...** at the top of the agent panel -> **MCP Servers** -> **Manage MCP Servers** -> **View raw config**.

(The file is `mcp_config.json`. Depending on your version it lives in `~/.gemini/antigravity/` or `~/.gemini/config/`. The button above opens the right one for you.)

## 2. Add the FPI Calendar server (no login)

Paste this inside the file. If `mcpServers` already exists, add just the `fpi-calendar` entry to it.

```json
{
  "mcpServers": {
    "fpi-calendar": {
      "serverUrl": "https://schedule.futureproofindia.com/mcp"
    }
  }
}
```

Important: the key is `serverUrl`, not `url`. With `url` the tools silently do not appear.

Save, then refresh the MCP Servers list. You should see 6 tools.

Try in the agent chat:
- What is on the FPI schedule this week?
- When is the next AI Agentathon?
- Which sessions are only for Diamond members this month?

## 3. Add FPI Ascent (real sign-in)

Add this entry next to `fpi-calendar`:

```json
    "fpi-ascent": {
      "serverUrl": "https://ascent.futureproofindia.com/api/mcp/member"
    }
```

The first time you use it, your browser opens. Sign in to Ascent with your email code and click **Allow**. Antigravity keeps the login for you.

Ascent only ever shows or changes YOUR details. Try:
- Show my Ascent profile.
- Update my headline to "Building agents with MCP".
- What is my Ascent progress?
- Show me someone else's profile. (It will refuse. That is the login doing its job.)

## 4. Use both together

- What is the next Agentathon, and how many sessions have I attended recently?
- Based on my target role in Ascent, which upcoming sessions should I attend?

Then go to `02_agent_with_mcp.py` to see the code behind all of this.
