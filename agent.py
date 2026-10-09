"""TaskPilot agent core: a tool-using loop (Plan -> Act -> Observe -> Repeat) on the Anthropic Messages API."""
import os

import anthropic

from tools import TOOL_FUNCTIONS, TOOL_SCHEMAS

MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5")
MAX_STEPS = 8

SYSTEM_PROMPT = """You are TaskPilot, a personal productivity agent.
You can manage a to-do list, do calculations, check the date and read web pages.
Rules:
- Call get_current_datetime before setting any due date.
- Break a big goal into small, concrete tasks and add each with add_task.
- Use tools instead of guessing. If a tool returns an error, adapt and try again.
- When finished, reply with a short summary of what you did."""


def run_agent(user_message: str, history: list | None = None, api_key: str | None = None):
    """Run the agent loop. Returns (final_text, updated_history, trace)."""
    client = anthropic.Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))
    messages = list(history or [])
    messages.append({"role": "user", "content": user_message})
    trace = []  # list of {"tool", "input", "output"} for display

    for _ in range(MAX_STEPS):
        response = client.messages.create(
            model=MODEL,
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            tools=TOOL_SCHEMAS,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            text = "".join(b.text for b in response.content if b.type == "text")
            return text, messages, trace

        results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            func = TOOL_FUNCTIONS.get(block.name)
            try:
                output = func(**block.input) if func else f"Unknown tool: {block.name}"
            except Exception as e:  # never crash the loop on a tool failure
                output = f"Tool error: {e}"
            trace.append({"tool": block.name, "input": block.input, "output": str(output)})
            results.append({"type": "tool_result", "tool_use_id": block.id, "content": str(output)})
        messages.append({"role": "user", "content": results})

    return "Stopped: reached the maximum number of steps.", messages, trace


if __name__ == "__main__":  # simple CLI
    history = []
    print("TaskPilot ready. Type 'quit' to exit.")
    while True:
        q = input("\nYou: ").strip()
        if q.lower() in {"quit", "exit"}:
            break
        answer, history, steps = run_agent(q, history)
        for s in steps:
            print(f"  [tool] {s['tool']}({s['input']}) -> {s['output'][:100]}")
        print(f"Agent: {answer}")
