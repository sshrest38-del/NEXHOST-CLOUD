"""
NEXHOST CLOUD - In-Browser File Manager and Source Code Editor
Author: @Harsh_54x
"""

import streamlit as st
from auth.sessions import get_current_user, is_logged_in
from components.theme import apply_custom_theme, render_developer_footer, safe_set_page_config
from components.navbar import render_navbar
from components.sidebar import render_sidebar
from database.projects import ProjectRepository
from services.storage_service import StorageService
from utils.helpers import format_bytes

safe_set_page_config(title="File Manager - NEXHOST CLOUD", icon="🗂️", layout="wide")
apply_custom_theme()

if not is_logged_in():
    st.warning("⚠️ Please log in to access the file manager.")
    st.stop()

render_navbar()
render_sidebar()
user = get_current_user()

st.title("🗂️ Project File Manager")
st.caption("Inspect, create, edit, upload, and organize your bot source files in an isolated filesystem.")

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

# Current Directory Navigation State
if "fm_subpath" not in st.session_state:
    st.session_state["fm_subpath"] = ""

subpath = st.session_state["fm_subpath"]

col_path, col_up = st.columns([4, 1])
with col_path:
    st.markdown(f"**Current Directory:** `/app/{subpath}`")
with col_up:
    if subpath:
        if st.button("⬆️ Up One Folder", use_container_width=True):
            parts = subpath.strip("/").split("/")
            st.session_state["fm_subpath"] = "/".join(parts[:-1])
            st.rerun()

# Actions Row: Create file, Create folder, Upload file
tab_files, tab_create, tab_upload = st.tabs(["📄 Directory Contents", "➕ Create File / Folder", "⬆️ Upload File"])

with tab_create:
    c_f1, c_f2 = st.columns(2)
    with c_f1:
        new_filename = st.text_input("New File Name", placeholder="e.g. config.py")
        if st.button("Create File", key="btn_create_file"):
            if new_filename:
                rel = f"{subpath}/{new_filename}".lstrip("/")
                ok = StorageService.write_file(user.id, chosen_id, rel, "# Created via NEXHOST CLOUD File Manager\n")
                if ok:
                    st.success(f"File '{new_filename}' created!")
                    st.rerun()
                else:
                    st.error("Failed to create file.")
    with c_f2:
        new_folder = st.text_input("New Directory Name", placeholder="e.g. handlers")
        if st.button("Create Directory", key="btn_create_dir"):
            if new_folder:
                rel = f"{subpath}/{new_folder}".lstrip("/")
                ok = StorageService.create_directory(user.id, chosen_id, rel)
                if ok:
                    st.success(f"Folder '{new_folder}' created!")
                    st.rerun()
                else:
                    st.error("Failed to create directory.")

with tab_upload:
    uploaded_single = st.file_uploader("Upload file to current directory", key="fm_upload")
    if uploaded_single and st.button("Save Uploaded File", type="primary"):
        rel = f"{subpath}/{uploaded_single.name}".lstrip("/")
        ok = StorageService.save_uploaded_binary(user.id, chosen_id, rel, uploaded_single.getvalue())
        if ok:
            st.success(f"Uploaded '{uploaded_single.name}'!")
            st.rerun()
        else:
            st.error("Failed to save file.")

with tab_files:
    items = StorageService.list_files(user.id, chosen_id, subpath)
    if not items:
        st.info("This directory is empty.")
    else:
        for it in items:
            col_icon, col_name, col_size, col_act1, col_act2 = st.columns([0.4, 3, 1.2, 1, 1])
            with col_icon:
                st.write("📁" if it["is_dir"] else "📄")
            with col_name:
                if it["is_dir"]:
                    if st.button(f"{it['name']}/", key=f"open_dir_{it['name']}"):
                        st.session_state["fm_subpath"] = it["relative_path"]
                        st.rerun()
                else:
                    st.write(it["name"])
            with col_size:
                st.caption("Folder" if it["is_dir"] else format_bytes(it["size_bytes"]))
            with col_act1:
                if not it["is_dir"]:
                    if st.button("✏️ Edit", key=f"edit_{it['relative_path']}"):
                        st.session_state["fm_editing_file"] = it["relative_path"]
            with col_act2:
                if st.button("🗑️ Del", key=f"del_it_{it['relative_path']}"):
                    StorageService.delete_item(user.id, chosen_id, it["relative_path"])
                    st.rerun()

# File Editor Section
if "fm_editing_file" in st.session_state:
    edit_rel = st.session_state["fm_editing_file"]
    st.markdown("---")
    st.subheader(f"✏️ Editing: `{edit_rel}`")

    content = StorageService.read_file(user.id, chosen_id, edit_rel)
    if content is None:
        st.error("Could not load file content or file is binary.")
        if st.button("Close Editor"):
            st.session_state.pop("fm_editing_file", None)
            st.rerun()
    else:
        new_content = st.text_area("File Content", value=content, height=350)
        c_sv, c_cl = st.columns([1, 4])
        with c_sv:
            if st.button("💾 Save File", type="primary"):
                ok = StorageService.write_file(user.id, chosen_id, edit_rel, new_content)
                if ok:
                    st.success("File saved successfully!")
                else:
                    st.error("Error saving file.")
        with c_cl:
            if st.button("Close"):
                st.session_state.pop("fm_editing_file", None)
                st.rerun()

render_developer_footer()
