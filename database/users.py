"""
NEXHOST CLOUD - User Entity Model and Repository
Author: @Harsh_54x
"""

from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import Column, Integer, BigInteger, String, Boolean, DateTime, Float
from database.connection import Base, get_db

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(150), unique=True, index=True, nullable=False)
    username = Column(String(60), unique=True, index=True, nullable=False)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(120), nullable=True)
    role = Column(String(30), default="free_user", nullable=False)  # super_admin, admin, premium_user, free_user
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=True, nullable=False)
    is_telegram_authorized = Column(Boolean, default=False, nullable=False)
    telegram_access_requested = Column(Boolean, default=False, nullable=False)
    
    # Custom admin overrides
    custom_bot_limit = Column(Integer, nullable=True)
    custom_ram_mb = Column(Integer, nullable=True)
    custom_cpu_cores = Column(Float, nullable=True)
    custom_storage_mb = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class UserRepository:
    @staticmethod
    def get_by_id(user_id: int) -> Optional[User]:
        with get_db() as db:
            return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_by_email(email: str) -> Optional[User]:
        with get_db() as db:
            return db.query(User).filter(User.email == email.strip().lower()).first()

    @staticmethod
    def get_by_username(username: str) -> Optional[User]:
        with get_db() as db:
            return db.query(User).filter(User.username == username.strip().lower()).first()

    @staticmethod
    def get_by_telegram_id(telegram_id: int) -> Optional[User]:
        with get_db() as db:
            return db.query(User).filter(User.telegram_id == telegram_id).first()

    @staticmethod
    def link_telegram_id(user_id: int, telegram_id: int) -> bool:
        with get_db() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.telegram_id = telegram_id
                user.updated_at = datetime.now(timezone.utc)
                db.commit()
                return True
            return False

    @staticmethod
    def get_or_create_by_telegram(telegram_id: int, tg_username: str = "", full_name: str = "") -> "User":
        with get_db() as db:
            user = db.query(User).filter(User.telegram_id == telegram_id).first()
            if user:
                return user
            
            from utils.security import hash_password
            from database.plans import PlanRepository
            from database.memberships import MembershipRepository
            
            clean_username = f"tg_{telegram_id}" if not tg_username else tg_username.lower()
            # Handle conflict if username exists
            if db.query(User).filter(User.username == clean_username).first():
                clean_username = f"tg_{telegram_id}"
            
            email = f"{clean_username}@telegram.nexhost.cloud"
            dummy_pw = hash_password(f"tg_pass_{telegram_id}_2026")
            
            new_user = User(
                email=email,
                username=clean_username,
                telegram_id=telegram_id,
                password_hash=dummy_pw,
                full_name=full_name or clean_username,
                role="free_user",
                is_active=True,
                is_verified=True,
                created_at=datetime.now(timezone.utc)
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            # Assign FREE Plan
            free_plan = PlanRepository.get_by_name("FREE")
            if free_plan:
                MembershipRepository.assign_plan(new_user.id, free_plan)
                
            return new_user

    @staticmethod
    def is_telegram_authorized(telegram_id: int) -> bool:
        from config import TELEGRAM_OWNER_ID
        if TELEGRAM_OWNER_ID and telegram_id == TELEGRAM_OWNER_ID:
            return True
        with get_db() as db:
            user = db.query(User).filter(User.telegram_id == telegram_id).first()
            if not user:
                return False
            # Super admin or admin is always authorized
            if user.role in ["super_admin", "admin"]:
                return True
            return bool(user.is_telegram_authorized and user.is_active)

    @staticmethod
    def set_telegram_access_requested(telegram_id: int, requested: bool = True) -> bool:
        with get_db() as db:
            user = db.query(User).filter(User.telegram_id == telegram_id).first()
            if user:
                user.telegram_access_requested = requested
                user.updated_at = datetime.now(timezone.utc)
                db.commit()
                return True
            return False

    @staticmethod
    def authorize_telegram_user(telegram_id: int, role: Optional[str] = None) -> bool:
        with get_db() as db:
            user = db.query(User).filter(User.telegram_id == telegram_id).first()
            if user:
                user.is_telegram_authorized = True
                user.telegram_access_requested = False
                if role:
                    user.role = role
                user.updated_at = datetime.now(timezone.utc)
                db.commit()
                return True
            return False

    @staticmethod
    def deauthorize_telegram_user(telegram_id: int) -> bool:
        with get_db() as db:
            user = db.query(User).filter(User.telegram_id == telegram_id).first()
            if user:
                user.is_telegram_authorized = False
                user.updated_at = datetime.now(timezone.utc)
                db.commit()
                return True
            return False

    @staticmethod
    def list_authorized_telegram_users() -> List["User"]:
        with get_db() as db:
            return db.query(User).filter(User.is_telegram_authorized == True).all()

    @staticmethod
    def list_pending_telegram_requests() -> List["User"]:
        with get_db() as db:
            return db.query(User).filter(
                User.telegram_access_requested == True,
                User.is_telegram_authorized == False
            ).all()

    @staticmethod
    def create(email: str, username: str, password_hash: str, full_name: str = "", role: str = "free_user") -> User:
        with get_db() as db:
            user = User(
                email=email.strip().lower(),
                username=username.strip().lower(),
                password_hash=password_hash,
                full_name=full_name.strip() if full_name else username,
                role=role,
                is_active=True,
                is_verified=True,
                created_at=datetime.now(timezone.utc)
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            return user

    @staticmethod
    def list_all(search: str = "") -> List[User]:
        with get_db() as db:
            query = db.query(User)
            if search:
                s = f"%{search.lower()}%"
                query = query.filter((User.email.ilike(s)) | (User.username.ilike(s)) | (User.full_name.ilike(s)))
            return query.order_by(User.id.desc()).all()

    @staticmethod
    def count() -> int:
        with get_db() as db:
            return db.query(User).count()

    @staticmethod
    def update_role(user_id: int, new_role: str) -> bool:
        with get_db() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.role = new_role
                user.updated_at = datetime.now(timezone.utc)
                db.commit()
                return True
            return False

    @staticmethod
    def update_active_status(user_id: int, is_active: bool) -> bool:
        with get_db() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.is_active = is_active
                user.updated_at = datetime.now(timezone.utc)
                db.commit()
                return True
            return False

    @staticmethod
    def update_password(user_id: int, new_password_hash: str) -> bool:
        with get_db() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.password_hash = new_password_hash
                user.updated_at = datetime.now(timezone.utc)
                db.commit()
                return True
            return False

    @staticmethod
    def set_custom_limits(user_id: int, bots: Optional[int], ram_mb: Optional[int], cpu: Optional[float], storage_mb: Optional[int]) -> bool:
        with get_db() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.custom_bot_limit = bots
                user.custom_ram_mb = ram_mb
                user.custom_cpu_cores = cpu
                user.custom_storage_mb = storage_mb
                user.updated_at = datetime.now(timezone.utc)
                db.commit()
                return True
            return False
