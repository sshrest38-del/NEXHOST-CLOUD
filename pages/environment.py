"""
NEXHOST CLOUD - Environment Variables and Secrets Manager
Author: @Harsh_54x
"""

import streamlit as st
from auth.sessions import get_current_user, is_logged_in
from components.theme import apply_custom_theme, render_developer_footer, safe_set_page_config
from components.navbar import render_navbar
from components.sidebar import render_sidebar
from database.projects import ProjectRepository
from core.process_manager import ProcessManager

safe_set_page_config(title="Environment Variables - NEXHOST CLOUD", icon="⚙️", layout="wide")
apply_custom_theme()

if not is_logged_in():
    st.warning("⚠️ Please log in to manage environment variables.")
    st.stop()

render_navbar()
render_sidebar()
user = get_current_user()

st.title("⚙️ Environment Variables & Bot Secrets")
st.caption("Securely configure API keys, bot tokens, and runtime parameters. Secrets are automatically masked in console outputs.")

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
current_env = ProjectRepository.get_env_vars(chosen_id)

st.markdown("### ➕ Add New Variable")
with st.form("add_env_form", clear_on_submit=True):
    col_k, col_v = st.columns([1.5, 2.5])
    with col_k:
        new_key = st.text_input("Variable Name (KEY)", placeholder="e.g. BOT_TOKEN or API_KEY")
    with col_v:
        new_val = st.text_input("Value", placeholder="e.g. 123456:ABC-DEF...", type="password")

    add_btn = st.form_submit_button("Add Variable", type="primary")
    if add_btn:
        clean_key = (new_key or "").strip().upper()
        if not clean_key:
            st.error("Variable key cannot be empty.")
        else:
            current_env[clean_key] = new_val.strip()
            ProjectRepository.update_env_vars(chosen_id, current_env)
            st.success(f"Added variable `{clean_key}`!")
            st.rerun()

st.markdown("---")
st.markdown("### 📋 Active Variables")

if not current_env:
    st.info("No environment variables configured yet for this bot.")
else:
    reveal_all = st.checkbox("Reveal secret values", value=False)
    for key, val in list(current_env.items()):
        c1, c2, c3 = st.columns([2, 3, 1])
        with c1:
            st.code(key)
        with c2:
            display_val = val if reveal_all else ("*" * len(val) if val else "")
            st.text_input(label=key, value=display_val, disabled=True, label_visibility="collapsed", key=f"disp_{key}")
        with c3:
            if st.button("🗑️ Delete", key=f"del_env_{key}"):
                current_env.pop(key, None)
                ProjectRepository.update_env_vars(chosen_id, current_env)
                st.success(f"Removed `{key}`")
                st.rerun()

    st.markdown("---")
    st.warning("⚠️ Changes to environment variables require a bot restart to take effect.")
    if st.button("🔄 Restart Bot Now to Apply Secrets", type="primary"):
        with st.spinner("Restarting bot with updated secrets..."):
            ok, msg = ProcessManager.restart_bot(user.id, chosen_id)
            if ok:
                st.success("Bot restarted with updated configuration!")
            else:
                st.error(msg)

render_developer_footer()
