"""
Faculty Dashboard
Project: IDENTIFY SLOW LEARNERS FOR REMEDIAL TEACHING AND CAPACITY BUILDING FOR INNOVATIVE METHODS
Shows assigned students, risk distribution, high-risk alerts, and individual analysis.
"""

from __future__ import annotations
import requests
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

API_BASE    = "http://localhost:5000"
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


def _metric(title: str, value, icon: str, card_cls: str) -> None:
    st.markdown(f"""
    <div class="metric-card {card_cls}">
        <div class="metric-icon">{icon}</div>
        <p class="metric-value">{value}</p>
        <p class="metric-label">{title}</p>
    </div>""", unsafe_allow_html=True)


def _style_risk(df: pd.DataFrame):
    def _c(v):
        m = {"High Risk": "background-color:rgba(239,68,68,.22);color:#ef4444;font-weight:700",
             "Medium Risk":"background-color:rgba(245,158,11,.22);color:#fbbf24;font-weight:700",
             "Low Risk":   "background-color:rgba(6,182,212,.22);color:#06b6d4;font-weight:700"}
        return m.get(v, "")
    styled = df.style
    if "risk_level" in df.columns:
        styled = styled.applymap(_c, subset=["risk_level"])
    return styled


# ── Main render ────────────────────────────────────────────────────────────────
def render_faculty_dashboard() -> None:
    fid      = st.session_state.get("linked_faculty_id", "")
    username = st.session_state.get("username", "Faculty")

    st.markdown(f"""
    <div class="page-header">
        <h1>👩‍🏫 Faculty Dashboard</h1>
        <p>Welcome, <strong>{username}</strong> &nbsp;|&nbsp;
           Faculty ID: <strong>{fid}</strong> &nbsp;|&nbsp; Class analytics and student monitoring</p>
    </div>""", unsafe_allow_html=True)

    # ── Load assigned students ─────────────────────────────────────────────────
    raw = _get("/students")
    if not raw or not raw.get("success"):
        st.error("Cannot load student data. Ensure the API is running.")
        return

    df = pd.DataFrame(raw["students"])
    if df.empty:
        st.warning("No students assigned to your faculty ID yet.")
        return

    total = len(df)
    vc    = df["risk_level"].value_counts() if "risk_level" in df.columns else pd.Series()
    high   = int(vc.get("High Risk",   0))
    medium = int(vc.get("Medium Risk", 0))
    low    = int(vc.get("Low Risk",    0))

    # ── Metric cards ───────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    with c1: _metric("Assigned Students", total,  "👥", "card-total")
    with c2: _metric("High Risk",         high,   "🔴", "card-high pulse")
    with c3: _metric("Medium Risk",       medium, "🟡", "card-medium")
    with c4: _metric("Low Risk",          low,    "🟢", "card-low")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts ─────────────────────────────────────────────────────────────────
    col1, col2 = st.columns([1, 1.6])

    with col1:
        st.markdown("#### 🎯 Risk Distribution")
        fig = go.Figure(go.Pie(
            labels=["High Risk", "Medium Risk", "Low Risk"],
            values=[high, medium, low], hole=0.62,
            marker=dict(colors=["#ef4444", "#f59e0b", "#06b6d4"],
                        line=dict(color="rgba(0,0,0,0)", width=0)),
            textinfo="label+percent",
            textfont=dict(size=11, color="white"),
        ))
        fig.add_annotation(
            text=f"<b>{total}</b><br><span style='font-size:11px;opacity:.7'>Students</span>",
            x=0.5, y=0.5, showarrow=False, font=dict(size=18, color="white")
        )
        fig.update_layout(**PLOTLY_BASE, height=300,
                          showlegend=True,
                          legend=dict(orientation="h", yanchor="bottom", y=-0.2,
                                      xanchor="center", x=0.5, font=dict(color="white", size=11)),
                          margin=dict(t=5, b=45, l=5, r=5))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### 📊 Average Scores by Risk Level")
        scols = ["attendance", "assignment_score", "internal_marks", "quiz_score", "average_score"]
        scols = [c for c in scols if c in df.columns]
        if scols and "risk_level" in df.columns:
            avg_df = df.groupby("risk_level")[scols].mean().reset_index()
            fig    = go.Figure()
            for risk in ["High Risk", "Medium Risk", "Low Risk"]:
                row = avg_df[avg_df["risk_level"] == risk]
                if not row.empty:
                    fig.add_trace(go.Bar(
                        name=risk, opacity=0.88,
                        x=[c.replace("_", " ").title() for c in scols],
                        y=[row.iloc[0][c] for c in scols],
                        marker_color=RISK_COLORS.get(risk, "#6366f1"),
                    ))
            fig.update_layout(**PLOTLY_BASE, barmode="group", height=300,
                              legend=dict(font=dict(color="white", size=11)),
                              margin=dict(t=5, b=10, l=5, r=5),
                              yaxis_title="Average Score")
            st.plotly_chart(fig, use_container_width=True)

    # ── High-risk alerts ───────────────────────────────────────────────────────
    st.markdown("#### 🚨 High Risk Students — Immediate Attention Required")
    if "risk_level" in df.columns:
        hr_df = df[df["risk_level"] == "High Risk"].copy()
        if not hr_df.empty:
            def _diff(row):
                d = []
                if row.get("attendance", 100) < 60:      d.append("Attendance")
                if row.get("internal_marks", 100) < 50:  d.append("Conceptual")
                if row.get("assignment_score", 100) < 50: d.append("Practice")
                if abs(row.get("performance_drop", 0)) > 15: d.append("Fluctuation")
                return ", ".join(d) or "General"
            hr_df["Difficulty"] = hr_df.apply(_diff, axis=1)
            show = ["student_id", "attendance", "assignment_score",
                    "internal_marks", "quiz_score", "average_score", "Difficulty"]
            show = [c for c in show if c in hr_df.columns]
            st.dataframe(
                hr_df[show].sort_values("average_score").style.background_gradient(
                    subset=["average_score"] if "average_score" in show else [],
                    cmap="RdYlGn",
                ),
                use_container_width=True, height=300,
            )
        else:
            st.success("No high-risk students in your class.")

    # ── Attendance vs Score scatter ─────────────────────────────────────────────
    st.markdown("#### 🔗 Attendance vs Average Score")
    if {"attendance", "average_score", "risk_level"}.issubset(df.columns):
        fig = px.scatter(
            df.sample(min(250, len(df)), random_state=42),
            x="attendance", y="average_score",
            color="risk_level", color_discrete_map=RISK_COLORS,
            opacity=0.7, trendline="lowess",
            hover_data=["student_id"] if "student_id" in df.columns else None,
        )
        fig.add_vline(x=75, line_dash="dash", line_color="rgba(255,255,255,.3)",
                      annotation_text="75% Threshold",
                      annotation_font_color="rgba(255,255,255,.5)")
        fig.update_layout(**PLOTLY_BASE, height=320,
                          margin=dict(t=5, b=10, l=5, r=5),
                          legend=dict(font=dict(color="white", size=11)),
                          xaxis_title="Attendance (%)", yaxis_title="Average Score")
        st.plotly_chart(fig, use_container_width=True)

    # ── Individual student lookup ───────────────────────────────────────────────
    st.markdown("#### 🔍 Individual Student Lookup")
    if "student_id" in df.columns:
        selected_sid = st.selectbox(
            "Select a Student",
            ["— select —"] + sorted(df["student_id"].tolist()),
        )
        if selected_sid != "— select —":
            s = df[df["student_id"] == selected_sid].iloc[0]
            risk  = str(s.get("risk_level", "Unknown"))
            badge = {"High Risk": "badge-high", "Medium Risk": "badge-medium",
                     "Low Risk":  "badge-low"}.get(risk, "")
            st.markdown(f"""
            <div style="background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);
                        border-radius:16px;padding:22px;margin-top:10px">
                <div style="display:flex;align-items:center;gap:14px;margin-bottom:16px">
                    <div style="font-size:2rem">👤</div>
                    <div>
                        <h4 style="margin:0;color:#fff">{selected_sid}</h4>
                        <span class="{badge}">{risk}</span>
                    </div>
                </div>
                <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px">
                    {"".join(f'''<div style="text-align:center">
                        <p style="color:rgba(255,255,255,.5);font-size:.7rem;text-transform:uppercase;margin:0">{lbl}</p>
                        <p style="color:#818cf8;font-size:1.3rem;font-weight:700;margin:4px 0">{s.get(key,0):.1f}</p>
                    </div>''' for lbl, key in [
                        ("Attendance",   "attendance"),
                        ("Assignment",   "assignment_score"),
                        ("Internal",     "internal_marks"),
                        ("Quiz",         "quiz_score"),
                    ])}
                </div>
            </div>""", unsafe_allow_html=True)

    # ── Full class table ────────────────────────────────────────────────────────
    st.markdown("#### 📋 Full Class List")
    show = ["student_id", "attendance", "assignment_score", "internal_marks",
            "quiz_score", "average_score", "performance_drop", "risk_level"]
    show = [c for c in show if c in df.columns]
    st.dataframe(_style_risk(df[show].reset_index(drop=True)),
                 use_container_width=True, height=380)

    # CSV export
    st.download_button("📥 Export Class CSV", df.to_csv(index=False),
                       "my_class.csv", "text/csv", use_container_width=True)
