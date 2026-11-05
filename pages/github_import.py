"""
NEXHOST CLOUD - GitHub Repository Import and Deployment
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
from services.github_service import GitHubService

safe_set_page_config(title="GitHub Import - NEXHOST CLOUD", icon="🐙", layout="wide")
apply_custom_theme()

if not is_logged_in():
    st.warning("⚠️ Please log in to import GitHub repositories.")
    st.stop()

render_navbar()
render_sidebar()
user = get_current_user()

st.title("🐙 Import Bot from GitHub")
st.caption("Deploy public or private GitHub repositories directly to your NEXHOST CLOUD container.")

limits = MembershipEngine.get_user_limits(user.id)
if limits["remaining_slots"] <= 0:
    st.error(f"❌ You have reached your plan limit of {limits['max_bots']} bot(s). Please upgrade to deploy more.")
    if st.button("💎 Upgrade Membership"):
        st.switch_page("pages/membership.py")
    st.stop()

with st.form("github_import_form"):
    repo_url = st.text_input("GitHub Repository URL *", placeholder="https://github.com/owner/telegram-bot or owner/repo")
    branch = st.text_input("Git Branch", value="main", help="Target branch to clone and deploy")
    github_token = st.text_input("Personal Access Token (PAT)", type="password", help="Required only for private repositories. Leave empty for public repos.")
    
    col1, col2 = st.columns(2)
    with col1:
        bot_name = st.text_input("Project Name *", placeholder="e.g. MyGithubBot")
        runtimes = RuntimeManager.get_supported_runtimes()
        runtime_choice = st.selectbox("Runtime Version", options=[r["id"] for r in runtimes], index=0)
    with col2:
        startup_cmd = st.text_input("Custom Startup Command (Optional)", placeholder="python main.py (auto-detected if blank)")
        description = st.text_input("Description (Optional)", placeholder="GitHub imported bot")

    submitted = st.form_submit_button("🚀 Clone & Import Repository", type="primary", use_container_width=True)

    if submitted:
        if not repo_url or not bot_name:
            st.error("Please provide both the Repository URL and Project Name.")
        else:
            with st.spinner("Connecting to GitHub and downloading repository..."):
                ok, msg, project = ProjectManager.create_project_from_github(
                    user_id=user.id,
                    name=bot_name,
                    repo_url=repo_url,
                    branch=branch,
                    token=github_token if github_token else None,
                    startup_cmd=startup_cmd if startup_cmd else None,
                    runtime_version=runtime_choice,
                    description=description
                )

                if not ok:
                    st.error(msg)
                else:
                    st.success(msg)
                    st.session_state["current_project_id"] = project.id
                    st.info("Repository cloned! Redirecting to project console...")
                    st.switch_page("pages/console.py")

render_developer_footer()
