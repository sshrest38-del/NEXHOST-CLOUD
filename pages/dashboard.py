"""
NEXHOST CLOUD - User Dashboard
Author: @Harsh_54x
"""

import streamlit as st
from auth.sessions import get_current_user, is_logged_in
from components.theme import apply_custom_theme, render_developer_footer, safe_set_page_config
from components.navbar import render_navbar
from components.sidebar import render_sidebar
from components.cards import metric_card, project_card
from components.charts import create_status_donut
from core.membership_engine import MembershipEngine
from database.projects import ProjectRepository
from services.storage_service import StorageService

safe_set_page_config(title="Dashboard - NEXHOST CLOUD", icon="📊", layout="wide")
apply_custom_theme()

if not is_logged_in():
    st.warning("⚠️ Please log in from the home page to access your dashboard.")
    st.stop()

render_navbar()
render_sidebar()
user = get_current_user()

st.title("📊 User Dashboard")
st.caption(f"Welcome to your cloud command center, {user.full_name or user.username}!")

# Compute core metrics
limits = MembershipEngine.get_user_limits(user.id)
user_projects = ProjectRepository.list_by_user(user.id)
running_count = sum(1 for p in user_projects if p.status == "RUNNING")
stopped_count = sum(1 for p in user_projects if p.status == "STOPPED")
failed_count = sum(1 for p in user_projects if p.status == "FAILED")

# Top Metrics Row
c1, c2, c3, c4 = st.columns(4)
with c1:
    metric_card("Total Projects", len(user_projects), f"Plan Quota: {limits['max_bots']} Bots", "🤖", "#6366F1")
with c2:
    metric_card("Running Bots", running_count, f"{limits['remaining_slots']} Slots Available", "⚡", "#10B981")
with c3:
    metric_card("Stopped Bots", stopped_count, "Offline or Idle", "■", "#F59E0B")
with c4:
    metric_card("Storage Used", f"{limits['used_storage_mb']:.1f} MB", f"Limit: {limits['max_storage_mb']} MB", "💾", "#8B5CF6")

st.markdown("---")

# Quick Actions
st.subheader("⚡ Quick Actions")
qa1, qa2, qa3, qa4, qa5, qa6 = st.columns(6)
with qa1:
    if st.button("🚀 Deploy Bot", use_container_width=True):
        st.switch_page("pages/deploy.py")
with qa2:
    if st.button("📁 My Projects", use_container_width=True):
        st.switch_page("pages/my_projects.py")
with qa3:
    if st.button("🐙 GitHub Import", use_container_width=True):
        st.switch_page("pages/github_import.py")
with qa4:
    if st.button("💎 Upgrade Plan", use_container_width=True):
        st.switch_page("pages/membership.py")
with qa5:
    if st.button("💳 View Payments", use_container_width=True):
        st.switch_page("pages/payments.py")
with qa6:
    if st.button("📋 Console Logs", use_container_width=True):
        st.switch_page("pages/console.py")

st.markdown("---")

# Projects & Overview
col_left, col_right = st.columns([2.2, 1])

with col_left:
    st.subheader("📁 Recent Projects")
    if not user_projects:
        st.info("You haven't deployed any Telegram bots yet. Click 'Deploy Bot' above to get started!")
    else:
        for proj in user_projects[:5]:
            p_size = StorageService.calculate_project_size(user.id, proj.id) / (1024 * 1024)
            project_card(
                project_name=proj.name,
                status=proj.status,
                runtime=proj.runtime_version,
                command=proj.startup_command,
                storage_mb=p_size,
                project_id=proj.id
            )

with col_right:
    st.subheader("📈 Deployment Status")
    if user_projects:
        donut_fig = create_status_donut(running_count, stopped_count, failed_count)
        st.plotly_chart(donut_fig, use_container_width=True)
    else:
        st.caption("No deployments active.")

    st.markdown("""
    <div class="nex-card">
        <div class="nex-card-header">🛡️ Enterprise Isolation</div>
        <p style="color: #9CA3AF; font-size: 0.82rem;">
            Your Python processes run in sandboxed worker environments with zero host exposure.
        </p>
    </div>
    """, unsafe_allow_html=True)

render_developer_footer()
