"""
NEXHOST CLOUD - Top Navigation Bar Component
Author: @Harsh_54x
"""

import streamlit as st
from config import PLATFORM_NAME, DEVELOPER_HANDLE, DEVELOPER_TELEGRAM
from auth.sessions import get_current_user, is_logged_in
from core.membership_engine import MembershipEngine
from services.notification_service import NotificationService

def render_navbar():
    """Render sleek modern top navbar."""
    user = get_current_user()
    unread_count = NotificationService.get_unread_count(user.id) if user else 0
    limits = MembershipEngine.get_user_limits(user.id) if user else {}

    plan_name = limits.get("plan_name", "FREE")
    role = (user.role if user else "guest").replace("_", " ").upper()

    col_brand, col_actions = st.columns([1.8, 2.2])

    with col_brand:
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 10px; margin-top: 4px;">
            <div style="background: linear-gradient(135deg, #6366F1, #8B5CF6); width: 34px; height: 34px; border-radius: 9px; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 1.1rem; color: #FFF; box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);">
                N
            </div>
            <div>
                <span style="font-weight: 800; font-size: 1.25rem; letter-spacing: -0.02em; color: #FFFFFF;">{PLATFORM_NAME}</span>
                <span style="display: block; font-size: 0.72rem; color: #9CA3AF; margin-top: -2px;">Your Bots. Your Cloud.</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_actions:
        st.markdown(f"""
        <div style="display: flex; justify-content: flex-end; align-items: center; gap: 8px; flex-wrap: wrap;">
            <span style="background: rgba(99, 102, 241, 0.15); border: 1px solid rgba(99, 102, 241, 0.3); color: #A5B4FC; font-size: 0.76rem; font-weight: 700; padding: 3px 10px; border-radius: 9999px;">
                ⭐ {plan_name}
            </span>
            <span style="background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.3); color: #6EE7B7; font-size: 0.76rem; font-weight: 700; padding: 3px 10px; border-radius: 9999px;">
                {role}
            </span>
            <a href="{DEVELOPER_TELEGRAM}" target="_blank" style="text-decoration: none; background: #1E293B; border: 1px solid rgba(255,255,255,0.1); color: #E2E8F0; font-size: 0.76rem; font-weight: 600; padding: 4px 10px; border-radius: 8px; display: inline-flex; align-items: center; gap: 4px;">
                💬 Contact {DEVELOPER_HANDLE}
            </a>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr style='border: 0; border-top: 1px solid rgba(255,255,255,0.08); margin: 0.6rem 0 1.2rem 0;' />", unsafe_allow_html=True)
