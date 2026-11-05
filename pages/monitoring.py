"""
NEXHOST CLOUD - Live Resource Monitoring and Telemetry
Author: @Harsh_54x
"""

import time
from datetime import datetime
import streamlit as st
from auth.sessions import get_current_user, is_logged_in
from components.theme import apply_custom_theme, render_developer_footer, safe_set_page_config
from components.navbar import render_navbar
from components.sidebar import render_sidebar
from components.charts import create_resource_gauge, create_resource_history_chart
from database.projects import ProjectRepository
from database.usage import UsageRepository
from core.membership_engine import MembershipEngine
from core.process_manager import ProcessManager
from services.storage_service import StorageService
from utils.helpers import format_uptime

safe_set_page_config(title="Monitoring - NEXHOST CLOUD", icon="📈", layout="wide")
apply_custom_theme()

if not is_logged_in():
    st.warning("⚠️ Please log in to monitor bot resources.")
    st.stop()

render_navbar()
render_sidebar()
user = get_current_user()

st.title("📈 Real-Time Resource Telemetry")
st.caption("Live hardware consumption measured directly from the active execution worker.")

user_projects = ProjectRepository.list_by_user(user.id)
if not user_projects:
    st.info("No projects deployed yet.")
    st.stop()

selected_id = st.session_state.get("current_project_id", user_projects[0].id)
proj_map = {p.id: p.name for p in user_projects}
curr_idx = list(proj_map.keys()).index(selected_id) if selected_id in proj_map else 0

chosen_id = st.selectbox(
    "Select Bot to Monitor",
    options=list(proj_map.keys()),
    format_func=lambda x: f"{proj_map[x]} (#{x})",
    index=curr_idx
)
st.session_state["current_project_id"] = chosen_id

proj = ProjectRepository.get_user_project(user.id, chosen_id)
limits = MembershipEngine.get_user_limits(user.id)

# Fetch actual live telemetry
metrics = ProcessManager.get_live_status(user.id, chosen_id)
is_running = metrics.get("is_running", False)
cpu_val = metrics.get("cpu_percent", 0.0)
ram_val = metrics.get("memory_mb", 0.0)
uptime_str = format_uptime(metrics.get("uptime_seconds"))

# Storage
storage_mb = StorageService.calculate_project_size(user.id, chosen_id) / (1024 * 1024)

# Record telemetry in database for history if bot is active
if is_running:
    UsageRepository.record(chosen_id, cpu_val, ram_val, storage_mb)

# Gauge Row
g1, g2, g3 = st.columns(3)
with g1:
    cpu_gauge = create_resource_gauge(cpu_val, 100.0, f"CPU Usage (Limit: {limits['max_cpu_cores']} vCPU)", "%", "#6366F1")
    st.plotly_chart(cpu_gauge, use_container_width=True)
with g2:
    ram_gauge = create_resource_gauge(ram_val, float(limits['max_ram_mb']), f"RAM Usage (Limit: {limits['max_ram_mb']} MB)", "MB", "#10B981")
    st.plotly_chart(ram_gauge, use_container_width=True)
with g3:
    storage_gauge = create_resource_gauge(storage_mb, float(limits['max_storage_mb']), f"Disk Usage (Limit: {limits['max_storage_mb']} MB)", "MB", "#F59E0B")
    st.plotly_chart(storage_gauge, use_container_width=True)

# Overview stats
st.markdown(f"""
<div class="nex-card">
    <div style="display: flex; justify-content: space-around; flex-wrap: wrap; text-align: center;">
        <div>
            <div class="nex-stat-label">Worker Status</div>
            <div style="font-weight: 700; color: {'#10B981' if is_running else '#9CA3AF'}; font-size: 1.1rem; margin-top: 4px;">
                {'● Online & Running' if is_running else '■ Offline'}
            </div>
        </div>
        <div>
            <div class="nex-stat-label">Active Uptime</div>
            <div style="font-weight: 700; color: #FFFFFF; font-size: 1.1rem; margin-top: 4px;">{uptime_str}</div>
        </div>
        <div>
            <div class="nex-stat-label">Crash Restarts</div>
            <div style="font-weight: 700; color: #FFFFFF; font-size: 1.1rem; margin-top: 4px;">{proj.restart_count}</div>
        </div>
        <div>
            <div class="nex-stat-label">Auto-Recovery</div>
            <div style="font-weight: 700; color: {'#10B981' if proj.auto_restart else '#EF4444'}; font-size: 1.1rem; margin-top: 4px;">
                {'Enabled' if proj.auto_restart else 'Disabled'}
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Telemetry History Line Chart
st.subheader("📊 Telemetry History")
history = UsageRepository.get_history(chosen_id, limit=25)
if history and len(history) > 1:
    timestamps = [h.timestamp.strftime("%H:%M:%S") for h in history]
    cpus = [h.cpu_percent for h in history]
    rams = [h.memory_mb for h in history]
    chart = create_resource_history_chart(timestamps, cpus, rams)
    st.plotly_chart(chart, use_container_width=True)
else:
    st.info("Gathering historical metric datapoints as the bot runs...")

if is_running:
    if st.button("🔄 Refresh Telemetry Now", use_container_width=True):
        st.rerun()

render_developer_footer()
