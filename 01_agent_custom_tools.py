"""
01 - An AI agent with your OWN tools, in a chat page.

LESSON: a tool is just a Python function. The AI reads its name and its docstring (the text in
triple quotes) to decide WHEN to call it. This is a ReAct agent: it REASONS about your question,
ACTS by calling a tool, reads the result, and reasons again until it can answer.
LangChain's create_agent builds that loop for you (it runs on LangGraph underneath).

The file has three blocks. Read 1 and 2. Block 3 is the chat page and is the same in every file.

Run:  uv run 01_agent_custom_tools.py      then open http://127.0.0.1:7860
Try:  Add a task to call the bank tomorrow
      Add a task to buy milk
      What is pending?
      I finished the bank call
"""

import datetime
import os
from zoneinfo import ZoneInfo

import gradio as gr
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.tools import tool

load_dotenv()
if not os.getenv("DEEPSEEK_API_KEY"):
    raise SystemExit("Put your DEEPSEEK_API_KEY in the .env file first.")


# =============================================================================
# 1. THE TOOLS  -  plain Python functions with @tool and a docstring
# =============================================================================

# Our to-do list. It is a list of tasks, and each task is a dictionary like this:
#     {"title": "Buy milk", "due": "2026-11-10", "done": False}
tasks = []


@tool
def add_task(title: str, due: str = "") -> str:
    """Add a task to my to-do list. due is an optional date such as 2026-11-10."""
    task = {"title": title, "due": due, "done": False}
    tasks.append(task)
    number = len(tasks)
    return "Added task " + str(number) + ": " + title


@tool
def list_tasks(status: str = "pending") -> str:
    """List my tasks. status is 'pending', 'done' or 'all'."""
    result = ""
    number = 0
    for task in tasks:
        number = number + 1

        # Decide whether this task should be shown
        show = False
        if status == "all":
            show = True
        elif status == "done" and task["done"] == True:
            show = True
        elif status == "pending" and task["done"] == False:
            show = True

        # Build one line of text for it
        if show:
            line = str(number) + ". " + task["title"]
            if task["due"] != "":
                line = line + " (due " + task["due"] + ")"
            if task["done"] == True:
                line = line + " [done]"
            result = result + line + "\n"

    if result == "":
        return "No tasks found."
    return result


@tool
def complete_task(task_id: int) -> str:
    """Mark a task as done, using its number from list_tasks."""
    if task_id < 1 or task_id > len(tasks):
        return "There is no task number " + str(task_id) + "."
    task = tasks[task_id - 1]  # task number 1 is at position 0 in the list
    task["done"] = True
    return "Marked task " + str(task_id) + " as done."


# =============================================================================
# 2. THE AGENT  -  an AI model plus the tools it may use
# =============================================================================

# Today's date in India, for example "Saturday 2026-11-07". The AI has no clock, so we tell it.
today = datetime.datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%A %Y-%m-%d")

agent = create_agent(
    model="deepseek:deepseek-chat",
    tools=[add_task, list_tasks, complete_task],
    system_prompt="You manage the user's to-do list using the tools. Today is " + today + ". Answer briefly in plain text.",
)


# =============================================================================
# 3. THE CHAT PAGE (Gradio)  -  the same in every file. Skip it on your first read.
# =============================================================================

# "async" and "await": the AI takes a few seconds to answer, so we wait for it without freezing the page.
# Read "await" as "wait here until this finishes".
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
    title="My To-Do Agent",
    description="An AI agent that manages your to-do list using Python tools.",
    examples=["Add a task to call the bank tomorrow", "What is pending?"],
)
page.launch()
