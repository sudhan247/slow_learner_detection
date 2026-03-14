"""
Login Page
Project: IDENTIFY SLOW LEARNERS FOR REMEDIAL TEACHING AND CAPACITY BUILDING FOR INNOVATIVE METHODS
Modern login UI with role-based authentication.
"""

from __future__ import annotations
import requests
import streamlit as st

API_BASE = "http://localhost:5001"


def render_login_page() -> None:
    """Render the login form. On success, populate st.session_state."""

    # Centre the card with spacer columns
    _, mid, _ = st.columns([1, 2, 1])

    with mid:
        st.markdown("""
        <div style="text-align:center;padding:30px 0 10px">
            <div style="font-size:4rem">🎓</div>
            <div class="gradient-title" style="font-size:1.8rem">EduAI Analytics</div>
            <p style="color:rgba(255,255,255,.45);font-size:.85rem;margin-top:6px">
                IDENTIFY SLOW LEARNERS FOR REMEDIAL TEACHING<br>
                AND CAPACITY BUILDING FOR INNOVATIVE METHODS
            </p>
        </div>""", unsafe_allow_html=True)

        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.markdown('<p class="login-title">Sign In</p>', unsafe_allow_html=True)
        st.markdown('<p class="login-sub">Enter your credentials to access your dashboard</p>',
                    unsafe_allow_html=True)

        with st.form("login_form", clear_on_submit=False):
            role = st.selectbox(
                "Login As",
                ["Admin", "Faculty", "Student"],
                help="Select your role to see the appropriate dashboard",
            )
            username = st.text_input(
                "Username",
                placeholder="admin / faculty1 / stu0001",
            )
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
            )
            submitted = st.form_submit_button("Sign In", use_container_width=True)

        if submitted:
            if not username.strip() or not password.strip():
                st.error("Username and password are required.")
            else:
                _do_login(username.strip(), password.strip())

        st.markdown('</div>', unsafe_allow_html=True)

        # Demo credentials card
        st.markdown("""
        <div style="background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.1);
                    border-radius:16px;padding:20px;margin-top:20px">
            <p style="color:#a78bfa;font-size:.75rem;text-transform:uppercase;
                      letter-spacing:1.5px;margin:0 0 12px;font-weight:700">
                Demo Credentials
            </p>
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px">
                <div style="background:rgba(99,102,241,.2);border-radius:10px;padding:12px;text-align:center">
                    <div style="font-size:1.4rem">🔑</div>
                    <p style="color:#818cf8;font-size:.75rem;font-weight:700;margin:4px 0 2px">ADMIN</p>
                    <p style="color:rgba(255,255,255,.6);font-size:.7rem;margin:0">admin / admin123</p>
                </div>
                <div style="background:rgba(6,182,212,.15);border-radius:10px;padding:12px;text-align:center">
                    <div style="font-size:1.4rem">👩‍🏫</div>
                    <p style="color:#06b6d4;font-size:.75rem;font-weight:700;margin:4px 0 2px">FACULTY</p>
                    <p style="color:rgba(255,255,255,.6);font-size:.7rem;margin:0">faculty1 / faculty123</p>
                </div>
                <div style="background:rgba(245,158,11,.15);border-radius:10px;padding:12px;text-align:center">
                    <div style="font-size:1.4rem">🎓</div>
                    <p style="color:#f59e0b;font-size:.75rem;font-weight:700;margin:4px 0 2px">STUDENT</p>
                    <p style="color:rgba(255,255,255,.6);font-size:.7rem;margin:0">stu0001 / student123</p>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)


def _do_login(username: str, password: str) -> None:
    """Call /login endpoint and populate session_state on success."""
    try:
        resp = requests.post(
            f"{API_BASE}/login",
            json={"username": username, "password": password},
            timeout=6,
        )
        if resp.status_code == 200:
            data = resp.json()
            st.session_state.logged_in         = True
            st.session_state.token             = data["token"]
            st.session_state.role              = data["role"]
            st.session_state.username          = data["username"]
            st.session_state.user_id           = data["user_id"]
            st.session_state.linked_student_id = data.get("linked_student_id")
            st.session_state.linked_faculty_id = data.get("linked_faculty_id")
            st.success(f"Welcome, {data['username']}!")
            st.rerun()
        elif resp.status_code == 401:
            st.error("Invalid username or password. Please try again.")
        else:
            st.error(f"Login failed: {resp.json().get('error','Unknown error')}")
    except requests.exceptions.ConnectionError:
        st.error("Cannot reach the API server. Make sure Flask is running: `python run_backend.py`")
    except Exception as exc:
        st.error(f"Login error: {exc}")
