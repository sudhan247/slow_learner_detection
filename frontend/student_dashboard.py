"""
Student Dashboard
Project: IDENTIFY SLOW LEARNERS FOR REMEDIAL TEACHING AND CAPACITY BUILDING FOR INNOVATIVE METHODS
Shows a student's own performance, risk level, recommendations, and improvement timeline.
"""

from __future__ import annotations
import requests
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

API_BASE = "http://localhost:5001"

RISK_COLORS = {"High Risk": "#ef4444", "Medium Risk": "#f59e0b", "Low Risk": "#06b6d4"}
PLOTLY_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#e2e8f0", family="Inter"),
    xaxis=dict(gridcolor="rgba(255,255,255,0.07)", linecolor="rgba(255,255,255,0.12)", zeroline=False),
    yaxis=dict(gridcolor="rgba(255,255,255,0.07)", linecolor="rgba(255,255,255,0.12)", zeroline=False),
)


def _auth_header() -> dict:
    return {"Authorization": f"Bearer {st.session_state.get('token', '')}"}


def _get(endpoint: str) -> dict | None:
    try:
        r = requests.get(f"{API_BASE}{endpoint}", headers=_auth_header(), timeout=6)
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None


def _post(endpoint: str, payload: dict) -> dict | None:
    try:
        r = requests.post(f"{API_BASE}{endpoint}", json=payload,
                          headers=_auth_header(), timeout=10)
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None


# ── Main render ────────────────────────────────────────────────────────────────
def render_student_dashboard() -> None:
    sid = st.session_state.get("linked_student_id", "")

    st.markdown(f"""
    <div class="page-header">
        <h1>🎓 My Dashboard</h1>
        <p>Student ID: <strong>{sid}</strong> &nbsp;|&nbsp; Personal performance overview and recommendations</p>
    </div>""", unsafe_allow_html=True)

    # Fetch student record
    data = _get(f"/students/{sid}")
    if not data or not data.get("success"):
        st.error("Could not load your profile. Ensure the API is running.")
        return

    student = data["student"]

    risk  = str(student.get("risk_level", "Unknown"))
    badge = {"High Risk": "badge-high", "Medium Risk": "badge-medium",
             "Low Risk":  "badge-low"}.get(risk, "")
    rc    = RISK_COLORS.get(risk, "#6366f1")

    # ── Profile + Radar ────────────────────────────────────────────────────────
    col1, col2 = st.columns([1, 2])

    with col1:
        att   = student.get("attendance", 0)
        avg   = student.get("average_score", 0)
        att_c = "#06b6d4" if att >= 75 else ("#f59e0b" if att >= 60 else "#ef4444")
        avg_c = "#06b6d4" if avg >= 65 else ("#f59e0b" if avg >= 50 else "#ef4444")

        st.markdown(f"""
        <div style="background:linear-gradient(135deg,rgba(99,102,241,.2),rgba(139,92,246,.12));
                    border:1px solid rgba(99,102,241,.4);border-radius:20px;padding:28px;text-align:center">
            <div style="font-size:3.5rem;margin-bottom:12px">👤</div>
            <h3 style="margin:0;color:#fff;font-size:1.2rem">{sid}</h3>
            <p style="color:rgba(255,255,255,.5);font-size:.8rem;margin:4px 0 14px">
                {st.session_state.get('username','').upper()}
            </p>
            <span class="{badge}">{risk}</span>
            <div style="margin-top:20px;text-align:left">
                <p style="color:rgba(255,255,255,.5);font-size:.75rem;margin:0 0 2px">Attendance</p>
                <p style="color:{att_c};font-size:1.5rem;font-weight:800;margin:0 0 10px">{att:.1f}%</p>
                <p style="color:rgba(255,255,255,.5);font-size:.75rem;margin:0 0 2px">Average Score</p>
                <p style="color:{avg_c};font-size:1.5rem;font-weight:800;margin:0">{avg:.1f}/100</p>
            </div>
        </div>""", unsafe_allow_html=True)

    with col2:
        cats = ["Attendance", "Assignment", "Internal", "Quiz", "Prev. Sem"]
        vals = [
            student.get("attendance", 0),
            student.get("assignment_score", 0),
            student.get("internal_marks", 0),
            student.get("quiz_score", 0),
            student.get("previous_semester_marks", 0),
        ]
        fig = go.Figure(go.Scatterpolar(
            r=vals + [vals[0]], theta=cats + [cats[0]],
            fill="toself", fillcolor="rgba(99,102,241,0.22)",
            line=dict(color="#818cf8", width=2.5),
            marker=dict(size=8, color="#a78bfa"),
        ))
        fig.update_layout(
            **PLOTLY_BASE,
            polar=dict(
                bgcolor="rgba(0,0,0,0)",
                radialaxis=dict(visible=True, range=[0, 100],
                               gridcolor="rgba(255,255,255,.1)",
                               tickfont=dict(color="rgba(255,255,255,.4)", size=9)),
                angularaxis=dict(gridcolor="rgba(255,255,255,.12)",
                                 tickfont=dict(color="white", size=11)),
            ),
            height=300, margin=dict(t=30, b=20, l=20, r=20),
            title=dict(text="Performance Radar", font=dict(color="white", size=13)),
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Score breakdown ────────────────────────────────────────────────────────
    st.markdown("#### 📊 Score Breakdown")
    labels = ["Assignment Score", "Internal Marks", "Quiz Score", "Previous Semester"]
    keys   = ["assignment_score", "internal_marks", "quiz_score", "previous_semester_marks"]
    bcols  = st.columns(4)
    for (lbl, key), bc in zip(zip(labels, keys), bcols):
        val = float(student.get(key, 0))
        clr = "#06b6d4" if val >= 70 else ("#f59e0b" if val >= 50 else "#ef4444")
        with bc:
            st.markdown(f"""
            <div style="background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);
                        border-radius:14px;padding:18px;text-align:center">
                <p style="color:rgba(255,255,255,.55);font-size:.7rem;text-transform:uppercase;
                          letter-spacing:1px;margin:0">{lbl}</p>
                <p style="color:{clr};font-size:2rem;font-weight:800;margin:6px 0">{val:.1f}</p>
                <div style="background:rgba(255,255,255,.1);border-radius:4px;height:5px;margin-top:8px">
                    <div style="background:{clr};width:{val:.1f}%;height:100%;border-radius:4px"></div>
                </div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── AI Prediction ──────────────────────────────────────────────────────────
    st.markdown("#### 🤖 AI Risk Analysis")
    with st.expander("Run AI Prediction for My Profile", expanded=False):
        if st.button("Analyse My Risk", use_container_width=True):
            payload = {
                "attendance":               student.get("attendance", 0),
                "assignment_score":         student.get("assignment_score", 0),
                "internal_marks":           student.get("internal_marks", 0),
                "quiz_score":               student.get("quiz_score", 0),
                "previous_semester_marks":  student.get("previous_semester_marks", 0),
            }
            result = _post("/predict", payload)
            if result and result.get("success"):
                pred = result["prediction"]
                recs = result["recommendations"]

                p_risk = pred["risk_level"]
                p_conf = pred["confidence"]
                p_rc   = RISK_COLORS.get(p_risk, "#6366f1")

                st.markdown(f"""
                <div style="background:linear-gradient(135deg,{p_rc}20,{p_rc}10);
                            border:2px solid {p_rc};border-radius:16px;
                            padding:22px;text-align:center;margin:12px 0">
                    <h3 style="color:{p_rc};margin:0">{p_risk}</h3>
                    <p style="color:rgba(255,255,255,.65);margin:6px 0 0">
                        Confidence: <strong style="color:#fff">{p_conf*100:.1f}%</strong>
                    </p>
                </div>""", unsafe_allow_html=True)

                st.markdown("**Detected Difficulties:**")
                for d in recs.get("difficulty_types", []):
                    st.markdown(f"- {d}")

                st.markdown("**Recommendations:**")
                for rec in recs.get("recommendations", [])[:3]:
                    with st.expander(f"📌 {rec['category']} [{rec['priority']}]",
                                     expanded=rec["priority"] == "Critical"):
                        for s in rec.get("strategies", []):
                            st.markdown(f"- {s}")
            else:
                st.error("Prediction failed. Check API status.")

    # ── Improvement history ────────────────────────────────────────────────────
    st.markdown("#### 📈 My Improvement Timeline")
    hist_data = _get(f"/improvement_history/{sid}")
    if hist_data and hist_data.get("history"):
        df_hist = pd.DataFrame(hist_data["history"])
        df_hist["timestamp"] = pd.to_datetime(df_hist["timestamp"])
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_hist["timestamp"], y=df_hist["average_score"],
            mode="lines+markers", name="Avg Score",
            line=dict(color="#818cf8", width=2.5),
            marker=dict(size=8, color="#a78bfa"),
        ))
        fig.add_trace(go.Scatter(
            x=df_hist["timestamp"], y=df_hist["attendance"],
            mode="lines+markers", name="Attendance %",
            line=dict(color="#06b6d4", width=2.5),
            marker=dict(size=8, color="#06b6d4"),
        ))
        fig.update_layout(**PLOTLY_BASE, height=280,
                          margin=dict(t=10, b=10, l=10, r=10),
                          legend=dict(font=dict(color="white", size=11)))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No improvement records yet. Faculty or admin will add records as you progress.")

    # ── Add improvement record (student-initiated) ─────────────────────────────
    with st.expander("Log a Progress Update", expanded=False):
        with st.form("improve_form"):
            ia = st.slider("Current Attendance (%)", 0, 100, int(student.get("attendance", 70)))
            is_ = st.slider("Current Average Score", 0, 100, int(student.get("average_score", 60)))
            if st.form_submit_button("Log Update", use_container_width=True):
                # Determine risk from score
                if ia < 60 or is_ < 45:  r_lv = "High Risk"
                elif ia < 75 or is_ < 60: r_lv = "Medium Risk"
                else:                      r_lv = "Low Risk"
                res = _post("/track_improvement", {
                    "student_id": sid, "attendance": ia,
                    "average_score": is_, "risk_level": r_lv,
                })
                if res and res.get("success"):
                    st.success("Progress logged!")
                    st.rerun()
                else:
                    st.error("Failed to log update.")
