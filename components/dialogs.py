"""
NEXHOST CLOUD - Modern Streamlit Action Dialogs and Safety Modals
Author: @Harsh_54x
"""

import streamlit as st

def confirm_action_banner(warning_text: str, button_label: str, action_key: str) -> bool:
    """
    Render confirmation banner for destructive actions.
    Returns True only when the user confirms.
    """
    st.warning(f"⚠️ {warning_text}")
    col1, col2 = st.columns([1, 4])
    with col1:
        confirmed = st.button(button_label, key=action_key, type="primary")
    return confirmed

if hasattr(st, "dialog"):
    @st.dialog("⚠️ Confirm Critical Action")
    def show_confirmation_modal(title: str, message: str, on_confirm_key: str):
        """
        Streamlit 1.34+ Native Modal Dialog for enterprise-grade confirmation workflows.
        """
        st.write(f"### {title}")
        st.write(message)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Proceed", type="primary", key=f"modal_yes_{on_confirm_key}", use_container_width=True):
                st.session_state[on_confirm_key] = True
                st.rerun()
        with col2:
            if st.button("Cancel", key=f"modal_no_{on_confirm_key}", use_container_width=True):
                st.rerun()
