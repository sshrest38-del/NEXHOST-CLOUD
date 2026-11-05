"""
NEXHOST CLOUD - Audit Logs, Support Tickets, and Notifications
Author: @Harsh_54x
"""

from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import Column, Integer, ForeignKey, String, Text, Boolean, DateTime
from sqlalchemy.orm import relationship
from database.connection import Base, get_db

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    resource = Column(String(100), nullable=True)
    ip_address = Column(String(50), nullable=True)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", lazy="joined")

class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    priority = Column(String(20), default="NORMAL", nullable=False)  # LOW, NORMAL, HIGH, URGENT
    status = Column(String(30), default="OPEN", nullable=False)  # OPEN, IN_PROGRESS, RESOLVED, CLOSED
    admin_reply = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", lazy="joined")

class SystemNotification(Base):
    __tablename__ = "system_notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(150), nullable=False)
    message = Column(Text, nullable=False)
    level = Column(String(20), default="INFO", nullable=False)  # INFO, SUCCESS, WARNING, ERROR
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

class AuditLogRepository:
    @staticmethod
    def record(user_id: Optional[int], action: str, resource: str = "", details: str = "", ip_address: str = "127.0.0.1"):
        with get_db() as db:
            log = AuditLog(
                user_id=user_id,
                action=action,
                resource=resource,
                ip_address=ip_address,
                details=details,
                timestamp=datetime.now(timezone.utc)
            )
            db.add(log)
            db.commit()

    @staticmethod
    def list_all(limit: int = 50) -> List[AuditLog]:
        with get_db() as db:
            return db.query(AuditLog).order_by(AuditLog.id.desc()).limit(limit).all()

class SupportTicketRepository:
    @staticmethod
    def create(user_id: int, subject: str, message: str, priority: str = "NORMAL") -> SupportTicket:
        with get_db() as db:
            ticket = SupportTicket(
                user_id=user_id,
                subject=subject.strip(),
                message=message.strip(),
                priority=priority.upper(),
                status="OPEN",
                created_at=datetime.now(timezone.utc)
            )
            db.add(ticket)
            db.commit()
            db.refresh(ticket)
            return ticket

    @staticmethod
    def list_by_user(user_id: int) -> List[SupportTicket]:
        with get_db() as db:
            return db.query(SupportTicket).filter(
                SupportTicket.user_id == user_id
            ).order_by(SupportTicket.id.desc()).all()

    @staticmethod
    def list_all() -> List[SupportTicket]:
        with get_db() as db:
            return db.query(SupportTicket).order_by(SupportTicket.id.desc()).all()

    @staticmethod
    def reply_ticket(ticket_id: int, reply: str, status: str = "RESOLVED") -> bool:
        with get_db() as db:
            ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
            if ticket:
                ticket.admin_reply = reply.strip()
                ticket.status = status.upper()
                ticket.updated_at = datetime.now(timezone.utc)
                db.commit()
                return True
            return False

class NotificationRepository:
    @staticmethod
    def send(user_id: int, title: str, message: str, level: str = "INFO") -> SystemNotification:
        with get_db() as db:
            notif = SystemNotification(
                user_id=user_id,
                title=title.strip(),
                message=message.strip(),
                level=level.upper(),
                created_at=datetime.now(timezone.utc)
            )
            db.add(notif)
            db.commit()
            db.refresh(notif)
            return notif

    @staticmethod
    def list_by_user(user_id: int, limit: int = 20) -> List[SystemNotification]:
        with get_db() as db:
            return db.query(SystemNotification).filter(
                SystemNotification.user_id == user_id
            ).order_by(SystemNotification.id.desc()).limit(limit).all()

    @staticmethod
    def mark_all_as_read(user_id: int):
        with get_db() as db:
            db.query(SystemNotification).filter(
                SystemNotification.user_id == user_id,
                SystemNotification.is_read == False
            ).update({"is_read": True})
            db.commit()
