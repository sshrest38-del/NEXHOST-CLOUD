"""
NEXHOST CLOUD - Requirements & Runtime Environment Manager
Author: @Harsh_54x
"""

import streamlit as st
from auth.sessions import get_current_user, is_logged_in
from components.theme import apply_custom_theme, render_developer_footer, safe_set_page_config
from components.navbar import render_navbar
from components.sidebar import render_sidebar
from database.projects import ProjectRepository
from services.storage_service import StorageService
from core.runtime_manager import RuntimeManager, SUPPORTED_RUNTIMES
from workers.worker_client import worker_client

safe_set_page_config(title="Requirements & Runtime - NEXHOST CLOUD", icon="📦", layout="wide")
apply_custom_theme()

if not is_logged_in():
    st.warning("⚠️ Please log in to manage runtime dependencies.")
    st.stop()

render_navbar()
render_sidebar()
user = get_current_user()

st.title("📦 Runtime & Dependencies Manager")
st.caption("Manage Python versions, startup entrypoints, and worker-isolated requirements.txt dependencies.")

user_projects = ProjectRepository.list_by_user(user.id)
if not user_projects:
    st.info("No projects deployed yet.")
    st.stop()

selected_id = st.session_state.get("current_project_id", user_projects[0].id)
proj_map = {p.id: p.name for p in user_projects}
curr_idx = list(proj_map.keys()).index(selected_id) if selected_id in proj_map else 0

chosen_id = st.selectbox(
    "Active Project",
    options=list(proj_map.keys()),
    format_func=lambda x: f"{proj_map[x]} (#{x})",
    index=curr_idx
)
st.session_state["current_project_id"] = chosen_id

proj = ProjectRepository.get_user_project(user.id, chosen_id)

tab_runtime, tab_reqs = st.tabs(["⚙️ Runtime & Startup Settings", "📄 requirements.txt"])

with tab_runtime:
    with st.form("runtime_settings_form"):
        col1, col2 = st.columns(2)
        with col1:
            runtime_idx = 0
            for idx, r in enumerate(SUPPORTED_RUNTIMES):
                if r["id"] == proj.runtime_version:
                    runtime_idx = idx
            selected_runtime = st.selectbox(
                "Python Runtime Version",
                options=[r["id"] for r in SUPPORTED_RUNTIMES],
                format_func=lambda x: next(r["label"] for r in SUPPORTED_RUNTIMES if r["id"] == x),
                index=runtime_idx
            )
        with col2:
            new_cmd = st.text_input("Startup Command", value=proj.startup_command, help="e.g. python bot.py or python3 main.py")

        auto_restart_chk = st.checkbox("Auto-restart on process crash", value=proj.auto_restart)

        if st.form_submit_button("💾 Save Settings", type="primary"):
            ProjectRepository.update_settings(
                project_id=chosen_id,
                name=proj.name,
                startup_command=new_cmd,
                runtime_version=selected_runtime,
                auto_restart=auto_restart_chk
            )
            st.success("Project runtime settings updated successfully!")
            st.rerun()

with tab_reqs:
    st.caption("Dependencies are installed exclusively inside the isolated worker environment.")
    current_reqs = StorageService.read_file(user.id, chosen_id, "requirements.txt") or ""

    updated_reqs = st.text_area("requirements.txt", value=current_reqs, height=220, placeholder="pyTelegramBotAPI>=4.15.0\nrequests>=2.31.0")

    col_save, col_install = st.columns([1, 1.5])
    with col_save:
        if st.button("💾 Save requirements.txt"):
            StorageService.write_file(user.id, chosen_id, "requirements.txt", updated_reqs)
            st.success("requirements.txt saved!")

    with col_install:
        if st.button("⚡ Install Dependencies on Worker", type="primary"):
            StorageService.write_file(user.id, chosen_id, "requirements.txt", updated_reqs)
            with st.spinner("Worker node is executing pip install -r requirements.txt..."):
                ok, msg = worker_client.install_requirements(chosen_id, user.id, proj.startup_command)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)

render_developer_footer()
