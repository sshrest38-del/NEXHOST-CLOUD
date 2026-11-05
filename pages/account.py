"""
NEXHOST CLOUD - Account Profile and Security Settings
Author: @Harsh_54x
"""

import streamlit as st
from auth.sessions import get_current_user, is_logged_in, clear_session
from auth.password_reset import change_password
from components.theme import apply_custom_theme, render_developer_footer, safe_set_page_config
from components.navbar import render_navbar
from components.sidebar import render_sidebar
from database.memberships import MembershipRepository
from core.membership_engine import MembershipEngine

safe_set_page_config(title="Account Settings - NEXHOST CLOUD", icon="👤", layout="wide")
apply_custom_theme()

if not is_logged_in():
    st.warning("⚠️ Please log in to manage your account.")
    st.stop()

render_navbar()
render_sidebar()
user = get_current_user()

st.title("👤 Account & Security Settings")
st.caption("Manage your profile credentials, change passwords, and review subscription history.")

limits = MembershipEngine.get_user_limits(user.id)

tab_profile, tab_security, tab_history = st.tabs(["👤 Profile Overview", "🔒 Security & Password", "📜 Membership History"])

with tab_profile:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="nex-card">
            <div class="nex-card-header">Account Details</div>
            <div style="font-size: 0.9rem; color: #D1D5DB; line-height: 2;">
                <strong>Username:</strong> @{user.username}<br>
                <strong>Email:</strong> {user.email}<br>
                <strong>Full Name:</strong> {user.full_name or 'N/A'}<br>
                <strong>Account Role:</strong> <span style="color: #6366F1; font-weight: 700;">{user.role.upper()}</span><br>
                <strong>Account Status:</strong> <span style="color: #10B981; font-weight: 700;">{'ACTIVE' if user.is_active else 'SUSPENDED'}</span><br>
                <strong>Member Since:</strong> {user.created_at.strftime('%Y-%m-%d')}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="nex-card">
            <div class="nex-card-header">Current Plan Quotas</div>
            <div style="font-size: 0.9rem; color: #D1D5DB; line-height: 2;">
                <strong>Active Plan:</strong> {limits['plan_display']}<br>
                <strong>Max Bots:</strong> {limits['max_bots']}<br>
                <strong>RAM Limit:</strong> {limits['max_ram_mb']} MB<br>
                <strong>Storage Quota:</strong> {limits['max_storage_mb']} MB<br>
                <strong>Priority Support:</strong> {limits['support_tier']}
            </div>
        </div>
        """, unsafe_allow_html=True)

with tab_security:
    st.subheader("Update Password")
    with st.form("change_pw_form"):
        old_pass = st.text_input("Current Password", type="password")
        new_pass = st.text_input("New Password (min 6 chars)", type="password")
        confirm_pass = st.text_input("Confirm New Password", type="password")

        if st.form_submit_button("Update Password", type="primary"):
            if not old_pass or not new_pass:
                st.error("Please fill in all password fields.")
            elif new_pass != confirm_pass:
                st.error("New passwords do not match.")
            else:
                ok, msg = change_password(user.id, old_pass, new_pass)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)

with tab_history:
    st.subheader("Subscription Records")
    history = MembershipRepository.list_history(user.id)
    if not history:
        st.info("No prior subscription history.")
    else:
        for m in history:
            st.markdown(f"""
            <div style="background: rgba(31, 41, 55, 0.6); padding: 10px 14px; border-radius: 8px; margin-bottom: 8px; display: flex; justify-content: space-between;">
                <div>
                    <strong>{m.plan.display_name if m.plan else 'Plan'}</strong> &bull;
                    Status: <span style="color: {'#10B981' if m.status == 'ACTIVE' else '#9CA3AF'}; font-weight: 700;">{m.status}</span>
                </div>
                <div style="font-size: 0.85rem; color: #9CA3AF;">
                    Started: {m.started_at.strftime('%Y-%m-%d')} &bull; Expires: {m.expires_at.strftime('%Y-%m-%d')}
                </div>
            </div>
            """, unsafe_allow_html=True)

render_developer_footer()
