# taskpilot
# TaskPilot: Agentic AI To-Do Assistant
TaskPilot is an agentic AI application that turns a high-level goal into a
finished, trackable plan. Instead of only answering questions, it works
autonomously. Given a goal such as "Plan my exam preparation for the next
5 days", the agent decides which tools to use, calls them step by step,
checks the results, and continues until the goal is complete.


Planning tasks and deadlines manually is time-consuming. Standard chatbots
give advice but cannot act on it. TaskPilot closes this gap: it breaks a
goal into tasks, schedules them against today's date, and saves them to a
persistent task list.


1. **Plan:** The LLM reads the user's goal and decides the next action.
2. **Act:** It calls a tool (date lookup, calculator, add task, web page reader).
3. **Observe:** It reads the tool's result and decides what to do next.
4. **Repeat:** The loop continues, up to 8 steps, until the goal is done.
5. **Respond:** The agent returns a short summary of what it completed.


- Autonomous multi-step reasoning with tool use
- 6 tools: date/time, safe calculator, add/list/complete tasks, web page reader
- Persistent task storage in JSON
- Web UI (Streamlit) with a visible log of every tool call the agent made
- Error handling: tool failures are returned to the agent so it can recover
- Security: AST-based calculator (no `eval`), http/https-only fetching,
  API key kept out of the repository


Python, Claude API (tool use), Streamlit, JSON storage

Built using AI-assisted ("vibe") coding with Claude, then tested manually
for tool behaviour and end-to-end agent runs.
234233