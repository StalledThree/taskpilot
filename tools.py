"""Tools the agent can call. Each tool has a JSON schema (TOOL_SCHEMAS) and a Python function (TOOL_FUNCTIONS)."""
import ast
import json
import operator
import re
import urllib.request
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

TASK_FILE = Path(__file__).parent / "tasks.json"


# ---------- helpers ----------
def _load_tasks() -> list:
    if not TASK_FILE.exists():
        return []
    try:
        return json.loads(TASK_FILE.read_text())
    except json.JSONDecodeError:
        return []


def _save_tasks(tasks: list) -> None:
    TASK_FILE.write_text(json.dumps(tasks, indent=2))


# ---------- tool functions ----------
def get_current_datetime() -> str:
    return datetime.now().strftime("%A, %d %B %Y, %H:%M")


_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod,
    ast.USub: operator.neg, ast.FloorDiv: operator.floordiv,
}


def _eval(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.operand))
    raise ValueError("Unsupported expression")


def calculator(expression: str) -> str:
    try:
        return str(_eval(ast.parse(expression, mode="eval").body))
    except Exception as e:
        return f"Error: {e}"


def add_task(title: str, due_date: str = "", priority: str = "medium") -> str:
    tasks = _load_tasks()
    new_id = max([t["id"] for t in tasks], default=0) + 1
    tasks.append({"id": new_id, "title": title, "due_date": due_date,
                  "priority": priority, "done": False})
    _save_tasks(tasks)
    return f"Task {new_id} added: {title} (due {due_date or 'n/a'}, {priority})"


def list_tasks(show_done: bool = False) -> str:
    tasks = [t for t in _load_tasks() if show_done or not t["done"]]
    return json.dumps(tasks, indent=2) if tasks else "No tasks."


def complete_task(task_id: int) -> str:
    tasks = _load_tasks()
    for t in tasks:
        if t["id"] == task_id:
            t["done"] = True
            _save_tasks(tasks)
            return f"Task {task_id} marked done."
    return f"Task {task_id} not found."


def fetch_webpage(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return "Error: only http/https URLs are allowed."
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TaskPilot/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            html = r.read(500_000).decode("utf-8", errors="ignore")
        html = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", html)
        text = re.sub(r"<[^>]+>", " ", html)
        return re.sub(r"\s+", " ", text).strip()[:3000]
    except Exception as e:
        return f"Error fetching page: {e}"


# ---------- JSON schemas given to the LLM ----------
TOOL_SCHEMAS = [
    {"name": "get_current_datetime",
     "description": "Get today's date and time. Use before scheduling anything.",
     "input_schema": {"type": "object", "properties": {}}},
    {"name": "calculator",
     "description": "Evaluate an arithmetic expression, e.g. '(120*3)/4'.",
     "input_schema": {"type": "object",
                      "properties": {"expression": {"type": "string"}},
                      "required": ["expression"]}},
    {"name": "add_task",
     "description": "Add a task to the to-do list.",
     "input_schema": {"type": "object",
                      "properties": {
                          "title": {"type": "string"},
                          "due_date": {"type": "string", "description": "YYYY-MM-DD"},
                          "priority": {"type": "string", "enum": ["low", "medium", "high"]}},
                      "required": ["title"]}},
    {"name": "list_tasks",
     "description": "List tasks. Pending only unless show_done is true.",
     "input_schema": {"type": "object",
                      "properties": {"show_done": {"type": "boolean"}}}},
    {"name": "complete_task",
     "description": "Mark a task as done by its id.",
     "input_schema": {"type": "object",
                      "properties": {"task_id": {"type": "integer"}},
                      "required": ["task_id"]}},
    {"name": "fetch_webpage",
     "description": "Fetch a public web page and return its text (first 3000 chars).",
     "input_schema": {"type": "object",
                      "properties": {"url": {"type": "string"}},
                      "required": ["url"]}},
]

TOOL_FUNCTIONS = {
    "get_current_datetime": get_current_datetime,
    "calculator": calculator,
    "add_task": add_task,
    "list_tasks": list_tasks,
    "complete_task": complete_task,
    "fetch_webpage": fetch_webpage,
}
