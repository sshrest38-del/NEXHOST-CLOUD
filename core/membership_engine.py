"""
NEXHOST CLOUD - Membership Engine and Quota Enforcement
Author: @Harsh_54x
"""

from typing import Dict, Any, Tuple, Optional
from database.users import UserRepository
from database.plans import PlanRepository
from database.memberships import MembershipRepository
from database.projects import ProjectRepository
from services.storage_service import StorageService

class MembershipEngine:
    @classmethod
    def get_user_limits(cls, user_id: int) -> Dict[str, Any]:
        """
        Calculate effective resource quotas and remaining capacity for user.
        Incorporates custom Super Admin overrides if assigned.
        """
        user = UserRepository.get_by_id(user_id)
        if not user:
            return {
                "plan_name": "NONE",
                "max_bots": 0,
                "current_bots": 0,
                "running_bots": 0,
                "remaining_slots": 0,
                "max_ram_mb": 0,
                "max_cpu_cores": 0.0,
                "max_storage_mb": 0,
                "used_storage_mb": 0.0,
                "backup_enabled": False,
                "support_tier": "None",
                "is_active": False,
                "expires_at": None,
                "is_lifetime": False
            }

        # Fetch active membership
        membership = MembershipRepository.get_active_membership(user_id)
        plan = membership.plan if membership else PlanRepository.get_by_name("FREE")

        max_bots = user.custom_bot_limit if user.custom_bot_limit is not None else (plan.max_bots if plan else 1)
        max_ram_mb = user.custom_ram_mb if user.custom_ram_mb is not None else (plan.max_ram_mb if plan else 256)
        max_cpu_cores = user.custom_cpu_cores if user.custom_cpu_cores is not None else (plan.max_cpu_cores if plan else 0.5)
        max_storage_mb = user.custom_storage_mb if user.custom_storage_mb is not None else (plan.max_storage_mb if plan else 500)
        backup_enabled = plan.backup_enabled if plan else False
        support_tier = plan.support_tier if plan else "Community"

        current_bots = ProjectRepository.count_by_user(user_id)
        running_bots = ProjectRepository.count_running_by_user(user_id)
        remaining_slots = max(0, max_bots - current_bots)

        used_storage_bytes = StorageService.calculate_user_total_storage(user_id)
        used_storage_mb = round(used_storage_bytes / (1024 * 1024), 2)

        return {
            "plan_name": plan.name if plan else "FREE",
            "plan_display": plan.display_name if plan else "Free Plan",
            "max_bots": max_bots,
            "current_bots": current_bots,
            "running_bots": running_bots,
            "remaining_slots": remaining_slots,
            "max_ram_mb": max_ram_mb,
            "max_cpu_cores": max_cpu_cores,
            "max_storage_mb": max_storage_mb,
            "used_storage_mb": used_storage_mb,
            "storage_percent": min(100.0, round((used_storage_mb / max_storage_mb) * 100, 1)) if max_storage_mb else 0,
            "backup_enabled": backup_enabled,
            "support_tier": support_tier,
            "is_active": bool(membership and membership.status == "ACTIVE"),
            "expires_at": membership.expires_at if membership else None,
            "is_lifetime": membership.is_lifetime if membership else False,
        }

    @classmethod
    def can_create_bot(cls, user_id: int) -> Tuple[bool, str]:
        """Verify user has an available bot deployment slot."""
        limits = cls.get_user_limits(user_id)
        if limits["current_bots"] >= limits["max_bots"]:
            return False, f"Bot slot limit reached ({limits['current_bots']}/{limits['max_bots']}). Upgrade your plan to host more bots."
        return True, "Slot available."

    @classmethod
    def can_start_bot(cls, user_id: int, project_id: int) -> Tuple[bool, str]:
        """Verify user has not exceeded limits before starting container/bot."""
        user = UserRepository.get_by_id(user_id)
        if not user or not user.is_active:
            return False, "Account is disabled or suspended."

        limits = cls.get_user_limits(user_id)
        if limits["running_bots"] >= limits["max_bots"]:
            return False, f"Maximum concurrent running bots reached ({limits['running_bots']}/{limits['max_bots']}). Please stop another bot first or upgrade."

        if limits["used_storage_mb"] > limits["max_storage_mb"]:
            return False, f"Storage quota exceeded ({limits['used_storage_mb']}MB / {limits['max_storage_mb']}MB). Please free up disk space."

        return True, "Ready to start."
