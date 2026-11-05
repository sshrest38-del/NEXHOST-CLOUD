"""
NEXHOST CLOUD - Metric, Project, and Plan Display Cards
Author: @Harsh_54x
"""

from typing import Any
import streamlit as st
from utils.helpers import format_currency, format_bytes, get_status_badge

def metric_card(title: str, value: Any, subtitle: str = "", icon: str = "⚡", color: str = "#6366F1"):
    """Render modern glassmorphism metric tile."""
    st.markdown(f"""
    <div class="nex-card">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div>
                <div class="nex-stat-label">{title}</div>
                <div class="nex-stat-val" style="background: linear-gradient(135deg, #FFFFFF 0%, {color} 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{value}</div>
                <div style="font-size: 0.78rem; color: #9CA3AF; margin-top: 4px;">{subtitle}</div>
            </div>
            <div style="background: {color}22; border: 1px solid {color}44; width: 42px; height: 42px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 1.3rem;">
                {icon}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def project_card(project_name: str, status: str, runtime: str, command: str, storage_mb: float, project_id: int):
    """Render project card summary."""
    badge = get_status_badge(status)
    st.markdown(f"""
    <div class="nex-card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <div style="font-size: 1.15rem; font-weight: 700; color: #FFFFFF;">{project_name}</div>
            <div>{badge}</div>
        </div>
        <div style="font-size: 0.82rem; color: #9CA3AF; margin-bottom: 6px;">
            Command: <code style="color: #A5B4FC; background: rgba(99,102,241,0.1); padding: 2px 6px; border-radius: 4px;">{command}</code>
        </div>
        <div style="display: flex; gap: 14px; font-size: 0.78rem; color: #6B7280;">
            <span>Runtime: <strong style="color: #D1D5DB;">{runtime}</strong></span>
            <span>&bull;</span>
            <span>Disk: <strong style="color: #D1D5DB;">{storage_mb:.1f} MB</strong></span>
            <span>&bull;</span>
            <span>ID: <strong style="color: #D1D5DB;">#{project_id}</strong></span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def plan_pricing_card(name: str, price_inr: float, max_bots: int, max_ram_mb: int,
                      max_cpu: float, max_storage_mb: int, backup: bool, support: str,
                      is_current: bool = False, is_popular: bool = False) -> str:
    """Generate HTML for membership comparison card."""
    border_color = "#6366F1" if is_popular else ("#10B981" if is_current else "rgba(255,255,255,0.08)")
    popular_badge = '<div style="position: absolute; top: -12px; right: 15px; background: #6366F1; color: #FFF; font-size: 0.7rem; font-weight: 800; padding: 2px 10px; border-radius: 9999px; text-transform: uppercase;">Most Popular</div>' if is_popular else ""
    current_badge = '<div style="position: absolute; top: -12px; left: 15px; background: #10B981; color: #FFF; font-size: 0.7rem; font-weight: 800; padding: 2px 10px; border-radius: 9999px; text-transform: uppercase;">Active Plan</div>' if is_current else ""

    price_tag = f"₹{price_inr:,.0f}" if price_inr > 0 else "Free"
    period = "/one-time" if name == "LIFETIME" else ("/month" if price_inr > 0 else " Forever")

    return f"""
    <div style="position: relative; background: rgba(17, 24, 39, 0.85); border: 2px solid {border_color}; border-radius: 16px; padding: 1.6rem 1.2rem; margin-bottom: 1.2rem; height: 100%;">
        {popular_badge}
        {current_badge}
        <div style="font-size: 1.15rem; font-weight: 800; color: #FFFFFF; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px;">{name}</div>
        <div style="margin-bottom: 1rem;">
            <span style="font-size: 2.2rem; font-weight: 800; color: #FFFFFF;">{price_tag}</span>
            <span style="font-size: 0.85rem; color: #9CA3AF;">{period}</span>
        </div>
        <hr style="border: 0; border-top: 1px solid rgba(255,255,255,0.08); margin: 0.8rem 0;" />
        <ul style="list-style: none; padding-left: 0; margin-bottom: 1.2rem; font-size: 0.85rem; color: #D1D5DB; line-height: 1.8;">
            <li>🤖 <strong>{max_bots}</strong> Active Telegram Bot{'s' if max_bots > 1 else ''}</li>
            <li>⚡ <strong>{max_ram_mb} MB</strong> Dedicated RAM</li>
            <li>🚀 <strong>{max_cpu} vCPU</strong> Priority CPU</li>
            <li>💾 <strong>{max_storage_mb} MB</strong> Persistent Storage</li>
            <li>🛡️ Daily Backups: <strong>{'Included' if backup else 'None'}</strong></li>
            <li>💬 Support: <strong>{support}</strong></li>
        </ul>
    </div>
    """
