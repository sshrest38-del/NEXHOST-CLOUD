"""
NEXHOST CLOUD - General Presentation and Data Helpers
Author: @Harsh_54x
"""

from datetime import datetime, timezone
from typing import Optional

def format_currency(amount: float) -> str:
    """Format INR currency."""
    if amount == 0:
        return "₹0 Free"
    return f"₹{amount:,.0f}" if amount.is_integer() else f"₹{amount:,.2f}"

def format_bytes(num_bytes: int) -> str:
    """Format bytes into readable units (KB, MB, GB)."""
    if num_bytes is None:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:3.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} PB"

def format_uptime(seconds: Optional[int]) -> str:
    """Format seconds into human-readable uptime string."""
    if not seconds or seconds < 0:
        return "Offline"
    mins, secs = divmod(seconds, 60)
    hours, mins = divmod(mins, 60)
    days, hours = divmod(hours, 24)
    if days > 0:
        return f"{days}d {hours}h {mins}m"
    if hours > 0:
        return f"{hours}h {mins}m {secs}s"
    if mins > 0:
        return f"{mins}m {secs}s"
    return f"{secs}s"

def get_status_badge(status: str) -> str:
    """Generate modern HTML status badge for Streamlit markdown rendering."""
    status_lower = (status or "").lower()
    styles = {
        "running": ("#10B981", "#064E3B", "● Running"),
        "stopped": ("#F59E0B", "#78350F", "■ Stopped"),
        "failed": ("#EF4444", "#7F1D1D", "✕ Failed"),
        "deploying": ("#3B82F6", "#1E3A8A", "◌ Deploying"),
        "building": ("#8B5CF6", "#4C1D95", "⚙ Building"),
        "approved": ("#10B981", "#064E3B", "✓ Approved"),
        "pending": ("#F59E0B", "#78350F", "⌛ Pending Review"),
        "under review": ("#3B82F6", "#1E3A8A", "🔍 Under Review"),
        "rejected": ("#EF4444", "#7F1D1D", "✕ Rejected"),
        "active": ("#10B981", "#064E3B", "✓ Active"),
        "expired": ("#6B7280", "#374151", "✕ Expired"),
    }
    
    color, bg, text = styles.get(status_lower, ("#94A3B8", "#1E293B", status.capitalize()))
    return (
        f'<span style="background-color: {bg}; color: {color}; '
        f'padding: 3px 10px; border-radius: 9999px; font-size: 0.82rem; '
        f'font-weight: 600; display: inline-flex; align-items: center; border: 1px solid {color}33;">'
        f'{text}</span>'
    )
