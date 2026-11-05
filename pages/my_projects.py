"""
NEXHOST CLOUD - My Projects & Bot Management Panel
Author: @Harsh_54x
"""

import streamlit as st
from auth.sessions import get_current_user, is_logged_in
from components.theme import apply_custom_theme, render_developer_footer, safe_set_page_config
from components.navbar import render_navbar
from components.sidebar import render_sidebar
from components.dialogs import confirm_action_banner
from database.projects import ProjectRepository
from core.process_manager import ProcessManager
from core.project_manager import ProjectManager as CoreProjectManager
from services.storage_service import StorageService
from utils.helpers import get_status_badge

safe_set_page_config(title="My Projects - NEXHOST CLOUD", icon="📁", layout="wide")
apply_custom_theme()

if not is_logged_in():
    st.warning("⚠️ Please log in to manage your projects.")
    st.stop()

render_navbar()
render_sidebar()
user = get_current_user()

st.title("📁 My Bot Projects")
st.caption("Manage all your deployed Telegram bots, execute lifecycle actions, and monitor runtime states.")

# Search and filter row
col_s, col_f, col_new = st.columns([3, 1.5, 1.5])
with col_s:
    search_query = st.text_input("🔍 Search bots", placeholder="Filter by name...", label_visibility="collapsed")
with col_f:
    status_filter = st.selectbox("Status", options=["ALL", "RUNNING", "STOPPED", "FAILED"], label_visibility="collapsed")
with col_new:
    if st.button("➕ Deploy New Bot", type="primary", use_container_width=True):
        st.switch_page("pages/deploy.py")

projects = ProjectRepository.list_by_user(user.id, search=search_query, status=status_filter)

if not projects:
    st.info("No projects found matching the filter criteria. Ready to create your first bot?")
else:
    for proj in projects:
        storage_mb = StorageService.calculate_project_size(user.id, proj.id) / (1024 * 1024)
        live_status = ProcessManager.get_live_status(user.id, proj.id)
        current_state = "RUNNING" if live_status.get("is_running") else proj.status

        with st.container():
            st.markdown(f"""
            <div class="nex-card" style="margin-bottom: 0.5rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                    <div>
                        <span style="font-size: 1.2rem; font-weight: 700; color: #FFFFFF;">{proj.name}</span>
                        <span style="font-size: 0.78rem; color: #6B7280; margin-left: 8px;">(ID: #{proj.id})</span>
                    </div>
                    <div>{get_status_badge(current_state)}</div>
                </div>
                <div style="font-size: 0.82rem; color: #9CA3AF; margin-top: 6px;">
                    Command: <code style="color: #A5B4FC;">{proj.startup_command}</code> &bull;
                    Runtime: <strong style="color: #E5E7EB;">{proj.runtime_version}</strong> &bull;
                    Disk: <strong style="color: #E5E7EB;">{storage_mb:.1f} MB</strong> &bull;
                    Restarts: <strong style="color: #E5E7EB;">{proj.restart_count}</strong>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Action Buttons Row
            b1, b2, b3, b4, b5, b6 = st.columns(6)

            with b1:
                if current_state == "RUNNING":
                    if st.button("🛑 Stop", key=f"stop_{proj.id}", use_container_width=True):
                        with st.spinner("Stopping..."):
                            ok, msg = ProcessManager.stop_bot(user.id, proj.id)
                            st.rerun()
                else:
                    if st.button("▶️ Start", key=f"start_{proj.id}", type="primary", use_container_width=True):
                        with st.spinner("Starting..."):
                            ok, msg = ProcessManager.start_bot(user.id, proj.id)
                            if not ok:
                                st.error(msg)
                            else:
                                st.rerun()

            with b2:
                if st.button("🔄 Restart", key=f"restart_{proj.id}", use_container_width=True):
                    with st.spinner("Restarting..."):
                        ok, msg = ProcessManager.restart_bot(user.id, proj.id)
                        st.rerun()

            with b3:
                if st.button("📋 Console", key=f"console_{proj.id}", use_container_width=True):
                    st.session_state["current_project_id"] = proj.id
                    st.switch_page("pages/console.py")

            with b4:
                if st.button("🗂️ Files", key=f"files_{proj.id}", use_container_width=True):
                    st.session_state["current_project_id"] = proj.id
                    st.switch_page("pages/file_manager.py")

            with b5:
                if st.button("⚙️ Config", key=f"env_{proj.id}", use_container_width=True):
                    st.session_state["current_project_id"] = proj.id
                    st.switch_page("pages/environment.py")

            with b6:
                if st.button("🗑️ Delete", key=f"del_{proj.id}", use_container_width=True):
                    st.session_state[f"confirm_delete_{proj.id}"] = True

            # Confirmation banner for deletion
            if st.session_state.get(f"confirm_delete_{proj.id}", False):
                st.error(f"⚠️ Are you sure you want to permanently delete '{proj.name}'? This cannot be undone.")
                c_del, c_can = st.columns([1, 4])
                with c_del:
                    if st.button("Yes, Delete", key=f"do_delete_{proj.id}", type="primary"):
                        ProcessManager.stop_bot(user.id, proj.id)
                        CoreProjectManager.delete_project(user.id, proj.id)
                        st.session_state.pop(f"confirm_delete_{proj.id}", None)
                        st.success(f"Project '{proj.name}' deleted.")
                        st.rerun()
                with c_can:
                    if st.button("Cancel", key=f"cancel_del_{proj.id}"):
                        st.session_state.pop(f"confirm_delete_{proj.id}", None)
                        st.rerun()

            st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)

render_developer_footer()
