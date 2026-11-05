"""
NEXHOST CLOUD - In-App Notification and Alert Service
Author: @Harsh_54x
"""

from typing import List
from database.audit_logs import SystemNotification, NotificationRepository

class NotificationService:
    @staticmethod
    def notify_user(user_id: int, title: str, message: str, level: str = "INFO"):
        """Deliver persistent in-app notification to user."""
        return NotificationRepository.send(user_id, title, message, level)

    @staticmethod
    def get_unread_count(user_id: int) -> int:
        """Count unread notifications for badge display."""
        notifications = NotificationRepository.list_by_user(user_id, limit=50)
        return sum(1 for n in notifications if not n.is_read)

    @staticmethod
    def get_recent(user_id: int, limit: int = 15) -> List[SystemNotification]:
        """Fetch latest notifications."""
        return NotificationRepository.list_by_user(user_id, limit=limit)

    @staticmethod
    def mark_all_read(user_id: int):
        """Mark all notifications as read."""
        NotificationRepository.mark_all_as_read(user_id)
