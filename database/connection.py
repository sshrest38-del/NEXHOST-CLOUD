"""
NEXHOST CLOUD - Database Engine and Connection Lifecycle
Author: @Harsh_54x
"""

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from config import DATABASE_URL, SUPERADMIN_EMAIL, SUPERADMIN_PASSWORD, SUPERADMIN_USERNAME, SUPERADMIN_NAME
from utils.logger import logger
from utils.security import hash_password

# Engine setup
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine)
Base = declarative_base()

@contextmanager
def get_db():
    """Context manager for scoped database sessions."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def init_db():
    """
    Initialize all database tables and seed initial plans and owner Super Admin.
    Guarantees idempotency.
    """
    # Import all models to register with Base.metadata
    from database.users import User
    from database.plans import Plan
    from database.memberships import UserMembership
    from database.payments import Payment
    from database.projects import Project
    from database.deployments import Deployment
    from database.usage import ResourceUsage
    from database.audit_logs import AuditLog, SupportTicket, SystemNotification

    Base.metadata.create_all(bind=engine)
    logger.info("Database schema verified and tables synchronized.")

    with get_db() as db:
        # Seed default Plans if table is empty
        if db.query(Plan).count() == 0:
            default_plans = [
                Plan(
                    name="FREE",
                    display_name="Free Explorer",
                    price_inr=0.0,
                    max_bots=1,
                    max_ram_mb=256,
                    max_cpu_cores=0.5,
                    max_storage_mb=500,
                    backup_enabled=False,
                    support_tier="Community",
                    duration_days=3650,
                    description="Ideal for beginners learning Telegram bot development."
                ),
                Plan(
                    name="STARTER",
                    display_name="Starter Creator",
                    price_inr=49.0,
                    max_bots=3,
                    max_ram_mb=512,
                    max_cpu_cores=1.0,
                    max_storage_mb=1500,
                    backup_enabled=True,
                    support_tier="Standard",
                    duration_days=30,
                    description="Reliable continuous hosting for up to 3 active bots."
                ),
                Plan(
                    name="PRO",
                    display_name="Pro Developer",
                    price_inr=99.0,
                    max_bots=10,
                    max_ram_mb=1024,
                    max_cpu_cores=2.0,
                    max_storage_mb=5000,
                    backup_enabled=True,
                    support_tier="Priority",
                    duration_days=30,
                    description="High performance, priority CPU and instant crash recovery."
                ),
                Plan(
                    name="BUSINESS",
                    display_name="Business Enterprise",
                    price_inr=199.0,
                    max_bots=25,
                    max_ram_mb=2048,
                    max_cpu_cores=4.0,
                    max_storage_mb=15000,
                    backup_enabled=True,
                    support_tier="24/7 Dedicated",
                    duration_days=30,
                    description="Maximum power, massive storage and priority worker allocation."
                ),
                Plan(
                    name="LIFETIME",
                    display_name="Lifetime Founder",
                    price_inr=999.0,
                    max_bots=50,
                    max_ram_mb=4096,
                    max_cpu_cores=4.0,
                    max_storage_mb=30000,
                    backup_enabled=True,
                    support_tier="VIP Direct Telegram",
                    duration_days=36500,
                    description="Pay once and host up to 50 bots forever with VIP founder perks."
                ),
            ]
            db.add_all(default_plans)
            db.commit()
            logger.info("Seeded 5 initial membership plans successfully.")

        # Ensure Super Admin Owner account exists from environment secrets
        admin_user = db.query(User).filter(User.email == SUPERADMIN_EMAIL).first()
        if not admin_user:
            admin_user = User(
                email=SUPERADMIN_EMAIL,
                username=SUPERADMIN_USERNAME,
                password_hash=hash_password(SUPERADMIN_PASSWORD),
                full_name=SUPERADMIN_NAME,
                role="super_admin",
                is_active=True,
                is_verified=True,
                created_at=datetime.now(timezone.utc)
            )
            db.add(admin_user)
            db.flush()

            # Assign Lifetime plan to owner
            lifetime_plan = db.query(Plan).filter(Plan.name == "LIFETIME").first()
            if lifetime_plan:
                owner_membership = UserMembership(
                    user_id=admin_user.id,
                    plan_id=lifetime_plan.id,
                    status="ACTIVE",
                    started_at=datetime.now(timezone.utc),
                    expires_at=datetime.now(timezone.utc) + timedelta(days=36500),
                    is_lifetime=True
                )
                db.add(owner_membership)
            db.commit()
            logger.info(f"Super Admin initialized securely for email: {SUPERADMIN_EMAIL}")
