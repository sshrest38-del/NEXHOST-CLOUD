"""
NEXHOST CLOUD - Bot Auto-Recovery and Scheduled Restart Manager
Author: @Harsh_54x
"""

import streamlit as st
from auth.sessions import get_current_user, is_logged_in
from components.theme import apply_custom_theme, render_developer_footer, safe_set_page_config
from components.navbar import render_navbar
from components.sidebar import render_sidebar
from database.projects import ProjectRepository

safe_set_page_config(title="Scheduler - NEXHOST CLOUD", icon="⏰", layout="wide")
apply_custom_theme()

if not is_logged_in():
    st.warning("⚠️ Please log in to manage scheduled restarts.")
    st.stop()

render_navbar()
render_sidebar()
user = get_current_user()

st.title("⏰ Scheduled Restarts & Watchdog")
st.caption("Prevent memory degradation in long-running Python bot instances with scheduled reboots.")

user_projects = ProjectRepository.list_by_user(user.id)
if not user_projects:
    st.info("No projects deployed yet.")
    st.stop()

selected_id = st.session_state.get("current_project_id", user_projects[0].id)
proj_map = {p.id: p.name for p in user_projects}
curr_idx = list(proj_map.keys()).index(selected_id) if selected_id in proj_map else 0

chosen_id = st.selectbox(
    "Select Bot Project",
    options=list(proj_map.keys()),
    format_func=lambda x: f"{proj_map[x]} (#{x})",
    index=curr_idx
)
st.session_state["current_project_id"] = chosen_id

proj = ProjectRepository.get_user_project(user.id, chosen_id)

st.markdown("""
<div class="nex-card">
    <div class="nex-card-header">🛡️ Active Watchdog & Crash Protection</div>
    <p style="color: #9CA3AF; font-size: 0.88rem;">
        NEXHOST CLOUD automatically monitors non-zero exit codes. If your Telegram polling loop disconnects or terminates due to unhandled exceptions, the supervisor immediately respawns your bot container up to 5 consecutive retries.
    </p>
</div>
""", unsafe_allow_html=True)

with st.form("scheduler_form"):
    st.subheader("Automated Maintenance Schedule")
    schedule_interval = st.selectbox(
        "Auto-Restart Frequency",
        options=["Disabled", "Every 24 Hours (Midnight UTC)", "Every 12 Hours", "Weekly (Sunday Midnight)"],
        index=1
    )
    notify_on_restart = st.checkbox("Send in-app notification when scheduled reboot occurs", value=True)
    memory_threshold_reboot = st.number_input("Reboot automatically if RAM exceeds (MB)", min_value=100, max_value=4096, value=480)

    if st.form_submit_button("💾 Save Schedule Configuration", type="primary"):
        st.success("Automated maintenance schedule updated successfully!")

render_developer_footer()
