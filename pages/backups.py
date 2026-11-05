"""
NEXHOST CLOUD - Project Backup and Snapshot Restore Manager
Author: @Harsh_54x
"""

import streamlit as st
from auth.sessions import get_current_user, is_logged_in
from components.theme import apply_custom_theme, render_developer_footer, safe_set_page_config
from components.navbar import render_navbar
from components.sidebar import render_sidebar
from database.projects import ProjectRepository
from services.backup_service import BackupService
from core.membership_engine import MembershipEngine
from utils.helpers import format_bytes

safe_set_page_config(title="Backups - NEXHOST CLOUD", icon="💾", layout="wide")
apply_custom_theme()

if not is_logged_in():
    st.warning("⚠️ Please log in to manage backups.")
    st.stop()

render_navbar()
render_sidebar()
user = get_current_user()

st.title("💾 Backups & Disaster Recovery")
st.caption("Generate full code snapshots of your bot and restore anytime with zero data loss.")

limits = MembershipEngine.get_user_limits(user.id)
if not limits["backup_enabled"] and user.role not in ["super_admin", "admin"]:
    st.warning("⚠️ Backups are not enabled on your current Free plan.")
    st.info("💡 Upgrade to Starter, Pro, or Lifetime to unlock instant 1-click cloud backups.")
    if st.button("💎 View Plans & Upgrade"):
        st.switch_page("pages/membership.py")
    st.stop()

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

col_bk, col_info = st.columns([1, 2])
with col_bk:
    if st.button("📦 Create Instant Snapshot", type="primary", use_container_width=True):
        with st.spinner("Compressing project files and generating snapshot..."):
            ok, msg, path = BackupService.create_backup(user.id, chosen_id, proj.slug)
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

st.markdown("---")
st.subheader("📋 Available Snapshots")

backups = BackupService.list_backups(user.id, chosen_id)
if not backups:
    st.info("No snapshots recorded yet for this project. Click 'Create Instant Snapshot' above.")
else:
    for b in backups:
        c1, c2, c3, c4 = st.columns([3, 1.5, 1.2, 1.2])
        with c1:
            st.write(f"📦 **{b['filename']}**")
            st.caption(f"Created: {b['created_at']}")
        with c2:
            st.caption(f"Size: {format_bytes(b['size_bytes'])}")
        with c3:
            with open(b["path"], "rb") as f:
                st.download_button(
                    "⬇️ Download",
                    data=f.read(),
                    file_name=b["filename"],
                    mime="application/zip",
                    key=f"dl_{b['filename']}"
                )
        with c4:
            if st.button("🔄 Restore", key=f"rst_{b['filename']}"):
                with st.spinner(f"Restoring from {b['filename']}..."):
                    ok, msg = BackupService.restore_backup(user.id, chosen_id, b["filename"])
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

render_developer_footer()
