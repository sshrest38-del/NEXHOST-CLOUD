"""
NEXHOST CLOUD - Deploy New Bot via ZIP Upload
Author: @Harsh_54x
"""

import streamlit as st
from auth.sessions import get_current_user, is_logged_in
from components.theme import apply_custom_theme, render_developer_footer, safe_set_page_config
from components.navbar import render_navbar
from components.sidebar import render_sidebar
from core.project_manager import ProjectManager
from core.runtime_manager import RuntimeManager
from core.membership_engine import MembershipEngine
from core.deployment_engine import DeploymentEngine

safe_set_page_config(title="Deploy Bot - NEXHOST CLOUD", icon="🚀", layout="wide")
apply_custom_theme()

if not is_logged_in():
    st.warning("⚠️ Please log in to deploy bot projects.")
    st.stop()

render_navbar()
render_sidebar()
user = get_current_user()

st.title("🚀 Deploy New Python Telegram Bot")
st.caption("Upload a ZIP archive containing your Python project code and start hosting.")

limits = MembershipEngine.get_user_limits(user.id)
if limits["remaining_slots"] <= 0:
    st.error(f"❌ You have reached your plan limit of {limits['max_bots']} bot(s).")
    st.info("💡 Please upgrade your membership to STARTER, PRO or LIFETIME to host more bots.")
    if st.button("💎 View Plans & Upgrade"):
        st.switch_page("pages/membership.py")
    st.stop()

with st.form("deploy_zip_form", clear_on_submit=False):
    col_a, col_b = st.columns(2)
    with col_a:
        bot_name = st.text_input("Project Name *", placeholder="e.g. MyMusicBot")
        runtimes = RuntimeManager.get_supported_runtimes()
        runtime_choice = st.selectbox(
            "Runtime Version *",
            options=[r["id"] for r in runtimes],
            format_func=lambda x: next(r["label"] for r in runtimes if r["id"] == x),
            index=0
        )
    with col_b:
        startup_cmd = st.text_input("Custom Startup Command (Optional)", placeholder="python bot.py (auto-detected if blank)")
        description = st.text_input("Description (Optional)", placeholder="Telegram media downloader bot")

    uploaded_zip = st.file_uploader("Upload Project Archive (.ZIP) *", type=["zip"], help="Maximum upload size: 200MB")
    install_deps_on_start = st.checkbox("Automatically install requirements.txt on build", value=True)
    start_immediately = st.checkbox("Start bot immediately after creation", value=True)

    submitted = st.form_submit_button("⚡ Create & Deploy Bot", type="primary", use_container_width=True)

    if submitted:
        if not bot_name:
            st.error("Please provide a project name.")
        elif not uploaded_zip:
            st.error("Please upload a ZIP file containing your project code.")
        else:
            with st.status("🚀 Deploying Python Bot to Worker...", expanded=True) as status_box:
                st.write("📦 Validating archive and extracting files safely...")
                ok, msg, project = ProjectManager.create_project_from_zip(
                    user_id=user.id,
                    name=bot_name,
                    zip_file=uploaded_zip,
                    startup_cmd=startup_cmd if startup_cmd else None,
                    runtime_version=runtime_choice,
                    description=description
                )

                if not ok:
                    status_box.update(label="❌ Archive validation failed", state="error")
                    st.error(f"Deployment failed: {msg}")
                else:
                    st.write(f"✓ Archive verified: {msg}")
                    if start_immediately:
                        st.write("⚙️ Preparing worker environment and launching process...")
                        d_ok, d_msg, dep = DeploymentEngine.deploy_project(user.id, project.id, install_deps=install_deps_on_start)
                        if d_ok:
                            st.write(f"✓ Worker process active: {d_msg}")
                            status_box.update(label=f"🎉 Bot '{project.name}' successfully deployed!", state="complete", expanded=False)
                            st.toast(f"Bot '{project.name}' deployed and running!", icon="🚀")
                        else:
                            status_box.update(label="❌ Process startup failed", state="error")
                            st.error(d_msg)
                    else:
                        status_box.update(label=f"✓ Bot '{project.name}' created (Stopped)", state="complete", expanded=False)
                        st.toast(f"Bot '{project.name}' created!", icon="✅")

                    st.session_state["current_project_id"] = project.id
                    st.info("Redirecting to bot console...")
                    st.switch_page("pages/console.py")

render_developer_footer()
