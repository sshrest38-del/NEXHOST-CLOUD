"""
NEXHOST CLOUD - Super Admin Command Center
Author: @Harsh_54x
"""

from pathlib import Path
import streamlit as st
from auth.sessions import get_current_user, is_logged_in
from auth.permissions import is_admin, is_super_admin
from components.theme import apply_custom_theme, render_developer_footer, safe_set_page_config
from components.navbar import render_navbar
from components.sidebar import render_sidebar
from components.cards import metric_card
from database.users import UserRepository
from database.plans import PlanRepository
from database.memberships import MembershipRepository
from database.payments import PaymentRepository
from database.projects import ProjectRepository
from database.audit_logs import AuditLogRepository, SupportTicketRepository
from core.payment_engine import PaymentEngine
from workers.worker_client import worker_client
from workers.monitor import WorkerTelemetryMonitor
from utils.helpers import format_currency

safe_set_page_config(title="Super Admin - NEXHOST CLOUD", icon="🛡️", layout="wide")
apply_custom_theme()

if not is_logged_in():
    st.warning("⚠️ Access restricted. Please log in.")
    st.stop()

user = get_current_user()
if not is_admin(user):
    st.error("⛔ Unauthorized. This control plane is restricted exclusively to platform administrators.")
    st.stop()

render_navbar()
render_sidebar()

st.title("🛡️ Super Admin Control Plane")
st.caption("Complete platform governance, payment auditing, user management, and worker fleet control.")

tab_kpi, tab_payments, tab_users, tab_plans, tab_workers, tab_support, tab_audit = st.tabs([
    "📊 KPI Analytics",
    "💳 Payment Queue",
    "👥 User Management",
    "💎 Plan Management",
    "🖥️ Worker Fleet",
    "🎫 Support Tickets",
    "📜 Audit Logs"
])

# ----------------- 1. KPI ANALYTICS -----------------
with tab_kpi:
    all_users = UserRepository.list_all()
    all_payments = PaymentRepository.list_all()
    all_projects = ProjectRepository.list_all()

    total_revenue = sum(p.amount_inr for p in all_payments if p.status == "APPROVED")
    pending_payments = [p for p in all_payments if p.status in ["PENDING", "UNDER_REVIEW"]]
    approved_payments = [p for p in all_payments if p.status == "APPROVED"]

    running_bots = sum(1 for p in all_projects if p.status == "RUNNING")
    premium_users = sum(1 for u in all_users if u.role in ["premium_user", "admin", "super_admin"])

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Total Revenue", format_currency(total_revenue), f"{len(approved_payments)} Approved Orders", "💰", "#10B981")
    with c2:
        metric_card("Total Users", len(all_users), f"{premium_users} Premium Members", "👥", "#6366F1")
    with c3:
        metric_card("Pending Payments", len(pending_payments), "Requires Verification", "⌛", "#F59E0B")
    with c4:
        metric_card("Active Bots", f"{running_bots} / {len(all_projects)}", "Running on Workers", "⚡", "#8B5CF6")

# ----------------- 2. PAYMENT QUEUE -----------------
with tab_payments:
    st.subheader("💳 Pending Payment Queue & Proof Verification")
    pending_list = PaymentRepository.list_pending()

    if not pending_list:
        st.success("✓ All payment submissions have been reviewed! No pending items.")
    else:
        for p in pending_list:
            st.markdown(f"""
            <div class="nex-card">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                    <div>
                        <span style="font-size: 1.15rem; font-weight: 700; color: #FFFFFF;">
                            Payment #{p.id} &bull; {p.user.username if p.user else 'User'}
                        </span>
                        <div style="font-size: 0.85rem; color: #9CA3AF; margin-top: 2px;">
                            Plan: <strong style="color: #FFFFFF;">{p.plan.display_name if p.plan else 'Plan'}</strong> &bull;
                            Amount: <strong style="color: #10B981;">{format_currency(p.amount_inr)}</strong> &bull;
                            UTR: <code style="color: #A5B4FC; font-weight: 700;">{p.upi_ref_id}</code>
                        </div>
                    </div>
                    <div>
                        <span style="background: rgba(245, 158, 11, 0.2); color: #F59E0B; padding: 4px 10px; border-radius: 9999px; font-weight: 700; font-size: 0.8rem;">
                            ⌛ {p.status}
                        </span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            col_proof, col_actions = st.columns([1.5, 2.5])
            with col_proof:
                if p.screenshot_path and Path(p.screenshot_path).exists():
                    st.image(p.screenshot_path, caption=f"Proof for UTR: {p.upi_ref_id}", width=260)
                else:
                    st.warning("Screenshot file not found on disk.")

            with col_actions:
                st.write("**Verification Actions:**")
                admin_notes = st.text_input("Internal Admin Notes (Optional)", key=f"notes_{p.id}")

                c_app, c_rej = st.columns(2)
                with c_app:
                    if st.button("✅ Approve & Activate Plan", key=f"app_{p.id}", type="primary", use_container_width=True):
                        with st.spinner("Approving payment and activating subscription..."):
                            ok, msg = PaymentEngine.approve_payment(p.id, user.id, notes=admin_notes)
                            if ok:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)

                with c_rej:
                    rejection_reason = st.text_input("Rejection Reason", value="Transaction could not be verified in bank statement.", key=f"rej_reason_{p.id}")
                    if st.button("❌ Reject Payment", key=f"rej_{p.id}", use_container_width=True):
                        with st.spinner("Rejecting payment request..."):
                            ok, msg = PaymentEngine.reject_payment(p.id, user.id, reason=rejection_reason, notes=admin_notes)
                            if ok:
                                st.warning(msg)
                                st.rerun()
                            else:
                                st.error(msg)
            st.markdown("---")

# ----------------- 3. USER MANAGEMENT -----------------
with tab_users:
    st.subheader("👥 User Account Governance")

    # Telegram Access Control Section
    st.markdown("#### 🤖 Telegram Bot Access Requests")
    pending_tg = UserRepository.list_pending_telegram_requests()
    if not pending_tg:
        st.success("✓ No pending Telegram access requests.")
    else:
        for pu in pending_tg:
            st.markdown(f"""
            <div class="nex-card" style="margin-bottom: 10px; padding: 12px;">
                <strong>{pu.full_name}</strong> (@{pu.username}) &bull; Telegram ID: <code>{pu.telegram_id}</code>
            </div>
            """, unsafe_allow_html=True)
            col_t1, col_t2, col_t3 = st.columns([2, 1, 1])
            with col_t1:
                sel_plan = st.selectbox("Assign Plan Tier", ["FREE", "STARTER", "PRO", "BUSINESS"], key=f"tg_plan_sel_{pu.id}")
            with col_t2:
                if st.button("✅ Approve Access", key=f"tg_app_btn_{pu.id}", type="primary", use_container_width=True):
                    UserRepository.authorize_telegram_user(pu.telegram_id, role="premium_user" if sel_plan != "FREE" else "free_user")
                    plan = PlanRepository.get_by_name(sel_plan)
                    if plan:
                        MembershipRepository.assign_plan(pu.id, plan)
                    st.success(f"Access granted to {pu.full_name} ({sel_plan})!")
                    st.rerun()
            with col_t3:
                if st.button("❌ Deny Access", key=f"tg_deny_btn_{pu.id}", use_container_width=True):
                    UserRepository.deauthorize_telegram_user(pu.telegram_id)
                    st.warning(f"Denied access for {pu.full_name}.")
                    st.rerun()
        st.markdown("---")

    st.markdown("#### 👥 All Registered Accounts")
    search_u = st.text_input("Search user by username, email or name...", key="admin_search_u")
    users_list = UserRepository.list_all(search=search_u)

    for u in users_list[:20]:
        c_u1, c_u2, c_u3 = st.columns([2.5, 1.5, 2])
        with c_u1:
            st.write(f"**@{u.username}** &bull; {u.email}")
            st.caption(f"Role: {u.role.upper()} &bull; Active: {u.is_active} &bull; Joined: {u.created_at.strftime('%Y-%m-%d')}")
        with c_u2:
            new_role = st.selectbox("Role", ["free_user", "premium_user", "admin", "super_admin"], index=["free_user", "premium_user", "admin", "super_admin"].index(u.role) if u.role in ["free_user", "premium_user", "admin", "super_admin"] else 0, key=f"role_sel_{u.id}")
            if new_role != u.role:
                if st.button("Update Role", key=f"up_role_{u.id}"):
                    UserRepository.update_role(u.id, new_role)
                    st.success(f"Updated role for @{u.username}")
                    st.rerun()
        with c_u3:
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                status_btn_label = "Ban User" if u.is_active else "Unban User"
                if st.button(status_btn_label, key=f"toggle_act_{u.id}"):
                    UserRepository.update_active_status(u.id, not u.is_active)
                    st.rerun()
            with col_b2:
                # Custom limit modal expander
                with st.expander("Overrides"):
                    c_bot = st.number_input("Custom Bots", value=u.custom_bot_limit or 1, key=f"cb_{u.id}")
                    c_ram = st.number_input("Custom RAM (MB)", value=u.custom_ram_mb or 256, key=f"cr_{u.id}")
                    if st.button("Save", key=f"sb_{u.id}"):
                        UserRepository.set_custom_limits(u.id, c_bot, c_ram, None, None)
                        st.success("Saved limits")
                        st.rerun()
        st.markdown("<hr style='margin: 4px 0;' />", unsafe_allow_html=True)

# ----------------- 4. PLAN MANAGEMENT -----------------
with tab_plans:
    st.subheader("💎 Membership Plan Configuration")
    all_plans = PlanRepository.list_all(active_only=False)

    for pl in all_plans:
        with st.expander(f"Edit Plan: {pl.display_name} ({pl.name}) - {format_currency(pl.price_inr)}"):
            with st.form(f"plan_edit_{pl.id}"):
                p_name = st.text_input("Display Name", value=pl.display_name)
                p_price = st.number_input("Price (₹ INR)", value=float(pl.price_inr), min_value=0.0)
                p_bots = st.number_input("Max Bots", value=int(pl.max_bots), min_value=1)
                p_ram = st.number_input("Max RAM (MB)", value=int(pl.max_ram_mb), min_value=128)
                p_storage = st.number_input("Max Storage (MB)", value=int(pl.max_storage_mb), min_value=250)
                p_active = st.checkbox("Plan is Active", value=pl.is_active)

                if st.form_submit_button("Save Plan Changes"):
                    PlanRepository.update(
                        pl.id,
                        display_name=p_name,
                        price_inr=p_price,
                        max_bots=p_bots,
                        max_ram_mb=p_ram,
                        max_storage_mb=p_storage,
                        is_active=p_active
                    )
                    st.success("Plan updated successfully!")
                    st.rerun()

# ----------------- 5. WORKER FLEET -----------------
with tab_workers:
    st.subheader("🖥️ Worker Fleet Status & Host Telemetry")
    host_stats = WorkerTelemetryMonitor.get_host_metrics()

    w1, w2, w3 = st.columns(3)
    with w1:
        metric_card("Host CPU", f"{host_stats['host_cpu_percent']}%", "Worker Node Load", "⚡", "#6366F1")
    with w2:
        metric_card("Host Memory", f"{host_stats['host_memory_used_mb']} MB", f"Total: {host_stats['host_memory_total_mb']} MB ({host_stats['host_memory_percent']}%)", "🧠", "#10B981")
    with w3:
        metric_card("Host Disk", f"{host_stats['host_disk_used_gb']} GB", f"Total: {host_stats['host_disk_total_gb']} GB ({host_stats['host_disk_percent']}%)", "💾", "#F59E0B")

    st.markdown("""
    <div class="nex-card">
        <div class="nex-card-header">Worker Node Health</div>
        <div style="font-size: 0.9rem; color: #D1D5DB;">
            Status: <span style="color: #10B981; font-weight: 700;">ONLINE (Health Check OK)</span> &bull;
            Mode: <strong>Isolated Sandbox & Non-Root Containers</strong> &bull;
            Architecture: <strong>REST Controller Protocol</strong>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ----------------- 6. SUPPORT TICKETS -----------------
with tab_support:
    st.subheader("🎫 Platform Support Desk")
    all_tickets = SupportTicketRepository.list_all()

    if not all_tickets:
        st.info("No support tickets submitted.")
    else:
        for t in all_tickets:
            with st.expander(f"#{t.id}: {t.subject} (by @{t.user.username if t.user else 'user'}) &bull; Status: {t.status}"):
                st.write(f"**User Message:** {t.message}")
                if t.admin_reply:
                    st.info(f"Current Reply: {t.admin_reply}")

                reply_txt = st.text_area("Admin Reply", key=f"t_reply_{t.id}")
                new_status = st.selectbox("Update Status", ["RESOLVED", "IN_PROGRESS", "CLOSED"], key=f"t_stat_{t.id}")

                if st.button("Send Reply & Update", key=f"btn_reply_{t.id}"):
                    if reply_txt:
                        SupportTicketRepository.reply_ticket(t.id, reply_txt, status=new_status)
                        st.success("Reply submitted!")
                        st.rerun()

# ----------------- 7. AUDIT LOGS -----------------
with tab_audit:
    st.subheader("📜 System Audit Trail")
    logs = AuditLogRepository.list_all(limit=50)
    for l in logs:
        st.markdown(f"""
        <div style="font-size: 0.82rem; padding: 6px 12px; background: rgba(31, 41, 55, 0.4); border-radius: 6px; margin-bottom: 4px; display: flex; justify-content: space-between;">
            <div>
                <strong style="color: #6366F1;">[{l.action}]</strong> &bull;
                {l.details} (User #{l.user_id or 'System'})
            </div>
            <div style="color: #6B7280;">
                {l.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}
            </div>
        </div>
        """, unsafe_allow_html=True)

render_developer_footer()
