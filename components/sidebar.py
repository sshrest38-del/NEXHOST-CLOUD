"""
NEXHOST CLOUD - Custom Sidebar Navigation and Plan Quota Widget
Author: @Harsh_54x
"""

import streamlit as st
from config import PLATFORM_NAME, DEVELOPER_HANDLE, DEVELOPER_TELEGRAM
from auth.sessions import get_current_user, is_logged_in, clear_session
from auth.permissions import is_admin
from core.membership_engine import MembershipEngine
from services.notification_service import NotificationService

def render_sidebar():
    """Render full-featured, role-aware sidebar navigation."""
    user = get_current_user()
    if not user:
        return

    with st.sidebar:
        # User profile badge
        st.markdown(f"""
        <div style="padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.08); margin-bottom: 15px;">
            <div style="font-size: 0.8rem; color: #9CA3AF; text-transform: uppercase; letter-spacing: 0.05em;">Logged In As</div>
            <div style="font-weight: 700; font-size: 1.05rem; color: #FFFFFF;">{user.full_name or user.username}</div>
            <div style="font-size: 0.78rem; color: #6366F1; font-weight: 600;">@{user.username} &bull; {user.role.upper()}</div>
        </div>
        """, unsafe_allow_html=True)

        # Quota meters
        limits = MembershipEngine.get_user_limits(user.id)
        current_bots = limits["current_bots"]
        max_bots = limits["max_bots"]
        quota_ratio = min(1.0, current_bots / max_bots) if max_bots > 0 else 1.0

        st.markdown(f"**Bot Quota: {current_bots} / {max_bots} Used**")
        st.progress(quota_ratio)

        # Storage meter
        used_mb = limits["used_storage_mb"]
        max_storage = limits["max_storage_mb"]
        storage_ratio = min(1.0, used_mb / max_storage) if max_storage > 0 else 0.0
        st.caption(f"Storage: {used_mb:.1f} MB / {max_storage} MB ({limits['storage_percent']}%)")
        st.progress(storage_ratio)

        st.markdown("---")

        # Developer Contact Button
        st.markdown(f"""
        <div style="margin-bottom: 14px;">
            <a href="{DEVELOPER_TELEGRAM}" target="_blank" style="display: flex; align-items: center; justify-content: center; gap: 8px; width: 100%; background: linear-gradient(135deg, #10B981, #059669); color: #FFFFFF; font-weight: 700; font-size: 0.82rem; padding: 8px 12px; border-radius: 9px; text-decoration: none; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.25);">
                💬 Contact {DEVELOPER_HANDLE}
            </a>
        </div>
        """, unsafe_allow_html=True)

        # Logout button
        if st.button("🚪 Logout", use_container_width=True):
            clear_session()
            st.rerun()

        st.markdown(f"""
        <div style="text-align: center; margin-top: 25px; font-size: 0.72rem; color: #4B5563;">
            {PLATFORM_NAME}<br>
            Dev: <a href="{DEVELOPER_TELEGRAM}" target="_blank" style="color: #6366F1;">{DEVELOPER_HANDLE}</a>
        </div>
        """, unsafe_allow_html=True)
