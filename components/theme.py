"""
NEXHOST CLOUD - Custom Theme, CSS Injector, and Developer Footer
Author: @Harsh_54x
"""

import streamlit as st
from config import PLATFORM_NAME, TAGLINE, DEVELOPER_HANDLE, DEVELOPER_TELEGRAM

CUSTOM_CSS = """
<style>
/* ===================================================================
   NEXHOST CLOUD - Premium SaaS Dark Architecture
   =================================================================== */

@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
}

code, pre, .stCodeBlock {
    font-family: 'JetBrains Mono', monospace !important;
}

/* Background Gradients */
.stApp {
    background: radial-gradient(circle at 15% 10%, rgba(99, 102, 241, 0.08), transparent 30%),
                radial-gradient(circle at 85% 85%, rgba(16, 185, 129, 0.05), transparent 35%),
                #090D16 !important;
    color: #F3F4F6 !important;
}

/* Glassmorphism Cards */
.nex-card {
    background: rgba(17, 24, 39, 0.75);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    padding: 1.3rem;
    margin-bottom: 1rem;
    box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.4);
    transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}

.nex-card:hover {
    border-color: rgba(99, 102, 241, 0.35);
    box-shadow: 0 8px 30px -4px rgba(99, 102, 241, 0.15);
}

.nex-card-header {
    font-size: 1.1rem;
    font-weight: 700;
    color: #FFFFFF;
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* Metric Display Numbers */
.nex-stat-val {
    font-size: 2.1rem;
    font-weight: 800;
    background: linear-gradient(135deg, #FFFFFF 0%, #A5B4FC 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    line-height: 1.2;
}

.nex-stat-label {
    font-size: 0.85rem;
    color: #9CA3AF;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* Buttons Styling */
.stButton>button {
    border-radius: 9px !important;
    font-weight: 600 !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    transition: all 0.2s ease-in-out !important;
    background-color: #1F2937 !important;
    color: #F9FAFB !important;
}

.stButton>button:hover {
    background: #6366F1 !important;
    border-color: #818CF8 !important;
    color: #FFFFFF !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 14px rgba(99, 102, 241, 0.4) !important;
}

/* Primary Button Highlighting */
.stButton>button[kind="primary"] {
    background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%) !important;
    border: 1px solid #818CF8 !important;
    box-shadow: 0 4px 15px rgba(79, 70, 229, 0.35) !important;
}

/* Tabs custom design */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background-color: rgba(17, 24, 39, 0.6);
    padding: 6px;
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.05);
}

.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    color: #9CA3AF;
    font-weight: 600;
    padding: 8px 18px;
}

.stTabs [aria-selected="true"] {
    background-color: #6366F1 !important;
    color: #FFFFFF !important;
}

/* Mobile Responsiveness */
@media (max-width: 768px) {
    .nex-card {
        padding: 1rem;
    }
    .nex-stat-val {
        font-size: 1.6rem;
    }
    .stApp {
        padding: 0.5rem;
    }
}

/* Developer Contact Banner */
.dev-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(99, 102, 241, 0.12);
    border: 1px solid rgba(99, 102, 241, 0.3);
    color: #C7D2FE;
    padding: 4px 12px;
    border-radius: 9999px;
    font-size: 0.82rem;
    font-weight: 600;
    text-decoration: none;
    transition: all 0.2s ease;
}

.dev-pill:hover {
    background: #6366F1;
    color: #FFFFFF;
    text-decoration: none;
}

/* Footer Container */
.nex-footer {
    margin-top: 3.5rem;
    padding: 1.8rem 1rem;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    text-align: center;
    color: #6B7280;
    font-size: 0.88rem;
}
</style>
"""

def safe_set_page_config(title: str, icon: str = "⚡", layout: str = "wide"):
    """
    Streamlit Best Practice: Set page config safely without raising
    StreamlitSetPageConfigError when navigating between pages.
    """
    try:
        st.set_page_config(page_title=title, page_icon=icon, layout=layout)
    except Exception:
        pass

def apply_custom_theme():
    """Inject custom responsive CSS styling."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

def render_developer_footer():
    """Render consistent developer branding across all pages."""
    footer_html = f"""
    <div class="nex-footer">
        <div style="margin-bottom: 0.6rem;">
            <strong style="color: #94A3B8;">{PLATFORM_NAME}</strong> &mdash; <em>{TAGLINE}</em>
        </div>
        <div style="display: flex; justify-content: center; align-items: center; gap: 12px; flex-wrap: wrap; margin-bottom: 0.8rem;">
            <span>Developer: <strong style="color: #A5B4FC;">{DEVELOPER_HANDLE}</strong></span>
            <span>&bull;</span>
            <a href="{DEVELOPER_TELEGRAM}" target="_blank" class="dev-pill">
                💬 Contact Developer ({DEVELOPER_HANDLE})
            </a>
            <span>&bull;</span>
            <span>Payments in <strong style="color: #10B981;">₹ INR</strong></span>
        </div>
        <div style="font-size: 0.78rem; color: #4B5563;">
            &copy; 2026 {PLATFORM_NAME}. Powered by Isolated Non-Root Worker Nodes. All rights reserved.
        </div>
    </div>
    """
    st.markdown(footer_html, unsafe_allow_html=True)
