"""
NEXHOST CLOUD - Live Console and Real-Time Logs Streamer
Author: @Harsh_54x
"""

import time
import streamlit as st
from auth.sessions import get_current_user, is_logged_in
from components.theme import apply_custom_theme, render_developer_footer, safe_set_page_config
from components.navbar import render_navbar
from components.sidebar import render_sidebar
from database.projects import ProjectRepository
from core.process_manager import ProcessManager
from utils.helpers import get_status_badge

safe_set_page_config(title="Live Console - NEXHOST CLOUD", icon="📋", layout="wide")
apply_custom_theme()

if not is_logged_in():
    st.warning("⚠️ Please log in to view bot consoles.")
    st.stop()

render_navbar()
render_sidebar()
user = get_current_user()

st.title("📋 Live Bot Console & Logs")

user_projects = ProjectRepository.list_by_user(user.id)
if not user_projects:
    st.info("No projects deployed yet. Create a bot project first.")
    if st.button("🚀 Deploy Bot"):
        st.switch_page("pages/deploy.py")
    st.stop()

# Project selector
selected_id = st.session_state.get("current_project_id", user_projects[0].id)
proj_map = {p.id: f"{p.name} (#{p.id}) - {p.status}" for p in user_projects}
curr_idx = list(proj_map.keys()).index(selected_id) if selected_id in proj_map else 0

chosen_id = st.selectbox(
    "Select Bot Project",
    options=list(proj_map.keys()),
    format_func=lambda x: proj_map[x],
    index=curr_idx
)
st.session_state["current_project_id"] = chosen_id

proj = ProjectRepository.get_user_project(user.id, chosen_id)
live_status = ProcessManager.get_live_status(user.id, chosen_id)
is_running = live_status.get("is_running", False)
display_status = "RUNNING" if is_running else proj.status

# Control Toolbar
c_status, c_start, c_stop, c_restart, c_clear, c_download = st.columns([2, 1, 1, 1, 1, 1.2])

with c_status:
    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 8px; margin-top: 4px;">
        <span style="font-weight: 700; color: #FFFFFF;">Status:</span>
        {get_status_badge(display_status)}
        <span style="font-size: 0.8rem; color: #9CA3AF;">PID: {live_status.get('pid') or 'Offline'}</span>
    </div>
    """, unsafe_allow_html=True)

with c_start:
    if st.button("▶️ Start", disabled=is_running, type="primary", use_container_width=True):
        ok, msg = ProcessManager.start_bot(user.id, proj.id)
        if not ok:
            st.error(msg)
        st.rerun()

with c_stop:
    if st.button("🛑 Stop", disabled=not is_running, use_container_width=True):
        ProcessManager.stop_bot(user.id, proj.id)
        st.rerun()

with c_restart:
    if st.button("🔄 Restart", use_container_width=True):
        ProcessManager.restart_bot(user.id, proj.id)
        st.rerun()

with c_clear:
    if st.button("🧹 Clear", use_container_width=True):
        ProcessManager.clear_logs(user.id, proj.id)
        st.rerun()

# Logs Display
st.markdown("---")
col_filter, col_search, col_refresh = st.columns([1.5, 2.5, 1])
with col_filter:
    log_filter = st.selectbox("Log Level", ["ALL", "INFO", "WARNING", "ERROR"], label_visibility="collapsed")
with col_search:
    search_term = st.text_input("Filter log text", placeholder="Type keywords to filter...", label_visibility="collapsed")
with col_refresh:
    auto_refresh = st.checkbox("Live Stream (3s)", value=True)

@st.fragment(run_every=3 if (auto_refresh and is_running) else None)
def display_logs_fragment():
    raw_logs = ProcessManager.get_live_logs(user.id, proj.id, limit=300)
    lines = raw_logs.splitlines()

    if log_filter != "ALL":
        lines = [l for l in lines if f"[{log_filter}]" in l.upper() or log_filter in l.upper()]

    if search_term:
        lines = [l for l in lines if search_term.lower() in l.lower()]

    filtered_log_text = "\n".join(lines) if lines else "[No matching log output available.]"
    st.code(filtered_log_text, language="log")

display_logs_fragment()

raw_for_dl = ProcessManager.get_live_logs(user.id, proj.id, limit=300)
with c_download:
    st.download_button(
        "⬇️ Download",
        data=raw_for_dl,
        file_name=f"{proj.slug}_logs.txt",
        mime="text/plain",
        use_container_width=True
    )

render_developer_footer()
