"""
NEXHOST CLOUD - Membership Plans and Upgrades
Author: @Harsh_54x
"""

import streamlit as st
from auth.sessions import get_current_user, is_logged_in
from components.theme import apply_custom_theme, render_developer_footer, safe_set_page_config
from components.navbar import render_navbar
from components.sidebar import render_sidebar
from components.cards import plan_pricing_card
from database.plans import PlanRepository
from core.membership_engine import MembershipEngine

safe_set_page_config(title="Membership Plans - NEXHOST CLOUD", icon="💎", layout="wide")
apply_custom_theme()

if not is_logged_in():
    st.warning("⚠️ Please log in to view membership details.")
    st.stop()

render_navbar()
render_sidebar()
user = get_current_user()

st.title("💎 Cloud Membership Plans")
st.caption("Scale your Telegram bot infrastructure with dedicated hardware allocations and priority support.")

limits = MembershipEngine.get_user_limits(user.id)
active_plan_name = limits["plan_name"]
exp_date = limits["expires_at"].strftime("%Y-%m-%d") if limits["expires_at"] else "Never (Lifetime)"

st.markdown(f"""
<div class="nex-card" style="border-color: rgba(99, 102, 241, 0.4); margin-bottom: 2rem;">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
        <div>
            <span style="font-size: 0.85rem; color: #9CA3AF; text-transform: uppercase;">Current Subscription</span>
            <div style="font-size: 1.6rem; font-weight: 800; color: #FFFFFF;">{limits['plan_display']}</div>
            <div style="font-size: 0.85rem; color: #A5B4FC; margin-top: 2px;">
                Expires: <strong>{exp_date}</strong> &bull; Bots: <strong>{limits['current_bots']} / {limits['max_bots']}</strong>
            </div>
        </div>
        <div>
            <span style="background: rgba(16, 185, 129, 0.2); color: #10B981; padding: 6px 14px; border-radius: 9999px; font-weight: 700; font-size: 0.9rem;">
                ● Active Status
            </span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Grid of Plans
plans = PlanRepository.list_all(active_only=True)
cols = st.columns(len(plans)) if plans else []

for i, plan in enumerate(plans):
    with cols[i]:
        is_current = (plan.name == active_plan_name)
        is_popular = (plan.name == "PRO")

        st.markdown(plan_pricing_card(
            name=plan.name,
            price_inr=plan.price_inr,
            max_bots=plan.max_bots,
            max_ram_mb=plan.max_ram_mb,
            max_cpu=plan.max_cpu_cores,
            max_storage_mb=plan.max_storage_mb,
            backup=plan.backup_enabled,
            support=plan.support_tier,
            is_current=is_current,
            is_popular=is_popular
        ), unsafe_allow_html=True)

        if plan.price_inr == 0:
            st.button("Default Plan", key=f"plan_btn_{plan.id}", disabled=True, use_container_width=True)
        elif is_current:
            st.button("Current Plan", key=f"plan_btn_{plan.id}", disabled=True, use_container_width=True)
        else:
            if st.button(f"Upgrade to {plan.name}", key=f"plan_btn_{plan.id}", type="primary", use_container_width=True):
                st.session_state["checkout_plan_id"] = plan.id
                st.switch_page("pages/payments.py")

render_developer_footer()
