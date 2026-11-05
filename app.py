"""
NEXHOST CLOUD - Master Entrypoint Application
Developer: @Harsh_54x (https://t.me/Harsh_54x)
Tagline: Your Bots. Your Cloud.
"""

import streamlit as st
from config import PLATFORM_NAME, TAGLINE, DEVELOPER_HANDLE, DEVELOPER_TELEGRAM
from database.connection import init_db
from database.plans import PlanRepository
from auth.sessions import init_session, is_logged_in, get_current_user, clear_session
from auth.authentication import login
from auth.registration import register_user
from components.theme import apply_custom_theme, render_developer_footer
from components.navbar import render_navbar
from components.sidebar import render_sidebar
from components.cards import plan_pricing_card

# Initialize database schema and default records
init_db()

# Streamlit Page Setup
st.set_page_config(
    page_title=f"{PLATFORM_NAME} - {TAGLINE}",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply global styling
apply_custom_theme()
init_session()

# Render Navbar
render_navbar()

if is_logged_in():
    # Authenticated user view
    render_sidebar()
    user = get_current_user()

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(16, 185, 129, 0.1) 100%); border: 1px solid rgba(99, 102, 241, 0.3); border-radius: 16px; padding: 2rem; margin-bottom: 2rem;">
        <h1 style="color: #FFFFFF; font-size: 2.2rem; font-weight: 800; margin-bottom: 0.4rem;">
            Welcome back, {user.full_name or user.username}! 🚀
        </h1>
        <p style="color: #D1D5DB; font-size: 1.05rem; margin-bottom: 1.2rem;">
            Manage your Python Telegram bots with high-speed isolated execution, live console streaming, and instant crash recovery.
        </p>
        <div style="display: flex; gap: 12px; flex-wrap: wrap;">
            <a href="/dashboard" target="_self" style="background: #6366F1; color: #FFF; font-weight: 700; padding: 10px 22px; border-radius: 9px; text-decoration: none; box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);">
                📊 Open Dashboard
            </a>
            <a href="/deploy" target="_self" style="background: #10B981; color: #FFF; font-weight: 700; padding: 10px 22px; border-radius: 9px; text-decoration: none;">
                ⚡ Deploy New Bot
            </a>
            <a href="/my_projects" target="_self" style="background: #1F2937; color: #FFF; font-weight: 700; padding: 10px 22px; border-radius: 9px; text-decoration: none; border: 1px solid rgba(255,255,255,0.15);">
                📁 My Projects
            </a>
            <a href="{DEVELOPER_TELEGRAM}" target="_blank" style="background: #374151; color: #E5E7EB; font-weight: 600; padding: 10px 20px; border-radius: 9px; text-decoration: none;">
                💬 Contact {DEVELOPER_HANDLE}
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Quick Feature Links
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="nex-card">
            <div class="nex-card-header">🚀 1-Click Bot Deployment</div>
            <p style="color: #9CA3AF; font-size: 0.9rem;">Upload ZIP files or clone GitHub repos. Automatic requirements detection and environment configuration.</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="nex-card">
            <div class="nex-card-header">🛡️ Isolated Worker Sandboxes</div>
            <p style="color: #9CA3AF; font-size: 0.9rem;">Hardened non-root containers with strict CPU, memory and storage quotas. Auto crash restarts.</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="nex-card">
            <div class="nex-card-header">💳 Instant UPI Upgrades</div>
            <p style="color: #9CA3AF; font-size: 0.9rem;">Pay seamlessly via Indian UPI QR with manual admin verification and zero hidden platform fees.</p>
        </div>
        """, unsafe_allow_html=True)

else:
    # Public Landing Page & Auth Portal
    st.markdown(f"""
    <div style="text-align: center; padding: 2.5rem 1rem 1.5rem 1rem;">
        <span style="background: rgba(99, 102, 241, 0.15); border: 1px solid rgba(99, 102, 241, 0.3); color: #A5B4FC; font-size: 0.85rem; font-weight: 700; padding: 5px 16px; border-radius: 9999px; text-transform: uppercase;">
            Next-Generation Python Cloud
        </span>
        <h1 style="font-size: 3.2rem; font-weight: 900; letter-spacing: -0.03em; margin-top: 1rem; color: #FFFFFF;">
            {PLATFORM_NAME}
        </h1>
        <p style="font-size: 1.3rem; color: #9CA3AF; max-width: 650px; margin: 0 auto 1.5rem auto;">
            {TAGLINE} &mdash; Production-grade, isolated Telegram bot cloud hosting with real-time logs, zero setup hassles, and INR UPI payments.
        </p>
        <div style="display: flex; justify-content: center; gap: 12px; margin-bottom: 2rem;">
            <a href="{DEVELOPER_TELEGRAM}" target="_blank" class="dev-pill" style="font-size: 0.95rem; padding: 8px 20px;">
                💬 Contact Developer ({DEVELOPER_HANDLE})
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Auth Tabs
    tab_login, tab_register, tab_plans = st.tabs(["🔑 Log In", "📝 Create Account", "💎 Membership Plans"])

    with tab_login:
        st.markdown("<div style='max-width: 480px; margin: 0 auto;'>", unsafe_allow_html=True)
        st.subheader("Welcome Back")
        login_ident = st.text_input("Username or Email", placeholder="e.g. user@example.com or username", key="login_id")
        login_pass = st.text_input("Password", type="password", placeholder="Enter your password", key="login_pw")
        
        if st.button("Log In to Account", type="primary", use_container_width=True):
            ok, msg, u = login(login_ident, login_pass)
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)
        st.markdown("</div>", unsafe_allow_html=True)

    with tab_register:
        st.markdown("<div style='max-width: 480px; margin: 0 auto;'>", unsafe_allow_html=True)
        st.subheader("Start Free with 1 Bot Slot")
        reg_email = st.text_input("Email Address", placeholder="user@example.com", key="reg_em")
        reg_username = st.text_input("Username", placeholder="alphabot_dev", key="reg_un")
        reg_fullname = st.text_input("Full Name (Optional)", placeholder="Harsh Sharma", key="reg_fn")
        reg_pass = st.text_input("Password (min. 6 characters)", type="password", key="reg_pw")

        if st.button("Create My Account", type="primary", use_container_width=True):
            ok, msg, u = register_user(reg_email, reg_username, reg_pass, reg_fullname)
            if ok:
                st.success(msg)
            else:
                st.error(msg)
        st.markdown("</div>", unsafe_allow_html=True)

    with tab_plans:
        st.subheader("Transparent Pricing in Indian Rupees (₹)")
        st.caption("All plans include automated crash recovery, console streaming, and isolated workers.")

        plans = PlanRepository.list_all(active_only=True)
        cols = st.columns(len(plans)) if plans else []
        for i, plan in enumerate(plans):
            with cols[i]:
                is_popular = (plan.name == "PRO")
                card_html = plan_pricing_card(
                    name=plan.name,
                    price_inr=plan.price_inr,
                    max_bots=plan.max_bots,
                    max_ram_mb=plan.max_ram_mb,
                    max_cpu=plan.max_cpu_cores,
                    max_storage_mb=plan.max_storage_mb,
                    backup=plan.backup_enabled,
                    support=plan.support_tier,
                    is_popular=is_popular
                )
                st.markdown(card_html, unsafe_allow_html=True)

# Footer
render_developer_footer()
