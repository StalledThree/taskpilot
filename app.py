"""Streamlit chat UI for TaskPilot. Run: streamlit run app.py"""
import json
import os

import streamlit as st

from agent import run_agent
from tools import TASK_FILE

st.set_page_config(page_title="TaskPilot Agent", page_icon="✅")
st.title("✅ TaskPilot — Agentic To-Do Assistant")

api_key = st.sidebar.text_input(
    "Anthropic API key", type="password", value=os.getenv("ANTHROPIC_API_KEY", "")
)
st.sidebar.markdown("### Current tasks")
try:
    tasks = json.loads(TASK_FILE.read_text()) if TASK_FILE.exists() else []
except json.JSONDecodeError:
    tasks = []
for t in tasks:
    st.sidebar.write(f"{'✔' if t['done'] else '☐'} #{t['id']} {t['title']} ({t['due_date'] or 'no date'})")

if "history" not in st.session_state:
    st.session_state.history = []
    st.session_state.chat = []

for role, text, steps in st.session_state.chat:
    with st.chat_message(role):
        if steps:
            with st.expander(f"Agent used {len(steps)} tool call(s)"):
                for s in steps:
                    st.code(f"{s['tool']}({s['input']})\n→ {s['output'][:300]}")
        st.write(text)

if prompt := st.chat_input("e.g. Plan my exam prep for the next 5 days"):
    if not api_key:
        st.error("Enter your API key in the sidebar.")
        st.stop()
    st.chat_message("user").write(prompt)
    with st.spinner("Agent is working..."):
        try:
            answer, st.session_state.history, trace = run_agent(
                prompt, st.session_state.history, api_key
            )
        except Exception as e:
            st.error(f"Error: {e}")
            st.stop()
    with st.chat_message("assistant"):
        if trace:
            with st.expander(f"Agent used {len(trace)} tool call(s)"):
                for s in trace:
                    st.code(f"{s['tool']}({s['input']})\n→ {s['output'][:300]}")
        st.write(answer)
    st.session_state.chat += [("user", prompt, []), ("assistant", answer, trace)]
    st.rerun()
