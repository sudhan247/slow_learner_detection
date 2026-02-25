"""
Main Entry Point — Router
Project: IDENTIFY SLOW LEARNERS FOR REMEDIAL TEACHING AND CAPACITY BUILDING FOR INNOVATIVE METHODS
Handles page config, CSS injection, sidebar, and role-based routing.
"""

from __future__ import annotations
import os
import sys

import streamlit as st

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PAGE CONFIG — must be the very first Streamlit call
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.set_page_config(
    page_title="EduAI | Slow Learner Detection System",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

from frontend.styles            import MAIN_CSS
from frontend.login             import render_login_page
from frontend.student_dashboard import render_student_dashboard
from frontend.faculty_dashboard import render_faculty_dashboard
from frontend.admin_dashboard   import render_admin_dashboard

# Inject global CSS
st.markdown(MAIN_CSS, unsafe_allow_html=True)


# ── Session state defaults ─────────────────────────────────────────────────────
def _init_session() -> None:
    defaults = {
        "logged_in":         False,
        "token":             "",
        "role":              "",
        "username":          "",
        "user_id":           None,
        "linked_student_id": None,
        "linked_faculty_id": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ── Sidebar ────────────────────────────────────────────────────────────────────
def _render_sidebar() -> None:
    role     = st.session_state.get("role", "")
    username = st.session_state.get("username", "")

    ROLE_ICONS = {"admin": "🔑", "faculty": "👩‍🏫", "student": "🎓"}
    ROLE_COLORS = {"admin": "#818cf8", "faculty": "#06b6d4", "student": "#f59e0b"}

    with st.sidebar:
        # Logo
        st.markdown("""
        <div style="text-align:center;padding:24px 16px 18px;
                    border-bottom:1px solid rgba(167,139,250,.2);margin-bottom:10px">
            <div style="font-size:3rem">🎓</div>
            <div class="gradient-title">EduAI Analytics</div>
            <p style="color:rgba(255,255,255,.4);font-size:.7rem;margin-top:6px;line-height:1.4">
                Slow Learner Detection &amp;<br>Remedial Teaching System
            </p>
        </div>""", unsafe_allow_html=True)

        if st.session_state.logged_in:
            icon  = ROLE_ICONS.get(role, "👤")
            color = ROLE_COLORS.get(role, "#818cf8")

            st.markdown(f"""
            <div style="background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.12);
                        border-radius:12px;padding:14px;margin:10px 0">
                <div style="display:flex;align-items:center;gap:10px">
                    <div style="font-size:1.6rem">{icon}</div>
                    <div>
                        <p style="color:#fff;font-weight:700;margin:0;font-size:.9rem">{username}</p>
                        <p style="color:{color};font-size:.72rem;text-transform:uppercase;
                                  letter-spacing:1px;margin:0;font-weight:600">{role}</p>
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

            st.markdown('<div style="height:1px;background:rgba(167,139,250,.2);margin:12px 0"></div>',
                        unsafe_allow_html=True)

            # Role-specific info
            if role == "student":
                sid = st.session_state.get("linked_student_id", "")
                st.markdown(f"""
                <div style="padding:10px;background:rgba(245,158,11,.1);border-radius:10px;margin:8px 0">
                    <p style="color:rgba(255,255,255,.5);font-size:.7rem;text-transform:uppercase;
                              letter-spacing:1px;margin:0">Student ID</p>
                    <p style="color:#f59e0b;font-weight:700;font-size:.95rem;margin:2px 0">{sid}</p>
                </div>""", unsafe_allow_html=True)
            elif role == "faculty":
                fid = st.session_state.get("linked_faculty_id", "")
                st.markdown(f"""
                <div style="padding:10px;background:rgba(6,182,212,.1);border-radius:10px;margin:8px 0">
                    <p style="color:rgba(255,255,255,.5);font-size:.7rem;text-transform:uppercase;
                              letter-spacing:1px;margin:0">Faculty ID</p>
                    <p style="color:#06b6d4;font-weight:700;font-size:.95rem;margin:2px 0">{fid}</p>
                </div>""", unsafe_allow_html=True)

            st.markdown('<div style="height:1px;background:rgba(167,139,250,.2);margin:12px 0"></div>',
                        unsafe_allow_html=True)

            # Logout
            if st.button("Logout", use_container_width=True):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

        # System status
        st.markdown('<p class="section-title">System Status</p>', unsafe_allow_html=True)
        try:
            import requests
            r = requests.get("http://localhost:5000/health", timeout=2)
            if r.status_code == 200:
                st.success("Flask API — Online")
            else:
                st.error("Flask API — Error")
        except Exception:
            st.warning("Flask API — Offline")

        import os as _os
        model_ok = _os.path.exists(_os.path.join(ROOT, "models", "random_forest_model.pkl"))
        if model_ok:
            st.success("ML Model — Loaded")
        else:
            st.error("ML Model — Not Trained")

        st.markdown("""
        <div style="text-align:center;opacity:.35;font-size:.68rem;padding:16px 0 8px">
            <p style="margin:2px 0">EduAI v2.0 — Role-Based Auth</p>
            <p style="margin:2px 0">Final Year Project</p>
        </div>""", unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN ROUTER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def main() -> None:
    _init_session()
    _render_sidebar()

    if not st.session_state.logged_in:
        render_login_page()
        return

    role = st.session_state.get("role", "")
    if role == "student":
        render_student_dashboard()
    elif role == "faculty":
        render_faculty_dashboard()
    elif role == "admin":
        render_admin_dashboard()
    else:
        st.error(f"Unknown role: '{role}'. Please log out and log in again.")


if __name__ == "__main__":
    main()
