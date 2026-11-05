"""
NEXHOST CLOUD - Support Tickets and Direct Developer Assistance
Author: @Harsh_54x
"""

import streamlit as st
from auth.sessions import get_current_user, is_logged_in
from components.theme import apply_custom_theme, render_developer_footer, safe_set_page_config
from components.navbar import render_navbar
from components.sidebar import render_sidebar
from database.audit_logs import SupportTicketRepository
from config import DEVELOPER_HANDLE, DEVELOPER_TELEGRAM

safe_set_page_config(title="Support - NEXHOST CLOUD", icon="💬", layout="wide")
apply_custom_theme()

if not is_logged_in():
    st.warning("⚠️ Please log in to open support tickets.")
    st.stop()

render_navbar()
render_sidebar()
user = get_current_user()

st.title("💬 Help & Support Center")
st.caption("Need technical assistance with your bot deployment or payment verification? We are here to help.")

# Contact Developer Card
st.markdown(f"""
<div class="nex-card" style="border: 1px solid rgba(16, 185, 129, 0.35); background: linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(17, 24, 39, 0.8) 100%);">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
        <div>
            <div style="font-size: 1.25rem; font-weight: 800; color: #FFFFFF;">Instant Developer Support</div>
            <p style="color: #D1D5DB; font-size: 0.9rem; margin-top: 4px; margin-bottom: 0;">
                Reach out directly to lead architect <strong>{DEVELOPER_HANDLE}</strong> on Telegram for 24/7 priority troubleshooting and custom hosting inquiries.
            </p>
        </div>
        <div>
            <a href="{DEVELOPER_TELEGRAM}" target="_blank" style="display: inline-flex; align-items: center; gap: 8px; background: #10B981; color: #FFFFFF; font-weight: 700; font-size: 0.95rem; padding: 10px 22px; border-radius: 9px; text-decoration: none; box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4);">
                💬 Contact {DEVELOPER_HANDLE} on Telegram
            </a>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

tab_create, tab_my_tickets = st.tabs(["📝 Open New Ticket", "🎫 My Support Tickets"])

with tab_create:
    with st.form("new_ticket_form"):
        subject = st.text_input("Ticket Subject *", placeholder="e.g. Issue connecting Telegram webhook")
        priority = st.selectbox("Priority Level", ["NORMAL", "LOW", "HIGH", "URGENT"], index=0)
        message = st.text_area("Detailed Message *", placeholder="Describe the issue, error traceback, or request...", height=180)

        if st.form_submit_button("Submit Support Ticket", type="primary"):
            if not subject or not message:
                st.error("Please provide both subject and detailed message.")
            else:
                ticket = SupportTicketRepository.create(user.id, subject, message, priority)
                st.success(f"Ticket #{ticket.id} submitted! Our support team will review it shortly.")
                st.rerun()

with tab_my_tickets:
    tickets = SupportTicketRepository.list_by_user(user.id)
    if not tickets:
        st.info("You haven't opened any support tickets yet.")
    else:
        for t in tickets:
            status_color = "#10B981" if t.status == "RESOLVED" else "#F59E0B"
            st.markdown(f"""
            <div class="nex-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="font-weight: 700; color: #FFFFFF; font-size: 1.1rem;">
                        #{t.id} &bull; {t.subject}
                    </div>
                    <div>
                        <span style="background: {status_color}22; color: {status_color}; border: 1px solid {status_color}44; font-size: 0.78rem; font-weight: 700; padding: 3px 10px; border-radius: 9999px;">
                            {t.status}
                        </span>
                    </div>
                </div>
                <div style="font-size: 0.85rem; color: #D1D5DB; margin-top: 8px;">
                    {t.message}
                </div>
                <div style="font-size: 0.75rem; color: #6B7280; margin-top: 8px;">
                    Submitted: {t.created_at.strftime('%Y-%m-%d %H:%M UTC')} &bull; Priority: {t.priority}
                </div>
            </div>
            """, unsafe_allow_html=True)

            if t.admin_reply:
                st.markdown(f"""
                <div style="background: rgba(99, 102, 241, 0.1); border-left: 3px solid #6366F1; border-radius: 6px; padding: 10px 14px; margin-left: 20px; margin-bottom: 15px;">
                    <strong style="color: #A5B4FC;">🛡️ Admin Support Reply:</strong>
                    <div style="color: #F3F4F6; font-size: 0.88rem; margin-top: 4px;">{t.admin_reply}</div>
                </div>
                """, unsafe_allow_html=True)

render_developer_footer()
