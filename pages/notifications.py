"""
NEXHOST CLOUD - User Notification Center
Author: @Harsh_54x
"""

import streamlit as st
from auth.sessions import get_current_user, is_logged_in
from components.theme import apply_custom_theme, render_developer_footer, safe_set_page_config
from components.navbar import render_navbar
from components.sidebar import render_sidebar
from services.notification_service import NotificationService

safe_set_page_config(title="Notifications - NEXHOST CLOUD", icon="🔔", layout="wide")
apply_custom_theme()

if not is_logged_in():
    st.warning("⚠️ Please log in to view notifications.")
    st.stop()

render_navbar()
render_sidebar()
user = get_current_user()

col_t, col_btn = st.columns([4, 1.5])
with col_t:
    st.title("🔔 Notifications Center")
    st.caption("Stay updated with deployment statuses, plan activations, and administrative alerts.")
with col_btn:
    if st.button("Mark All as Read", use_container_width=True):
        NotificationService.mark_all_read(user.id)
        st.success("All notifications marked as read.")
        st.rerun()

notifs = NotificationService.get_recent(user.id, limit=30)
if not notifs:
    st.info("No notifications to display right now.")
else:
    for n in notifs:
        border_color = {
            "SUCCESS": "#10B981",
            "ERROR": "#EF4444",
            "WARNING": "#F59E0B",
            "INFO": "#6366F1"
        }.get(n.level, "#6366F1")

        unread_badge = '<span style="background: #6366F1; color: #FFF; font-size: 0.65rem; font-weight: 800; padding: 2px 6px; border-radius: 4px; margin-left: 8px;">NEW</span>' if not n.is_read else ""

        st.markdown(f"""
        <div style="background: rgba(17, 24, 39, 0.75); border-left: 4px solid {border_color}; border-radius: 8px; padding: 1rem; margin-bottom: 0.8rem; border-top: 1px solid rgba(255,255,255,0.05); border-right: 1px solid rgba(255,255,255,0.05); border-bottom: 1px solid rgba(255,255,255,0.05);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="font-weight: 700; color: #FFFFFF; font-size: 1rem;">
                    {n.title} {unread_badge}
                </div>
                <div style="font-size: 0.75rem; color: #6B7280;">
                    {n.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")}
                </div>
            </div>
            <div style="font-size: 0.88rem; color: #D1D5DB; margin-top: 6px;">
                {n.message}
            </div>
        </div>
        """, unsafe_allow_html=True)

render_developer_footer()
