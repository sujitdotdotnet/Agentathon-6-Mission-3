"""
app.py - Vercel Serverless & Production Entrypoint for Nexura HR MCP Gradio Application
Domain: Software Service Company | Sub-domain: HR Policies
"""

import os
from hr_agent_app import demo

# Export ASGI Starlette/FastAPI app for Vercel Python runtime
app = demo.app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    print(f"[Nexura HR Agent] Starting on port {port}...")
    demo.launch(server_name="0.0.0.0", server_port=port, inbrowser=False)

