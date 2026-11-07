"""
00 - Setup Check  (RUN THIS FIRST)

Run it once. If the last line says "ALL GOOD" you are ready for the whole mission.
If not, it tells you exactly what to fix.

    uv run 00_setup_check.py

Keep this folder OUT of OneDrive / Dropbox (cloud sync can break package installs).
"""

import os
import sys

from dotenv import load_dotenv

print("====================================================================")
print("MISSION 3 - SETUP CHECK")
print("====================================================================")

problems = []  # we collect everything that is wrong here, and show it at the end

# 1. Python version
python_version = str(sys.version_info.major) + "." + str(sys.version_info.minor)
if sys.version_info.major < 3 or (sys.version_info.major == 3 and sys.version_info.minor < 10):
    problems.append("Python 3.10 or higher is needed. You have " + python_version + ".")
else:
    print("[OK] Python", python_version)

# 2. Folder location
folder = os.getcwd().lower()
if "onedrive" in folder or "dropbox" in folder:
    problems.append("This folder is inside OneDrive/Dropbox. Move it to e.g. C:\\mission3 and run  uv sync  again.")

# 3. Packages
try:
    import mcp
    import langchain
    import langchain_deepseek
    import langchain_mcp_adapters
    import jsonpatch
    import gradio
    print("[OK] Packages are installed.")
except ModuleNotFoundError as error:
    problems.append("A package is missing (" + str(error) + "). Fix: run  uv sync  in this folder.")

# 4. API key
load_dotenv()
api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
if api_key == "" or api_key == "your_deepseek_api_key_here":
    problems.append("No API key. Open the .env file and set your real DEEPSEEK_API_KEY.")
else:
    print("[OK] API key found in .env.")

# 5. One tiny AI call (only if nothing is wrong so far)
if len(problems) == 0:
    print("[..] One small test call to DeepSeek...")
    try:
        from langchain_deepseek import ChatDeepSeek
        model = ChatDeepSeek(model="deepseek-chat", temperature=0.0, max_tokens=5)
        reply = model.invoke("Reply with exactly: ready")
        print("[OK] DeepSeek replied:", reply.content.strip())
    except Exception as error:
        problems.append("The DeepSeek test call failed. Check internet, key or balance. Details: " + str(error))

print("====================================================================")
if len(problems) == 0:
    print("ALL GOOD - you are ready. Next: open 01_agent_custom_tools.py")
else:
    print("NOT READY YET - please fix these and run again:")
    number = 0
    for problem in problems:
        number = number + 1
        print("  " + str(number) + ". " + problem)
print("====================================================================")
