"""
NEXHOST CLOUD - Manual UPI Payment Workflow and Verification Tracking
Author: @Harsh_54x
"""

import os
from pathlib import Path
import streamlit as st
from auth.sessions import get_current_user, is_logged_in
from components.theme import apply_custom_theme, render_developer_footer, safe_set_page_config
from components.navbar import render_navbar
from components.sidebar import render_sidebar
from components.tables import render_payments_table
from config import ADMIN_UPI_ID, ADMIN_UPI_NAME, ADMIN_PAYMENT_NOTE, UPI_QR_IMAGE_PATH, DEVELOPER_TELEGRAM
from database.plans import PlanRepository
from database.payments import PaymentRepository
from core.payment_engine import PaymentEngine
from utils.helpers import format_currency

safe_set_page_config(title="Payments - NEXHOST CLOUD", icon="💳", layout="wide")
apply_custom_theme()

if not is_logged_in():
    st.warning("⚠️ Please log in to access the payment portal.")
    st.stop()

render_navbar()
render_sidebar()
user = get_current_user()

st.title("💳 Manual UPI Payment Portal")
st.caption("Subscribe or upgrade to premium plans securely via Google Pay, PhonePe, Paytm or any UPI app.")

paid_plans = [p for p in PlanRepository.list_all(active_only=True) if p.price_inr > 0]
if not paid_plans:
    st.info("No premium plans are currently available for purchase.")
    st.stop()

# Check for preselected plan from membership page
preselected_id = st.session_state.get("checkout_plan_id", paid_plans[0].id)
plan_dict = {p.id: p for p in paid_plans}
current_plan_id = preselected_id if preselected_id in plan_dict else paid_plans[0].id

col_left, col_right = st.columns([1.2, 1.8])

with col_left:
    st.subheader("1. Payment Details")
    chosen_plan_id = st.selectbox(
        "Select Membership Plan",
        options=list(plan_dict.keys()),
        format_func=lambda x: f"{plan_dict[x].display_name} — {format_currency(plan_dict[x].price_inr)}",
        index=list(plan_dict.keys()).index(current_plan_id)
    )
    target_plan = plan_dict[chosen_plan_id]

    st.markdown(f"""
    <div class="nex-card">
        <div style="font-size: 0.85rem; color: #9CA3AF;">Payable Amount</div>
        <div style="font-size: 2.2rem; font-weight: 800; color: #10B981;">{format_currency(target_plan.price_inr)}</div>
        <div style="font-size: 0.8rem; color: #D1D5DB; margin-top: 4px;">
            Includes: <strong>{target_plan.max_bots} Bots</strong> &bull; <strong>{target_plan.max_ram_mb} MB RAM</strong>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # UPI QR display
    if Path(UPI_QR_IMAGE_PATH).exists():
        st.image(UPI_QR_IMAGE_PATH, caption=f"Scan to pay {format_currency(target_plan.price_inr)} via any UPI App", width=220)

    st.markdown(f"""
    <div style="background: rgba(31, 41, 55, 0.7); border: 1px solid rgba(255,255,255,0.1); border-radius: 10px; padding: 12px; margin-top: 10px;">
        <div style="font-size: 0.78rem; color: #9CA3AF;">UPI ID:</div>
        <code style="font-size: 1.05rem; color: #A5B4FC; font-weight: 700;">{ADMIN_UPI_ID}</code>
        <div style="font-size: 0.78rem; color: #9CA3AF; margin-top: 6px;">Payee Name:</div>
        <div style="font-size: 0.9rem; font-weight: 600; color: #FFFFFF;">{ADMIN_UPI_NAME}</div>
    </div>
    """, unsafe_allow_html=True)

with col_right:
    st.subheader("2. Submit Transaction Proof")
    st.markdown("""
    **Instructions:**
    1. Open GPay / PhonePe / Paytm / BHIM and transfer the exact amount shown.
    2. Note the **12-digit UPI Reference Number / UTR** from your banking transaction details.
    3. Take a screenshot showing the completed transaction.
    4. Fill in the form below and click Submit.
    """)

    with st.form("manual_upi_submit_form"):
        utr_number = st.text_input("12-Digit UPI Transaction Reference (UTR) *", placeholder="e.g. 431289123456")
        proof_image = st.file_uploader("Upload Payment Screenshot *", type=["png", "jpg", "jpeg", "webp"])

        st.caption("🔒 All payment submissions are independently audited by an administrator before activation. Duplicate reference numbers are immediately rejected.")

        submitted = st.form_submit_button("Submit Payment Request for Review", type="primary", use_container_width=True)

        if submitted:
            if not utr_number:
                st.error("Please enter the transaction reference / UTR number.")
            elif not proof_image:
                st.error("Please upload the payment confirmation screenshot.")
            else:
                with st.spinner("Submitting payment request for admin verification..."):
                    ok, msg, payment = PaymentEngine.submit_payment_request(
                        user_id=user.id,
                        plan_id=target_plan.id,
                        upi_ref_id=utr_number,
                        screenshot_bytes=proof_image.getvalue(),
                        filename=proof_image.name
                    )

                    if ok:
                        st.success(msg)
                        st.balloons()
                    else:
                        st.error(msg)

st.markdown("---")
st.subheader("📜 Your Payment History")
my_payments = PaymentRepository.list_by_user(user.id)
render_payments_table(my_payments, is_admin=False)

render_developer_footer()
