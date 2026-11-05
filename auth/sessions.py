"""
NEXHOST CLOUD - Session State Management for Streamlit Multi-Page Architecture
Author: @Harsh_54x
"""

from typing import Optional, Dict, Any
import streamlit as st
from database.users import User, UserRepository
from database.memberships import MembershipRepository

def init_session():
    """Ensure baseline session variables exist."""
    defaults = {
        "is_authenticated": False,
        "user_id": None,
        "username": None,
        "email": None,
        "role": "free_user",
        "current_project_id": None,
        "theme": "dark",
        "toast_msg": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

def set_login_session(user: User):
    """Store authenticated user details in session."""
    st.session_state["is_authenticated"] = True
    st.session_state["user_id"] = user.id
    st.session_state["username"] = user.username
    st.session_state["email"] = user.email
    st.session_state["role"] = user.role
    st.session_state["full_name"] = user.full_name or user.username

def clear_session():
    """Wipe authentication details from session state."""
    st.session_state["is_authenticated"] = False
    st.session_state["user_id"] = None
    st.session_state["username"] = None
    st.session_state["email"] = None
    st.session_state["role"] = "free_user"
    st.session_state["current_project_id"] = None

def get_current_user() -> Optional[User]:
    """Retrieve full fresh user entity from database."""
    init_session()
    user_id = st.session_state.get("user_id")
    if not user_id:
        return None
    return UserRepository.get_by_id(user_id)

def is_logged_in() -> bool:
    """Check if active session is authenticated."""
    init_session()
    return bool(st.session_state.get("is_authenticated") and st.session_state.get("user_id"))

def get_user_role() -> str:
    """Return user role."""
    init_session()
    return st.session_state.get("role", "free_user")
