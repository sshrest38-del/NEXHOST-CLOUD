"""
NEXHOST CLOUD - Official Platform Telegram Bot Service
Author: @Harsh_54x (https://t.me/Harsh_54x)
Tagline: Your Bots. Your Cloud.

Full Telegram Bot Control Plane with:
- Owner-Gated Access Control (Private Cloud Architecture)
- Professional English Access Restriction Screen with One-Click Access Request
- Real-Time Owner Approval / Denial with Instant User Notification
- Direct Bot Deployment via .ZIP Document Upload
- GitHub Deployment (Public & Private with PAT Token)
- Bot Lifecycle Management (Start, Stop, Restart, Live Logs, Env Vars, Delete)
- Optional MongoDB Event Logging
- Super Admin Owner Commands (/auth, /unauth, /users, /pending, /broadcast, /stats)
"""

import os
import io
import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from config import (
    PLATFORM_NAME,
    TAGLINE,
    DEVELOPER_HANDLE,
    DEVELOPER_TELEGRAM,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_OWNER_ID,
    ADMIN_UPI_ID,
    CURRENCY_SYMBOL,
)
from database.connection import init_db
from database.users import UserRepository
from database.projects import ProjectRepository
from database.plans import PlanRepository
from database.memberships import MembershipRepository
from database.mongo import MongoLogger
from core.membership_engine import MembershipEngine
from core.project_manager import ProjectManager
from core.process_manager import ProcessManager
from core.deployment_engine import DeploymentEngine
from services.storage_service import StorageService
from utils.helpers import get_status_badge, format_currency

# Setup logging
logging.basicConfig(
    format="[%(asctime)s] [%(levelname)s] [NEXHOST-BOT]: %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("NEXHOST-BOT")

# Ensure database is synchronized
init_db()


# =====================================================================
# ACCESS CONTROL & USER HELPERS
# =====================================================================

def is_owner(user_id: int) -> bool:
    """Check if the given Telegram user ID is the configured Platform Owner."""
    return bool(TELEGRAM_OWNER_ID and user_id == TELEGRAM_OWNER_ID)

def is_user_authorized(user_id: int) -> bool:
    """Verify if user has active authorization to use NEXHOST CLOUD."""
    if is_owner(user_id):
        return True
    return UserRepository.is_telegram_authorized(user_id)

def get_or_register_user(update: Update):
    """Link or auto-register Telegram user in the central database."""
    tg_u = update.effective_user
    user = UserRepository.get_or_create_by_telegram(
        telegram_id=tg_u.id,
        tg_username=tg_u.username or "",
        full_name=tg_u.full_name or tg_u.first_name
    )
    # If this user is configured as TELEGRAM_OWNER_ID, automatically grant super_admin
    if is_owner(tg_u.id) and (user.role != "super_admin" or not user.is_telegram_authorized):
        UserRepository.authorize_telegram_user(tg_u.id, role="super_admin")
        user = UserRepository.get_by_telegram_id(tg_u.id)
    return user

async def send_restricted_access_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Display a clean, professional English Access Restricted screen
    with One-Click Request Access and Contact buttons.
    """
    tg_user = update.effective_user
    user_id = tg_user.id
    name = tg_user.first_name or "Developer"

    # Register record if not exists
    db_user = get_or_register_user(update)
    has_requested = bool(db_user.telegram_access_requested)

    msg = (
        f"🔒 <b>ACCESS RESTRICTED — {PLATFORM_NAME}</b>\n"
        f"<i>{TAGLINE}</i>\n\n"
        f"Hello <b>{name}</b> (User ID: <code>{user_id}</code>),\n\n"
        f"<b>{PLATFORM_NAME}</b> is a private, high-performance cloud hosting platform "
        f"engineered for 24/7 Python Telegram Bot deployments.\n\n"
        f"⚠️ <b>Authorization Required:</b> Your account is currently not authorized to deploy "
        f"or manage bots on this server.\n\n"
        f"To gain access, click <b>Request Access</b> below. The Platform Owner "
        f"will review your request and activate your account.\n\n"
        f"👑 <b>Platform Owner:</b> {DEVELOPER_HANDLE}"
    )

    req_btn = (
        InlineKeyboardButton("⏳ Request Pending Review", callback_data="status_pending")
        if has_requested
        else InlineKeyboardButton("📩 Request Access", callback_data=f"req_access_{user_id}")
    )

    keyboard = [
        [req_btn],
        [
            InlineKeyboardButton(f"💬 Contact Owner ({DEVELOPER_HANDLE})", url=DEVELOPER_TELEGRAM),
            InlineKeyboardButton("🔄 Refresh Status", callback_data=f"check_auth_{user_id}")
        ]
    ]

    if update.callback_query:
        await update.callback_query.edit_message_text(
            msg, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
        )
    elif update.message:
        await update.message.reply_html(
            msg, reply_markup=InlineKeyboardMarkup(keyboard)
        )


# =====================================================================
# COMMAND HANDLERS
# =====================================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command with role-based routing (Owner / Authorized / Unauthorized)."""
    tg_user = update.effective_user
    user_id = tg_user.id

    # Log action in MongoDB if available
    MongoLogger.log_telegram_action(user_id, tg_user.username or "", "start")

    # 1. Check Authorization Gate
    if not is_user_authorized(user_id):
        await send_restricted_access_message(update, context)
        return

    user = get_or_register_user(update)
    limits = MembershipEngine.get_user_limits(user.id)

    # 2. Owner Dashboard
    if is_owner(user_id):
        pending_requests = UserRepository.list_pending_telegram_requests()
        running_bots = ProjectRepository.count_by_status("RUNNING")
        total_bots = ProjectRepository.count_all()
        total_users = UserRepository.count()

        owner_text = (
            f"👑 <b>NEXHOST CLOUD — OWNER COMMAND CENTER</b>\n"
            f"<i>{TAGLINE}</i>\n\n"
            f"Welcome back, <b>{tg_user.first_name}</b> (@{DEVELOPER_HANDLE.lstrip('@')})!\n"
            f"System Status: 🟢 <b>ONLINE</b> | Role: <b>SUPER ADMIN</b>\n\n"
            f"📊 <b>Platform Quick Stats:</b>\n"
            f"• 👥 Total Users: <b>{total_users}</b>\n"
            f"• 🤖 Total Bots: <b>{total_bots}</b> (🟢 {running_bots} Running)\n"
            f"• ⏳ Pending Access Requests: <b>{len(pending_requests)}</b>\n\n"
            f"Select an action below or deploy bots instantly by sending a .ZIP file:"
        )

        owner_keyboard = [
            [
                InlineKeyboardButton("📁 My Bots", callback_data="cmd_mybots"),
                InlineKeyboardButton("🚀 Deploy Info", callback_data="cmd_deploy_help"),
            ],
            [
                InlineKeyboardButton(f"⏳ Pending Requests ({len(pending_requests)})", callback_data="owner_view_pending"),
                InlineKeyboardButton("👥 Authorized Users", callback_data="owner_view_users"),
            ],
            [
                InlineKeyboardButton("📊 System Stats", callback_data="owner_view_stats"),
                InlineKeyboardButton("💎 Plan Limits", callback_data="cmd_plan"),
            ]
        ]

        if update.callback_query:
            await update.callback_query.edit_message_text(
                owner_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(owner_keyboard)
            )
        else:
            await update.message.reply_html(
                owner_text, reply_markup=InlineKeyboardMarkup(owner_keyboard)
            )
        return

    # 3. Standard Authorized User Dashboard
    welcome_text = (
        f"⚡ <b>Welcome to {PLATFORM_NAME}!</b>\n"
        f"<i>{TAGLINE}</i>\n\n"
        f"👋 Hello, <b>{tg_user.first_name}</b>!\n"
        f"Your account is authorized on the <b>{limits['plan_display']}</b> plan.\n\n"
        f"🤖 <b>Bot Slots:</b> {limits['current_bots']} / {limits['max_bots']} Used\n"
        f"⚡ <b>RAM Allocation:</b> {limits['max_ram_mb']} MB\n"
        f"💾 <b>Storage:</b> {limits['used_storage_mb']:.1f} / {limits['max_storage_mb']} MB\n\n"
        f"<b>🚀 How to Deploy Your Bot:</b>\n"
        f"• 📤 <b>Send any .ZIP file</b> directly in this chat to deploy!\n"
        f"• 🐙 Or use <code>/git &lt;repo_url&gt;</code> to deploy from GitHub."
    )

    keyboard = [
        [
            InlineKeyboardButton("📁 My Bots", callback_data="cmd_mybots"),
            InlineKeyboardButton("💎 Plans & Quota", callback_data="cmd_plan")
        ],
        [
            InlineKeyboardButton("🚀 Deploy Instructions", callback_data="cmd_deploy_help"),
            InlineKeyboardButton(f"💬 Contact Owner", url=DEVELOPER_TELEGRAM)
        ]
    ]

    if update.callback_query:
        await update.callback_query.edit_message_text(
            welcome_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_html(
            welcome_text, reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def plan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /plan command to view quotas and upgrade info."""
    user_id = update.effective_user.id
    if not is_user_authorized(user_id):
        await send_restricted_access_message(update, context)
        return

    user = get_or_register_user(update)
    limits = MembershipEngine.get_user_limits(user.id)
    exp_str = limits["expires_at"].strftime("%Y-%m-%d") if limits["expires_at"] else "Permanent"

    msg = (
        f"💎 <b>Current Subscription:</b> {limits['plan_display']}\n"
        f"📅 <b>Expires:</b> {exp_str}\n\n"
        f"🤖 <b>Active Bots:</b> {limits['current_bots']} / {limits['max_bots']}\n"
        f"⚡ <b>RAM:</b> {limits['max_ram_mb']} MB\n"
        f"💾 <b>Storage:</b> {limits['used_storage_mb']:.1f} MB / {limits['max_storage_mb']} MB\n\n"
        f"<b>Available Upgrades:</b>\n"
        f"• <b>FREE:</b> ₹0 (1 Bot, 256MB RAM)\n"
        f"• <b>STARTER:</b> ₹49/mo (3 Bots, 512MB RAM)\n"
        f"• <b>PRO:</b> ₹99/mo (10 Bots, 1024MB RAM)\n"
        f"• <b>BUSINESS:</b> ₹199/mo (25 Bots, 2048MB RAM)\n"
        f"• <b>LIFETIME:</b> ₹999 One-time (50 Bots, 4096MB RAM)\n\n"
        f"💳 Pay via UPI ID: <code>{ADMIN_UPI_ID}</code>\n"
        f"Then submit verification or contact {DEVELOPER_HANDLE}."
    )

    keyboard = [
        [InlineKeyboardButton("📁 My Bots", callback_data="cmd_mybots")],
        [InlineKeyboardButton(f"💬 Contact Owner ({DEVELOPER_HANDLE})", url=DEVELOPER_TELEGRAM)]
    ]

    if update.callback_query:
        await update.callback_query.edit_message_text(msg, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_html(msg, reply_markup=InlineKeyboardMarkup(keyboard))

async def mybots_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /mybots command to view and control user's deployed bots."""
    user_id = update.effective_user.id
    if not is_user_authorized(user_id):
        await send_restricted_access_message(update, context)
        return

    user = get_or_register_user(update)
    projects = ProjectRepository.list_by_user(user.id)

    if not projects:
        text = (
            "📁 <b>You have not deployed any bots yet!</b>\n\n"
            "To deploy, simply <b>send your bot's .ZIP file</b> here in chat, "
            "or send <code>/git &lt;repo_url&gt;</code>."
        )
        keyboard = [[InlineKeyboardButton("🚀 Deploy Guide", callback_data="cmd_deploy_help")]]
        if update.callback_query:
            await update.callback_query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await update.message.reply_html(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    for proj in projects:
        status_icon = "🟢" if proj.status == "RUNNING" else ("🔴" if proj.status == "FAILED" else "🟡")
        p_text = (
            f"{status_icon} <b>Bot:</b> {proj.name} (<code>#{proj.id}</code>)\n"
            f"<b>Status:</b> {proj.status}\n"
            f"<b>Runtime:</b> {proj.runtime_version}\n"
            f"<b>Command:</b> <code>{proj.startup_command}</code>\n"
            f"<b>Restarts:</b> {proj.restart_count}"
        )

        btn_start_stop = (
            InlineKeyboardButton("🛑 Stop", callback_data=f"bot_stop_{proj.id}")
            if proj.status == "RUNNING"
            else InlineKeyboardButton("▶️ Start", callback_data=f"bot_start_{proj.id}")
        )
        keyboard = [
            [
                btn_start_stop,
                InlineKeyboardButton("🔄 Restart", callback_data=f"bot_restart_{proj.id}"),
                InlineKeyboardButton("📋 Logs", callback_data=f"bot_logs_{proj.id}")
            ],
            [
                InlineKeyboardButton("⚙️ Env Vars", callback_data=f"bot_env_{proj.id}"),
                InlineKeyboardButton("🗑️ Delete", callback_data=f"bot_del_{proj.id}")
            ]
        ]

        if update.message:
            await update.message.reply_html(p_text, reply_markup=InlineKeyboardMarkup(keyboard))
        elif update.callback_query:
            await update.callback_query.message.reply_html(p_text, reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_zip_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle direct .ZIP file upload from Telegram user."""
    doc = update.message.document
    if not doc.file_name.lower().endswith(".zip"):
        return

    user_id = update.effective_user.id
    if not is_user_authorized(user_id):
        await send_restricted_access_message(update, context)
        return

    user = get_or_register_user(update)
    can_create, reason = MembershipEngine.can_create_bot(user.id)
    if not can_create:
        await update.message.reply_html(f"❌ <b>Quota Exceeded:</b> {reason}\nUse /plan to upgrade.")
        return

    status_msg = await update.message.reply_html("⏳ <b>Downloading project ZIP archive...</b>")

    try:
        tg_file = await context.bot.get_file(doc.file_id)
        file_bytes = await tg_file.download_as_bytearray()
        buf = io.BytesIO(file_bytes)

        bot_name = Path(doc.file_name).stem.replace("_", " ").replace("-", " ").title()

        await status_msg.edit_text("⚙️ <b>Extracting files and detecting dependencies...</b>", parse_mode="HTML")

        ok, msg, project = ProjectManager.create_project_from_zip(
            user_id=user.id,
            name=bot_name,
            zip_file=buf,
            runtime_version="python:3.11"
        )

        if not ok:
            await status_msg.edit_text(f"❌ <b>Deployment Error:</b> {msg}", parse_mode="HTML")
            return

        await status_msg.edit_text("🚀 <b>Launching bot container on worker node...</b>", parse_mode="HTML")

        d_ok, d_msg, _ = DeploymentEngine.deploy_project(user.id, project.id, install_deps=True)

        keyboard = [
            [
                InlineKeyboardButton("🛑 Stop", callback_data=f"bot_stop_{project.id}"),
                InlineKeyboardButton("🔄 Restart", callback_data=f"bot_restart_{project.id}"),
                InlineKeyboardButton("📋 View Logs", callback_data=f"bot_logs_{project.id}")
            ]
        ]

        await status_msg.edit_text(
            f"🎉 <b>Bot '{project.name}' Deployed Successfully!</b>\n\n"
            f"<b>Status:</b> RUNNING 🟢\n"
            f"<b>Project ID:</b> <code>#{project.id}</code>\n"
            f"<b>Startup Command:</b> <code>{project.startup_command}</code>\n"
            f"<i>{d_msg}</i>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        # Log deployment
        MongoLogger.log_bot_deployment(user.id, project.id, project.name, "RUNNING", "telegram_zip")

    except Exception as e:
        logger.error(f"Telegram ZIP deploy failure: {e}")
        await status_msg.edit_text(f"❌ <b>Deployment failed:</b> {str(e)}", parse_mode="HTML")

async def git_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /git <repo_url> [token] [branch]
    Supports both Public and Private GitHub repositories!
    """
    user_id = update.effective_user.id
    if not is_user_authorized(user_id):
        await send_restricted_access_message(update, context)
        return

    if not context.args:
        help_msg = (
            "🐙 <b>GitHub Deployment (Public & Private):</b>\n\n"
            "• <b>Public Repo:</b>\n"
            "<code>/git https://github.com/owner/repo</code>\n\n"
            "• <b>Private Repo (using GitHub PAT Token):</b>\n"
            "<code>/git https://github.com/owner/private-repo ghp_YourTokenHere</code>\n\n"
            "• <b>Custom Branch:</b>\n"
            "<code>/git https://github.com/owner/repo none dev</code>\n"
            "<i>(Pass token as 'none' for public repo on custom branch)</i>"
        )
        await update.message.reply_html(help_msg)
        return

    repo_url = context.args[0].strip()
    token = None
    branch = "main"

    if len(context.args) >= 2:
        arg2 = context.args[1].strip()
        if arg2.lower() != "none":
            token = arg2

    if len(context.args) >= 3:
        branch = context.args[2].strip()

    user = get_or_register_user(update)
    can_create, reason = MembershipEngine.can_create_bot(user.id)
    if not can_create:
        await update.message.reply_html(f"❌ <b>Quota Exceeded:</b> {reason}\nUse /plan to upgrade.")
        return

    repo_type = "🔒 Private" if token else "🌍 Public"
    status_msg = await update.message.reply_html(f"⏳ <b>Cloning {repo_type} repository ({branch})...</b>")
    bot_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "").replace("-", " ").title()

    try:
        ok, msg, project = ProjectManager.create_project_from_github(
            user_id=user.id,
            name=bot_name,
            repo_url=repo_url,
            branch=branch,
            token=token
        )
        if not ok:
            await status_msg.edit_text(f"❌ <b>Git Clone Failed:</b> {msg}\nCheck URL or Token.", parse_mode="HTML")
            return

        await status_msg.edit_text("🚀 <b>Installing requirements and launching bot on worker...</b>", parse_mode="HTML")
        d_ok, d_msg, _ = DeploymentEngine.deploy_project(user.id, project.id, install_deps=True)

        keyboard = [
            [
                InlineKeyboardButton("🛑 Stop", callback_data=f"bot_stop_{project.id}"),
                InlineKeyboardButton("🔄 Restart", callback_data=f"bot_restart_{project.id}"),
                InlineKeyboardButton("📋 View Logs", callback_data=f"bot_logs_{project.id}")
            ]
        ]

        await status_msg.edit_text(
            f"🎉 <b>{repo_type} Bot '{project.name}' Deployed!</b>\n\n"
            f"<b>Status:</b> RUNNING 🟢\n"
            f"<b>Project ID:</b> <code>#{project.id}</code>\n"
            f"<b>Branch:</b> <code>{branch}</code>\n"
            f"<i>{d_msg}</i>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        MongoLogger.log_bot_deployment(user.id, project.id, project.name, "RUNNING", "telegram_git")

    except Exception as e:
        await status_msg.edit_text(f"❌ <b>Error:</b> {str(e)}", parse_mode="HTML")

async def setenv_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /setenv <project_id> <KEY> <VALUE>."""
    user_id = update.effective_user.id
    if not is_user_authorized(user_id):
        await send_restricted_access_message(update, context)
        return

    if len(context.args) < 3:
        await update.message.reply_html(
            "⚠️ <b>Usage:</b> <code>/setenv &lt;project_id&gt; &lt;KEY&gt; &lt;VALUE&gt;</code>\n"
            "<i>Example:</i> <code>/setenv 1 BOT_TOKEN 123456:ABC...</code>"
        )
        return

    user = get_or_register_user(update)
    try:
        proj_id = int(context.args[0])
        key = context.args[1].strip().upper()
        val = " ".join(context.args[2:]).strip()

        proj = ProjectRepository.get_user_project(user.id, proj_id)
        if not proj:
            await update.message.reply_html("❌ <b>Project not found or unauthorized.</b>")
            return

        current_env = ProjectRepository.get_env_vars(proj_id)
        current_env[key] = val
        ProjectRepository.update_env_vars(proj_id, current_env)

        await update.message.reply_html(
            f"✅ <b>Environment variable set:</b> <code>{key}=********</code>\n"
            f"Use <code>/restart {proj_id}</code> to apply changes."
        )
    except Exception as e:
        await update.message.reply_html(f"❌ <b>Error:</b> {str(e)}")


# =====================================================================
# SUPER ADMIN / OWNER COMMANDS
# =====================================================================

async def auth_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Owner command: /auth <user_id> [plan_name] (e.g. /auth 123456789 pro)."""
    caller_id = update.effective_user.id
    if not is_owner(caller_id):
        await update.message.reply_html("⛔ <b>Unauthorized:</b> This command is restricted to the Platform Owner.")
        return

    if not context.args:
        await update.message.reply_html(
            "⚠️ <b>Usage:</b> <code>/auth &lt;telegram_user_id&gt; [free|starter|pro|business|lifetime]</code>\n"
            "<i>Example:</i> <code>/auth 123456789 pro</code>"
        )
        return

    try:
        target_tg_id = int(context.args[0].strip())
        plan_name = context.args[1].strip().upper() if len(context.args) >= 2 else "FREE"
    except ValueError:
        await update.message.reply_html("❌ Invalid Telegram User ID. Must be numeric.")
        return

    target_user = UserRepository.get_by_telegram_id(target_tg_id)
    if not target_user:
        target_user = UserRepository.get_or_create_by_telegram(target_tg_id, "", f"User_{target_tg_id}")

    # Authorize user
    UserRepository.authorize_telegram_user(target_tg_id, role="premium_user" if plan_name != "FREE" else "free_user")
    plan = PlanRepository.get_by_name(plan_name) or PlanRepository.get_by_name("FREE")
    if plan:
        MembershipRepository.assign_plan(target_user.id, plan)

    await update.message.reply_html(
        f"✅ <b>User Authorized Successfully!</b>\n\n"
        f"👤 <b>User:</b> {target_user.full_name} (<code>{target_tg_id}</code>)\n"
        f"💎 <b>Assigned Plan:</b> {plan.name if plan else 'FREE'}\n"
        f"🤖 <b>Bot Limit:</b> {plan.max_bots if plan else 1}"
    )

    # Notify target user via bot
    try:
        await context.bot.send_message(
            chat_id=target_tg_id,
            text=(
                f"🎉 <b>ACCESS GRANTED — {PLATFORM_NAME}</b>\n\n"
                f"Hello! The Platform Owner has authorized your account on the <b>{plan.name if plan else 'FREE'}</b> plan.\n\n"
                f"You can now deploy bots via ZIP upload or GitHub!\n"
                f"Click /start to open your dashboard."
            ),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.warning(f"Could not deliver notification to authorized user {target_tg_id}: {e}")

async def unauth_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Owner command: /unauth <user_id> to revoke access."""
    caller_id = update.effective_user.id
    if not is_owner(caller_id):
        await update.message.reply_html("⛔ <b>Unauthorized:</b> Restricted to Platform Owner.")
        return

    if not context.args:
        await update.message.reply_html("⚠️ <b>Usage:</b> <code>/unauth &lt;telegram_user_id&gt;</code>")
        return

    try:
        target_tg_id = int(context.args[0].strip())
    except ValueError:
        await update.message.reply_html("❌ Invalid Telegram User ID.")
        return

    UserRepository.deauthorize_telegram_user(target_tg_id)
    await update.message.reply_html(f"🔒 <b>User <code>{target_tg_id}</code> access has been REVOKED.</b>")

    try:
        await context.bot.send_message(
            chat_id=target_tg_id,
            text=f"🔒 <b>Access Revoked:</b> Your access to {PLATFORM_NAME} has been suspended by the Owner.",
            parse_mode="HTML"
        )
    except Exception:
        pass

async def authusers_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Owner command: /authusers or /users to view all authorized users."""
    caller_id = update.effective_user.id
    if not is_owner(caller_id):
        await update.message.reply_html("⛔ <b>Unauthorized:</b> Restricted to Platform Owner.")
        return

    users = UserRepository.list_authorized_telegram_users()
    if not users:
        await update.message.reply_html("ℹ️ <b>No authorized Telegram users found.</b>")
        return

    msg = f"👥 <b>AUTHORIZED TELEGRAM USERS ({len(users)}):</b>\n\n"
    for u in users:
        bots_count = ProjectRepository.count_by_user(u.id)
        msg += f"• <b>{u.full_name}</b> (<code>{u.telegram_id}</code>) | Role: <code>{u.role}</code> | Bots: {bots_count}\n"

    await update.message.reply_html(msg)

async def pending_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Owner command: /pending to view and approve pending access requests."""
    caller_id = update.effective_user.id
    if not is_owner(caller_id):
        await update.message.reply_html("⛔ <b>Unauthorized:</b> Restricted to Platform Owner.")
        return

    pending = UserRepository.list_pending_telegram_requests()
    if not pending:
        await update.message.reply_html("✅ <b>No pending access requests!</b> All requests are reviewed.")
        return

    for u in pending:
        card = (
            f"⏳ <b>PENDING ACCESS REQUEST</b>\n\n"
            f"👤 <b>Name:</b> {u.full_name}\n"
            f"🔗 <b>Username:</b> @{u.username}\n"
            f"🆔 <b>Telegram ID:</b> <code>{u.telegram_id}</code>\n"
            f"📅 <b>Created:</b> {u.created_at.strftime('%Y-%m-%d %H:%M UTC')}"
        )
        keyboard = [
            [
                InlineKeyboardButton("✅ Approve (Free)", callback_data=f"owner_grant_free_{u.telegram_id}"),
                InlineKeyboardButton("⚡ Approve (Starter)", callback_data=f"owner_grant_starter_{u.telegram_id}"),
            ],
            [
                InlineKeyboardButton("💎 Approve (Pro)", callback_data=f"owner_grant_pro_{u.telegram_id}"),
                InlineKeyboardButton("❌ Deny", callback_data=f"owner_deny_{u.telegram_id}")
            ]
        ]
        await update.message.reply_html(card, reply_markup=InlineKeyboardMarkup(keyboard))

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Owner command: /stats to view cloud metrics."""
    caller_id = update.effective_user.id
    if not is_owner(caller_id):
        await update.message.reply_html("⛔ <b>Unauthorized:</b> Restricted to Platform Owner.")
        return

    total_users = UserRepository.count()
    auth_users = len(UserRepository.list_authorized_telegram_users())
    pending_users = len(UserRepository.list_pending_telegram_requests())
    total_bots = ProjectRepository.count_all()
    running_bots = ProjectRepository.count_by_status("RUNNING")
    stopped_bots = ProjectRepository.count_by_status("STOPPED")
    mongo_status = "🟢 Connected" if MongoLogger.is_available() else "⚪ Not Configured (PostgreSQL active)"

    msg = (
        f"📊 <b>{PLATFORM_NAME} — SYSTEM HEALTH & STATS</b>\n\n"
        f"👥 <b>Users:</b>\n"
        f"• Total Registered: {total_users}\n"
        f"• Telegram Authorized: {auth_users}\n"
        f"• Pending Access Requests: {pending_users}\n\n"
        f"🤖 <b>Bot Clusters:</b>\n"
        f"• Total Deployed: {total_bots}\n"
        f"• 🟢 Running: {running_bots}\n"
        f"• 🛑 Stopped: {stopped_bots}\n\n"
        f"🗄️ <b>Storage & Engines:</b>\n"
        f"• Database: 🟢 PostgreSQL (Neon Cloud Active)\n"
        f"• MongoDB: {mongo_status}\n"
        f"• Worker Engine: Active Process Supervisor"
    )
    await update.message.reply_html(msg)

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Owner command: /broadcast <message> to announce to all authorized users."""
    caller_id = update.effective_user.id
    if not is_owner(caller_id):
        await update.message.reply_html("⛔ <b>Unauthorized:</b> Restricted to Platform Owner.")
        return

    if not context.args:
        await update.message.reply_html("⚠️ <b>Usage:</b> <code>/broadcast &lt;announcement text&gt;</code>")
        return

    text = " ".join(context.args).strip()
    users = UserRepository.list_authorized_telegram_users()
    count = 0

    status_msg = await update.message.reply_html(f"📢 <b>Broadcasting to {len(users)} users...</b>")

    broadcast_content = (
        f"📢 <b>ANNOUNCEMENT — {PLATFORM_NAME}</b>\n\n"
        f"{text}\n\n"
        f"👑 <i>From: Platform Owner ({DEVELOPER_HANDLE})</i>"
    )

    for u in users:
        if u.telegram_id:
            try:
                await context.bot.send_message(
                    chat_id=u.telegram_id,
                    text=broadcast_content,
                    parse_mode="HTML"
                )
                count += 1
                await asyncio.sleep(0.05)  # Telegram rate limit compliance
            except Exception:
                pass

    await status_msg.edit_text(f"✅ <b>Broadcast complete! Delivered to {count} users.</b>", parse_mode="HTML")


# =====================================================================
# CALLBACK ROUTER & OWNER ACTIONS
# =====================================================================

async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Route all inline keyboard callbacks for both users and owner."""
    query = update.callback_query
    await query.answer()
    data = query.data
    tg_user = update.effective_user
    user_id = tg_user.id

    # -------------------------------------------------------------
    # 1. USER ACCESS REQUEST FLOW
    # -------------------------------------------------------------
    if data.startswith("req_access_"):
        target_tg_id = int(data.split("_")[-1])
        # Mark in DB
        UserRepository.set_telegram_access_requested(target_tg_id, True)

        # Notify User
        confirm_text = (
            f"✅ <b>Access Request Submitted!</b>\n\n"
            f"Your request has been forwarded directly to the Platform Owner ({DEVELOPER_HANDLE}).\n"
            f"You will receive an automatic notification here the moment your access is approved.\n\n"
            f"For express verification, you may also message the Owner directly."
        )
        confirm_kb = [
            [InlineKeyboardButton(f"💬 Message Owner ({DEVELOPER_HANDLE})", url=DEVELOPER_TELEGRAM)],
            [InlineKeyboardButton("🔄 Refresh Status", callback_data=f"check_auth_{target_tg_id}")]
        ]
        await query.edit_message_text(confirm_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(confirm_kb))

        # Forward request to OWNER
        if TELEGRAM_OWNER_ID and TELEGRAM_OWNER_ID > 0:
            owner_card = (
                f"🚨 <b>NEW USER ACCESS REQUEST</b>\n\n"
                f"👤 <b>Name:</b> {tg_user.full_name}\n"
                f"🔗 <b>Username:</b> @{tg_user.username if tg_user.username else 'None'}\n"
                f"🆔 <b>User ID:</b> <code>{target_tg_id}</code>\n"
                f"📅 <b>Time:</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
                f"Choose an action below to grant or decline access:"
            )
            owner_kb = [
                [
                    InlineKeyboardButton("✅ Free (1 Bot)", callback_data=f"owner_grant_free_{target_tg_id}"),
                    InlineKeyboardButton("⚡ Starter (3 Bots)", callback_data=f"owner_grant_starter_{target_tg_id}"),
                ],
                [
                    InlineKeyboardButton("💎 Pro (10 Bots)", callback_data=f"owner_grant_pro_{target_tg_id}"),
                    InlineKeyboardButton("❌ Deny", callback_data=f"owner_deny_{target_tg_id}")
                ]
            ]
            try:
                await context.bot.send_message(
                    chat_id=TELEGRAM_OWNER_ID,
                    text=owner_card,
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup(owner_kb)
                )
            except Exception as e:
                logger.error(f"Failed to forward access request to OWNER ({TELEGRAM_OWNER_ID}): {e}")

        MongoLogger.log_telegram_action(target_tg_id, tg_user.username or "", "request_access_submitted")
        return

    elif data.startswith("check_auth_"):
        target_tg_id = int(data.split("_")[-1])
        if is_user_authorized(target_tg_id):
            await query.answer("🎉 Congratulations! Your access has been approved!", show_alert=True)
            await start_command(update, context)
        else:
            await query.answer("⏳ Your access request is still under review by the Owner.", show_alert=True)
        return

    elif data == "status_pending":
        await query.answer("⏳ Your request is currently pending review with the Owner. Please wait.", show_alert=True)
        return

    # -------------------------------------------------------------
    # 2. OWNER ACTIONS: APPROVE / DENY
    # -------------------------------------------------------------
    if data.startswith("owner_grant_") or data.startswith("owner_deny_"):
        if not is_owner(user_id):
            await query.answer("⛔ Only the Platform Owner can perform this action.", show_alert=True)
            return

        parts = data.split("_")
        action = parts[1]  # "grant" or "deny"

        if action == "grant":
            plan_name = parts[2].upper()  # "FREE", "STARTER", "PRO"
            target_tg_id = int(parts[3])

            target_user = UserRepository.get_by_telegram_id(target_tg_id)
            if not target_user:
                target_user = UserRepository.get_or_create_by_telegram(target_tg_id, "", f"User_{target_tg_id}")

            # Authorize & assign plan
            UserRepository.authorize_telegram_user(target_tg_id, role="premium_user" if plan_name != "FREE" else "free_user")
            plan = PlanRepository.get_by_name(plan_name) or PlanRepository.get_by_name("FREE")
            if plan:
                MembershipRepository.assign_plan(target_user.id, plan)

            # Update owner message
            await query.edit_message_text(
                f"✅ <b>USER AUTHORIZED SUCCESSFULLY</b>\n\n"
                f"👤 <b>User:</b> {target_user.full_name} (<code>{target_tg_id}</code>)\n"
                f"💎 <b>Plan Granted:</b> {plan_name}\n"
                f"🤖 <b>Bot Capacity:</b> {plan.max_bots if plan else 1} bots\n"
                f"📅 <b>Timestamp:</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
                parse_mode="HTML"
            )

            # Notify the user
            try:
                user_msg = (
                    f"🎉 <b>ACCESS APPROVED — {PLATFORM_NAME}</b>\n\n"
                    f"Hello <b>{target_user.full_name}</b>, great news!\n"
                    f"The Platform Owner has authorized your account on the <b>{plan_name}</b> tier.\n\n"
                    f"🤖 <b>Bot Slots:</b> {plan.max_bots if plan else 1}\n"
                    f"⚡ <b>RAM:</b> {plan.max_ram_mb if plan else 256} MB\n\n"
                    f"🚀 Click /start to open your dashboard and deploy your bots!"
                )
                start_kb = [[InlineKeyboardButton("🚀 Open Dashboard", callback_data="start_fresh")]]
                await context.bot.send_message(
                    chat_id=target_tg_id,
                    text=user_msg,
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup(start_kb)
                )
            except Exception as e:
                logger.warning(f"Could not deliver approval notification to user {target_tg_id}: {e}")

            MongoLogger.log_telegram_action(user_id, tg_user.username or "", "owner_approved_user", {"target_id": target_tg_id, "plan": plan_name})
            return

        elif action == "deny":
            target_tg_id = int(parts[2])
            UserRepository.deauthorize_telegram_user(target_tg_id)

            await query.edit_message_text(
                f"❌ <b>ACCESS REQUEST DECLINED</b>\n\n"
                f"User ID: <code>{target_tg_id}</code> was declined access.\n"
                f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
                parse_mode="HTML"
            )

            try:
                await context.bot.send_message(
                    chat_id=target_tg_id,
                    text=(
                        f"❌ <b>Access Request Declined</b>\n\n"
                        f"Your request to access {PLATFORM_NAME} was declined by the Platform Owner.\n"
                        f"For questions or business inquiries, contact {DEVELOPER_HANDLE}."
                    ),
                    parse_mode="HTML"
                )
            except Exception:
                pass
            return

    # -------------------------------------------------------------
    # 3. OWNER NAVIGATION CALLBACKS
    # -------------------------------------------------------------
    if data == "owner_view_pending":
        await pending_command(update, context)
        return
    elif data == "owner_view_users":
        await authusers_command(update, context)
        return
    elif data == "owner_view_stats":
        await stats_command(update, context)
        return

    # -------------------------------------------------------------
    # 4. GENERAL AUTHORIZED ACTIONS
    # -------------------------------------------------------------
    if not is_user_authorized(user_id):
        await send_restricted_access_message(update, context)
        return

    user = get_or_register_user(update)

    if data in ["cmd_mybots", "start_fresh"]:
        await mybots_command(update, context)
    elif data == "cmd_plan":
        await plan_command(update, context)
    elif data == "cmd_deploy_help":
        help_text = (
            "🚀 <b>How to Deploy Your Telegram Bot on NEXHOST CLOUD:</b>\n\n"
            "1. <b>Direct ZIP Upload:</b>\n"
            "   • Zip your project folder containing <code>requirements.txt</code> and your main bot file (e.g. <code>bot.py</code> or <code>main.py</code>).\n"
            "   • Send the .zip file directly into this chat!\n\n"
            "2. <b>GitHub Deployment:</b>\n"
            "   • <b>Public:</b> <code>/git https://github.com/owner/bot-repo</code>\n"
            "   • <b>Private:</b> <code>/git https://github.com/owner/bot-repo &lt;GITHUB_TOKEN&gt;</code>\n\n"
            "3. <b>Configure Bot Credentials:</b>\n"
            "   • Set secrets: <code>/setenv &lt;project_id&gt; BOT_TOKEN 123456:ABC...</code>\n"
            "   • Restart bot: <code>/mybots</code> -> Click <b>Restart</b>"
        )
        keyboard = [[InlineKeyboardButton("📁 My Bots", callback_data="cmd_mybots")]]
        await query.message.reply_html(help_text, reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("bot_start_"):
        pid = int(data.split("_")[-1])
        ok, msg = ProcessManager.start_bot(user.id, pid)
        await query.message.reply_html(f"{'✅' if ok else '❌'} {msg}")

    elif data.startswith("bot_stop_"):
        pid = int(data.split("_")[-1])
        ok, msg = ProcessManager.stop_bot(user.id, pid)
        await query.message.reply_html(f"🛑 {msg}")

    elif data.startswith("bot_restart_"):
        pid = int(data.split("_")[-1])
        ok, msg = ProcessManager.restart_bot(user.id, pid)
        await query.message.reply_html(f"🔄 {msg}")

    elif data.startswith("bot_logs_"):
        pid = int(data.split("_")[-1])
        logs = ProcessManager.get_live_logs(user.id, pid, limit=25)
        snippet = logs[-3500:] if logs else "No logs recorded yet."
        await query.message.reply_html(f"📋 <b>Console Logs (Project #{pid}):</b>\n<pre>{snippet}</pre>")

    elif data.startswith("bot_del_"):
        pid = int(data.split("_")[-1])
        ProcessManager.stop_bot(user.id, pid)
        ok, msg = ProjectManager.delete_project(user.id, pid)
        await query.message.reply_html(f"🗑️ {msg}")

    elif data.startswith("bot_env_"):
        pid = int(data.split("_")[-1])
        await query.message.reply_html(
            f"⚙️ <b>Set Environment Variable for Bot #{pid}:</b>\n"
            f"Send: <code>/setenv {pid} KEY VALUE</code>\n"
            f"<i>Example:</i> <code>/setenv {pid} BOT_TOKEN 123456:ABC-DEF</code>"
        )


# =====================================================================
# MAIN ENTRYPOINT
# =====================================================================

def main():
    """Start Telegram Bot application with polling."""
    if not TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN is not set in config or .env. Telegram Bot service will not start.")
        print("[-] Please set TELEGRAM_BOT_TOKEN in .env or config to run the Telegram Bot.")
        return

    logger.info("Starting NEXHOST CLOUD Telegram Bot application...")
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # User & General Handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("mybots", mybots_command))
    app.add_handler(CommandHandler("plan", plan_command))
    app.add_handler(CommandHandler("git", git_command))
    app.add_handler(CommandHandler("setenv", setenv_command))

    # Owner Admin Handlers
    app.add_handler(CommandHandler("auth", auth_command))
    app.add_handler(CommandHandler("unauth", unauth_command))
    app.add_handler(CommandHandler("users", authusers_command))
    app.add_handler(CommandHandler("authusers", authusers_command))
    app.add_handler(CommandHandler("pending", pending_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("broadcast", broadcast_command))

    # Document & Callback Router
    app.add_handler(MessageHandler(filters.Document.ALL, handle_zip_document))
    app.add_handler(CallbackQueryHandler(callback_router))

    print(f"[+] NEXHOST CLOUD Telegram Bot is active and listening for user interactions!")
    if TELEGRAM_OWNER_ID:
        print(f"[+] Master Owner Telegram ID configured: {TELEGRAM_OWNER_ID}")
    else:
        print(f"[!] Warning: TELEGRAM_OWNER_ID is not configured. Set it in .env to enable one-click access approval notifications.")

    app.run_polling()

if __name__ == "__main__":
    main()
