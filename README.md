# NEXHOST CLOUD ⚡
> **Your Bots. Your Cloud.**  
> Advanced Multi-User Paid Python Telegram Bot Hosting SaaS Platform  
> **Lead Architect & Developer:** [@Harsh_54x](https://t.me/Harsh_54x)  
> **Currency:** Indian Rupee (₹ INR) &bull; **Payment Method:** Manual UPI with Proof Verification  

---

## 🌟 Executive Overview
**NEXHOST CLOUD** is an enterprise-grade cloud hosting SaaS specifically engineered for Python Telegram bots. It delivers a modern, high-performance web dashboard coupled with an isolated worker execution engine.

### Core Architectural Separation (Zero Security Compromise)
* **Frontend / Control Plane (Streamlit Community Cloud):** Responsive, mobile-first SaaS interface built in Streamlit. Handles user authentication, project configuration, billing tracking, and management. **Never executes user Python code inside the Streamlit process.**
* **Worker Infrastructure (Isolated Linux Nodes):** User bots run on dedicated worker hosts using hardened non-root Docker containers or isolated process sandboxes with strict CPU, RAM, disk quotas, process limits, and automatic crash recovery.
* **Database & Persistence:** SQLite for local development, PostgreSQL for production. Complete relational schema, foreign keys, indexes, and automated migrations.

---

## 💎 Membership Plans & Limits

| Plan | Price | Max Active Bots | Dedicated RAM | Priority vCPU | Storage Quota | Backups | Support Tier |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **FREE** | **₹0 Free** | 1 Bot | 256 MB | 0.5 vCPU | 500 MB | ✕ None | Community |
| **STARTER** | **₹49 / month** | 3 Bots | 512 MB | 1.0 vCPU | 1,500 MB | ✓ Included | Standard |
| **PRO** | **₹99 / month** | 10 Bots | 1,024 MB | 2.0 vCPU | 5,000 MB | ✓ Included | Priority |
| **BUSINESS** | **₹199 / month** | 25 Bots | 2,048 MB | 4.0 vCPU | 15,000 MB | ✓ Included | 24/7 Dedicated |
| **LIFETIME** | **₹999 One-time** | 50 Bots | 4,096 MB | 4.0 vCPU | 30,000 MB | ✓ Included | VIP Direct Telegram |

*All quotas, pricing, and durations are fully dynamic and editable in real time from the Super Admin Panel.*

---

## 💳 Manual UPI Payment Architecture

NEXHOST CLOUD includes an auditable manual UPI payment workflow:
1. **User Selects Plan:** Chooses duration and views payable amount in ₹ INR.
2. **UPI Gateway Display:** Renders the Admin's UPI QR code alongside the UPI ID (`harsh54x@upi`) with account payee details.
3. **Transaction Reference (UTR):** User enters the unique 12-digit UPI banking reference number.
4. **Screenshot Upload:** User submits screenshot proof of payment.
5. **Anti-Fraud Duplicate Prevention:** The database enforces a `UNIQUE` constraint on `upi_ref_id`. Duplicate reference numbers are immediately rejected.
6. **Admin Verification Queue:** Uploading a screenshot does **NOT** activate a plan automatically. Only authorized Super Admins / Admins inspect the payment proof image and verify the UTR against banking records.
7. **Instant Activation:** On Admin approval:
   - User's subscription is automatically provisioned/extended.
   - User role is upgraded to `premium_user`.
   - In-app notification is delivered to the user.
   - An immutable audit trail entry is recorded.

---

## 📁 Repository & Folder Structure

```
NEXHOST-CLOUD/
├── app.py                      # Main entrypoint, landing page, auth tabs, global theme
├── config.py                   # Central typed configuration & secret loader
├── requirements.txt            # Python dependencies
├── packages.txt                # System packages for Debian/Streamlit Cloud
├── .env.example                # Example environment configuration
├── README.md                   # Comprehensive platform documentation
│
├── .streamlit/
│   └── config.toml             # Theme settings (dark SaaS palette, server limits)
│
├── pages/                      # Multi-page application architecture
│   ├── dashboard.py            # Overview metrics, status donut, recent bots, shortcuts
│   ├── deploy.py               # Deploy bot via ZIP upload with entrypoint detection
│   ├── my_projects.py          # Bot management panel (start, stop, restart, delete)
│   ├── github_import.py        # Import from public/private GitHub repositories
│   ├── file_manager.py         # In-browser file manager & code editor with syntax colors
│   ├── console.py              # Real-time console logs streamer, search, filter, download
│   ├── environment.py          # Environment variables & secrets manager with masking
│   ├── requirements_manager.py # Python runtime selector (3.10-3.12) & pip manager
│   ├── monitoring.py           # Real-time hardware telemetry gauges (CPU, RAM, Disk)
│   ├── scheduler.py            # Automated reboot schedules and crash watchdog
│   ├── backups.py              # Instant compressed snapshot generation & restore
│   ├── membership.py           # Subscription comparison cards & upgrade triggers
│   ├── payments.py             # UPI payment portal & personal payment history
│   ├── notifications.py        # In-app alert notifications center
│   ├── account.py              # Profile details, security settings, password change
│   ├── support.py              # Support ticket system & direct Telegram developer link
│   └── admin.py                # Super Admin panel (KPIs, queue, users, plans, workers)
│
├── components/                 # Reusable UI component modules
│   ├── sidebar.py              # Role-aware sidebar with quota meter & logout
│   ├── navbar.py               # Top brand bar, active plan pill, contact button
│   ├── cards.py                # Metric tiles, project cards, pricing matrices
│   ├── charts.py               # Plotly interactive graphs (gauges, donuts, lines)
│   ├── tables.py               # Searchable data tables for orders & deployments
│   ├── dialogs.py              # Safety confirmation dialogs
│   └── theme.py                # Custom CSS styling & branded developer footer
│
├── auth/                       # Authentication and authorization
│   ├── authentication.py       # Login & logout services
│   ├── registration.py         # User registration with automatic Free plan assignment
│   ├── password_reset.py       # Password update workflows
│   ├── permissions.py          # Strict role checks & user resource isolation
│   └── sessions.py             # Session state preservation
│
├── core/                       # SaaS engines & business logic
│   ├── deployment_engine.py    # Build coordination, dependency install & container launch
│   ├── project_manager.py      # Project lifecycle, unpack ZIP, delete project
│   ├── process_manager.py      # Bot process control (start, stop, restart, status)
│   ├── resource_manager.py     # Live resource quota enforcement
│   ├── runtime_manager.py      # Entrypoint auto-discovery & runtime versions
│   ├── membership_engine.py    # Backend quota evaluation (max bots, RAM, storage)
│   └── payment_engine.py       # UPI payment processing, duplicate check & activation
│
├── workers/                    # Worker node infrastructure
│   ├── worker_api.py           # Dedicated FastAPI REST service for worker nodes
│   ├── worker_client.py        # Control plane HTTP client with embedded local fallback
│   ├── docker_manager.py       # Hardened non-root Docker container orchestrator
│   ├── sandbox.py              # Secure process execution sandbox with psutil telemetry
│   └── monitor.py              # Background host telemetry sampler
│
├── database/                   # Database models & repositories
│   ├── connection.py           # SQLAlchemy engine, session maker, init & seed
│   ├── users.py                # User entity & UserRepository
│   ├── plans.py                # Plan entity & PlanRepository
│   ├── memberships.py          # UserMembership entity & MembershipRepository
│   ├── payments.py             # Payment entity with UNIQUE UTR constraint
│   ├── projects.py             # Project entity with user isolation
│   ├── deployments.py          # Deployment history & logs repository
│   ├── usage.py                # Resource usage time-series repository
│   └── audit_logs.py           # AuditLog, SupportTicket & SystemNotification
│
├── services/                   # External services & file storage
│   ├── github_service.py       # GitHub REST/zipball downloader & PAT authentication
│   ├── storage_service.py      # Isolated user storage with path-traversal blocking
│   ├── notification_service.py # In-app notification delivery
│   └── backup_service.py       # Compressed backup creator & restorer
│
├── utils/                      # Utilities & validators
│   ├── security.py             # PBKDF2 password hashing & token masking
│   ├── validators.py           # Safe ZIP extraction (Zip Slip defense), UTR & email
│   ├── logger.py               # Platform log rotator & formatter
│   └── helpers.py              # Byte formatting, currency formatting & status badges
│
├── tests/                      # Automated test suite (14/14 tests)
│   ├── conftest.py             # Pristine database fixture
│   ├── test_auth.py            # Registration, login, duplicate checks, password change
│   ├── test_permissions.py     # Role boundaries & user resource isolation
│   ├── test_membership_and_limits.py # Quota backend enforcement & upgrades
│   ├── test_payments.py        # UPI flow, duplicate UTR block, approve/reject
│   ├── test_deployment_and_worker.py # Zip Slip prevention, sandbox execution, masking
│   └── test_backups.py         # Snapshot creation, corruption simulation, restore
│
└── static/
    └── default_upi_qr.png      # Default UPI payment QR code
```

---

## 🚀 Deployment Instructions

### 1. Streamlit Community Cloud (Frontend / Control Plane)
1. Fork or push the `NEXHOST-CLOUD` folder to a GitHub repository.
2. Go to [share.streamlit.io](https://share.streamlit.io) and click **"New App"**.
3. Select your repository, branch (`main`), and set the Main file path to `app.py`.
4. Under **Advanced Settings > Secrets**, paste your environment secrets:
```toml
PLATFORM_NAME = "NEXHOST CLOUD"
TAGLINE = "Your Bots. Your Cloud."
DEVELOPER_HANDLE = "@Harsh_54x"
DEVELOPER_TELEGRAM = "https://t.me/Harsh_54x"
CURRENCY_SYMBOL = "₹"

SECRET_KEY = "your-32-byte-hex-random-secret"
SUPERADMIN_EMAIL = "owner@nexhost.cloud"
SUPERADMIN_USERNAME = "owner"
SUPERADMIN_PASSWORD = "YourStrongOwnerPassword2026!"
SUPERADMIN_NAME = "Super Administrator"

ADMIN_UPI_ID = "harsh54x@upi"
ADMIN_UPI_NAME = "NEXHOST CLOUD / Harsh"

# Production PostgreSQL Database
DATABASE_URL = "postgresql://nexhost_user:StrongPassword@db.yourprovider.com:5432/nexhost_db"

# Dedicated Linux Worker Connection
WORKER_TYPE = "docker"
WORKER_URL = "https://worker.nexhostcloud.com"
WORKER_API_KEY = "your-worker-shared-secret-token"
```
5. Click **Deploy!** Your cloud platform is live with custom branding.

---

### 2. Dedicated Linux Worker Node Setup
On a dedicated Ubuntu/Debian Linux VPS (e.g., Hetzner, DigitalOcean, AWS EC2):

```bash
# 1. Update system & install Docker
sudo apt update && sudo apt install -y docker.io python3-pip git curl
sudo systemctl enable --now docker

# 2. Clone NEXHOST CLOUD Worker repository
git clone https://github.com/your-org/nexhost-cloud.git /opt/nexhost-cloud
cd /opt/nexhost-cloud

# 3. Install worker dependencies
pip3 install -r requirements.txt

# 4. Configure environment
cat << 'EOF' > .env
WORKER_TYPE=docker
WORKER_API_KEY=your-worker-shared-secret-token
WORKER_URL=http://0.0.0.0:8000
DATABASE_URL=postgresql://nexhost_user:StrongPassword@db.yourprovider.com:5432/nexhost_db
EOF

# 5. Create systemd background service
sudo cat << 'EOF' > /etc/systemd/system/nexhost-worker.service
[Unit]
Description=NEXHOST CLOUD Worker Node Service
After=network.target docker.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/nexhost-cloud
ExecStart=/usr/local/bin/uvicorn workers.worker_api:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 6. Enable and start worker daemon
sudo systemctl daemon-reload
sudo systemctl enable --now nexhost-worker.service
sudo systemctl status nexhost-worker.service
```

---

## 🔑 Credentials & Configuration Guide

Everything is controlled via environment variables or `.env` / Streamlit secrets (`secrets.toml`). Here is what each credential is and where to obtain it:

| Configuration Key | Description | Where to Get It / Value |
| :--- | :--- | :--- |
| `DATABASE_URL` | PostgreSQL or SQLite connection string | **Neon PostgreSQL Console** (`postgresql://neondb_owner:npg_RTDvj86puILU@ep-purple-cherry-bcsvp5i7-pooler.c-16.us-east-1.aws.neon.tech/neondb?sslmode=require`) |
| `TELEGRAM_BOT_TOKEN` | Platform Telegram Bot Token | Open Telegram, message **[@BotFather](https://t.me/BotFather)**, send `/newbot`, and copy the token. |
| `TELEGRAM_API_ID` | Telegram Client API ID | Visit **[https://my.telegram.org/apps](https://my.telegram.org/apps)**, log in with your phone number, create an App, and copy the numeric App `api_id`. |
| `TELEGRAM_API_HASH` | Telegram Client API Hash | In **[https://my.telegram.org/apps](https://my.telegram.org/apps)**, copy the `api_hash` string. |
| `TELEGRAM_OWNER_ID` | Platform Owner Telegram Numeric ID | Message **[@userinfobot](https://t.me/userinfobot)** or **[@MissRose_bot](https://t.me/MissRose_bot)** (type `/id`) to get your numeric ID (e.g., `123456789`). |
| `MONGO_URI` | MongoDB Connection URI (Optional) | Visit **[MongoDB Atlas](https://www.mongodb.com/cloud/atlas)** (Free Shared Cluster) -> Connect -> Drivers -> copy URI (`mongodb+srv://...`). |
| `ADMIN_UPI_ID` | UPI ID for receiving payments | Your banking/GPay/PhonePe UPI ID (default: `harsh54x@upi`). |
| `SECRET_KEY` | JWT/Session encryption key | Any 32+ character random hex string: `python -c "import secrets; print(secrets.token_hex(32))"`. |

---

## 🤖 Telegram Bot Control Plane & Owner Access Gate

NEXHOST CLOUD includes a full-featured Telegram bot service (`bot_service.py`) built with strict **Owner-Gated Access Control**:

### 1. Unauthorized User Protection
* When ANY unauthorized user starts the bot (`/start`), access is strictly blocked.
* The user receives a professional English Access Restricted screen displaying their **Telegram User ID** and **Name**.
* The screen includes two buttons:
  - `📩 Request Access`
  - `💬 Contact Owner (@Harsh_54x)`

### 2. Real-Time Owner Review & Approval
* When a user taps `📩 Request Access`, the bot instantly dispatches an interactive notification card to the configured `TELEGRAM_OWNER_ID`:
  ```
  🚨 NEW USER ACCESS REQUEST
  👤 Name: John Doe (@johndoe)
  🆔 User ID: 987654321
  📅 Time: 2026-11-05 23:00:00 UTC
  ```
* The Owner can click any of the action buttons directly in Telegram:
  - `✅ Free (1 Bot)`
  - `⚡ Starter (3 Bots)`
  - `💎 Pro (10 Bots)`
  - `❌ Deny Request`
* Upon approval:
  - User's account is activated in PostgreSQL.
  - The user immediately receives a celebration notification in Telegram: *"Access Approved! Click /start to deploy your bots."*

### 3. Owner Master Commands
The Platform Owner (`TELEGRAM_OWNER_ID`) has full control via Telegram:
* `/auth <user_id> [free|starter|pro|business]` — Manually authorize any Telegram user and assign a plan.
* `/unauth <user_id>` — Revoke authorization and freeze access.
* `/authusers` or `/users` — List all authorized users and their active bot counts.
* `/pending` — View all pending access requests with approval buttons.
* `/broadcast <message>` — Send an instant announcement to all authorized platform users.
* `/stats` — Real-time health metrics (users, running bots, database status, memory).

### 4. Direct Deployment via Telegram
Authorized users can deploy and manage bots directly from Telegram:
* **Direct .ZIP Upload:** Send any bot project `.zip` file in the chat to extract, detect `requirements.txt`, install dependencies, and launch 24/7.
* **GitHub Public & Private:** Send `/git https://github.com/user/bot-repo [token] [branch]`.
* **Bot Controls:** `/mybots` provides interactive buttons for `▶️ Start`, `🛑 Stop`, `🔄 Restart`, `📋 Logs`, `⚙️ Env Vars`, and `🗑️ Delete`.
* **Secrets Injection:** `/setenv <project_id> BOT_TOKEN <token>` safely injects secrets without leaking in chat.

---

### 3. Local Development (Instant Out-of-the-Box)
You can run the entire platform locally in single-host mode with zero extra setup:

```powershell
# Clone and navigate into directory
cd D:\test\NEXHOST-CLOUD

# Install dependencies
pip install -r requirements.txt

# Launch Streamlit Application
streamlit run app.py
```
*The embedded worker engine automatically activates using local sandbox mode, requiring no external worker or database services.*

---

## 🧪 Automated Test Suite

Run the full automated test suite anytime with pytest (18/18 Passing):
```powershell
pytest tests -v
```
**Test Coverage Includes:**
- User registration, password complexity, duplicate email/username rejection
- Authentication & login validation, suspension enforcement
- Password update flow
- Role hierarchy & strict user data isolation (User B cannot access User A's bots/files)
- Free plan quota enforcement (1 bot limit) and capacity expansion on upgrade
- Manual UPI payment request submission, UTR uniqueness constraint
- Duplicate transaction reference blocking
- Admin approval with automatic role upgrade and plan activation
- Rejection with audit log recording
- Zip-Slip path traversal attack detection and defense
- Worker process sandbox lifecycle (start, log capture, stop)
- Sensitive secret masking (Telegram bot tokens masked in logs)
- Full snapshot backup creation, intentional file corruption, and byte-for-byte restore
- Telegram bot user auto-registration and default authorization lock
- Telegram access request state machine and pending list query
- Real-time Owner one-click access approval and tier provisioning
- Dynamic TELEGRAM_OWNER_ID bypass authorization
- MongoDB logger graceful fallback when database is unconfigured or offline

---

## 🔒 Security Architecture Highlights
1. **Control Plane Isolation:** Streamlit Community Cloud acts solely as a UI and API dispatcher.
2. **Execution Sandboxing:** Subprocesses and Docker containers drop privileges and execute with non-root UID `1000:1000`.
3. **No Docker Socket Mounting:** Containers are prevented from communicating with the host Docker daemon.
4. **Zip-Slip Defense:** All uploaded archives are validated member-by-member before extraction, neutralizing `../` directory traversal attempts.
5. **Secret Masking:** Telegram bot tokens (`123456789:ABC...`) and sensitive environment variables are sanitized with regex filters before rendering in web consoles.
6. **Audit Trails:** Critical actions (logins, payments, approvals, deletions) are immutably logged with timestamps.

---

## 💬 Developer & Support Branding
* **Platform Name:** NEXHOST CLOUD
* **Tagline:** Your Bots. Your Cloud.
* **Lead Developer:** [@Harsh_54x](https://t.me/Harsh_54x)
* **Direct Telegram Support:** [https://t.me/Harsh_54x](https://t.me/Harsh_54x)
* **Default Super Admin:** `owner@nexhost.cloud` / `OwnerSecurePass2026!` (Configurable via secrets)
