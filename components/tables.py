"""
NEXHOST CLOUD - Formatted Tables and List Renderers
Author: @Harsh_54x
"""

from typing import List, Dict, Any
import pandas as pd
import streamlit as st
from utils.helpers import get_status_badge, format_currency

def render_payments_table(payments: List[Any], is_admin: bool = False):
    """Render payments history table."""
    if not payments:
        st.info("No payment records found.")
        return

    rows = []
    for p in payments:
        rows.append({
            "Payment ID": f"#{p.id}",
            "Plan": p.plan.display_name if p.plan else "N/A",
            "Amount": format_currency(p.amount_inr),
            "UPI Reference / UTR": p.upi_ref_id,
            "Status": p.status,
            "Date (UTC)": p.created_at.strftime("%Y-%m-%d %H:%M") if p.created_at else "N/A"
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

def render_deployments_table(deployments: List[Any]):
    """Render project deployments history table."""
    if not deployments:
        st.info("No deployments recorded for this bot yet.")
        return

    rows = []
    for d in deployments:
        rows.append({
            "Deployment": f"#{d.deployment_number}",
            "Status": d.status,
            "Version": d.commit_or_version or "latest",
            "Started": d.started_at.strftime("%Y-%m-%d %H:%M:%S") if d.started_at else "N/A",
            "Exit Code": d.exit_code if d.exit_code is not None else ("Running" if d.status == "RUNNING" else "N/A")
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
