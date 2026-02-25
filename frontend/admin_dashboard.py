"""
Admin Dashboard
Project: IDENTIFY SLOW LEARNERS FOR REMEDIAL TEACHING AND CAPACITY BUILDING FOR INNOVATIVE METHODS
Full system access: overview, upload, retrain, analytics, and user management.
"""

from __future__ import annotations
import os
import json
import requests
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

API_BASE    = "http://localhost:5000"
ROOT        = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RISK_COLORS = {"High Risk": "#ef4444", "Medium Risk": "#f59e0b", "Low Risk": "#06b6d4"}
PLOTLY_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#e2e8f0", family="Inter"),
    xaxis=dict(gridcolor="rgba(255,255,255,0.07)", linecolor="rgba(255,255,255,0.12)", zeroline=False),
    yaxis=dict(gridcolor="rgba(255,255,255,0.07)", linecolor="rgba(255,255,255,0.12)", zeroline=False),
)


def _auth_header() -> dict:
    return {"Authorization": f"Bearer {st.session_state.get('token', '')}"}


@st.cache_data(ttl=30, show_spinner=False)
def _get_cached(endpoint: str, token: str) -> dict | None:
    try:
        r = requests.get(f"{API_BASE}{endpoint}",
                         headers={"Authorization": f"Bearer {token}"}, timeout=6)
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None


def _post(endpoint: str, payload: dict | None = None) -> dict | None:
    try:
        r = requests.post(f"{API_BASE}{endpoint}", json=payload or {},
                          headers=_auth_header(), timeout=30)
        return r.json()
    except Exception:
        return None


def _metric(title: str, value, icon: str, card_cls: str, delta: str = "") -> None:
    delta_html = f'<p class="metric-delta">{delta}</p>' if delta else ""
    st.markdown(f"""
    <div class="metric-card {card_cls}">
        <div class="metric-icon">{icon}</div>
        <p class="metric-value">{value}</p>
        <p class="metric-label">{title}</p>
        {delta_html}
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
def render_admin_dashboard() -> None:
    st.markdown("""
    <div class="page-header">
        <h1>🔑 Admin Control Panel</h1>
        <p>Full system access — analytics, model management, uploads, and user administration</p>
    </div>""", unsafe_allow_html=True)

    # Sub-page tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview", "📈 Analytics", "📁 Data Management",
        "🤖 AI Prediction", "👥 Users"
    ])

    token = st.session_state.get("token", "")

    # ── TAB 1: Overview ────────────────────────────────────────────────────────
    with tab1:
        raw = _get_cached("/students", token)
        if not raw or not raw.get("success"):
            st.error("Cannot load student data.")
            return

        df    = pd.DataFrame(raw["students"])
        total = len(df)
        vc    = df["risk_level"].value_counts() if "risk_level" in df.columns else pd.Series()
        high   = int(vc.get("High Risk",   0))
        medium = int(vc.get("Medium Risk", 0))
        low    = int(vc.get("Low Risk",    0))

        c1, c2, c3, c4 = st.columns(4)
        with c1: _metric("Total Students",  f"{total:,}", "👥", "card-total")
        with c2: _metric("High Risk",        high,        "🔴", "card-high pulse",
                         f"{high/total*100:.1f}% of class" if total else "")
        with c3: _metric("Medium Risk",      medium,      "🟡", "card-medium")
        with c4: _metric("Low Risk",         low,         "🟢", "card-low")

        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2 = st.columns([1, 1.6])

        with col1:
            st.markdown("#### 🎯 Risk Distribution")
            fig = go.Figure(go.Pie(
                labels=["High Risk", "Medium Risk", "Low Risk"],
                values=[high, medium, low], hole=0.62,
                marker=dict(colors=["#ef4444", "#f59e0b", "#06b6d4"],
                            line=dict(color="rgba(0,0,0,0)", width=0)),
                textinfo="label+percent", textfont=dict(size=11, color="white"),
            ))
            fig.add_annotation(
                text=f"<b>{total}</b><br><span style='font-size:11px;opacity:.7'>Students</span>",
                x=0.5, y=0.5, showarrow=False, font=dict(size=18, color="white"),
            )
            fig.update_layout(**PLOTLY_BASE, height=300,
                              showlegend=True,
                              legend=dict(orientation="h", yanchor="bottom", y=-0.2,
                                          xanchor="center", x=0.5,
                                          font=dict(color="white", size=11)),
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

        # Scatter + Histogram
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 🔗 Attendance vs Average Score")
            if {"attendance", "average_score", "risk_level"}.issubset(df.columns):
                fig = px.scatter(
                    df.sample(min(300, len(df)), random_state=42),
                    x="attendance", y="average_score",
                    color="risk_level", color_discrete_map=RISK_COLORS,
                    opacity=0.7, trendline="lowess",
                )
                fig.add_vline(x=75, line_dash="dash", line_color="rgba(255,255,255,.3)",
                              annotation_text="75% Threshold",
                              annotation_font_color="rgba(255,255,255,.5)")
                fig.update_layout(**PLOTLY_BASE, height=300,
                                  margin=dict(t=5, b=10, l=5, r=5),
                                  legend=dict(font=dict(color="white", size=11)),
                                  xaxis_title="Attendance (%)", yaxis_title="Average Score")
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("#### 📉 Score Distribution")
            if {"average_score", "risk_level"}.issubset(df.columns):
                fig = go.Figure()
                for risk in ["High Risk", "Medium Risk", "Low Risk"]:
                    vals = df[df["risk_level"] == risk]["average_score"]
                    if not vals.empty:
                        fig.add_trace(go.Histogram(
                            x=vals, name=risk, nbinsx=20, opacity=0.75,
                            marker_color=RISK_COLORS.get(risk, "#6366f1"),
                        ))
                fig.update_layout(**PLOTLY_BASE, barmode="overlay", height=300,
                                  margin=dict(t=5, b=10, l=5, r=5),
                                  legend=dict(font=dict(color="white", size=11)),
                                  xaxis_title="Average Score", yaxis_title="Count")
                st.plotly_chart(fig, use_container_width=True)

        # Full table
        st.markdown("#### 📋 All Student Records")
        show = ["student_id", "faculty_id", "attendance", "assignment_score",
                "internal_marks", "quiz_score", "average_score", "risk_level"]
        show = [c for c in show if c in df.columns]
        st.dataframe(_style_risk(df[show].reset_index(drop=True)),
                     use_container_width=True, height=350)
        st.download_button("📥 Download Full Dataset",
                           df.to_csv(index=False), "all_students.csv",
                           "text/csv", use_container_width=True)

    # ── TAB 2: Analytics ───────────────────────────────────────────────────────
    with tab2:
        st.markdown("### 🤖 Model Performance Metrics")
        metrics_path = os.path.join(ROOT, "models", "metrics.json")
        if os.path.exists(metrics_path):
            with open(metrics_path) as f:
                m = json.load(f)

            mc = st.columns(4)
            for col, (name, key, icon) in zip(mc, [
                ("Accuracy",  "accuracy",  "🎯"),
                ("Precision", "precision", "📌"),
                ("Recall",    "recall",    "🔍"),
                ("F1-Score",  "f1_score",  "⚖️"),
            ]):
                val = m.get(key, 0)
                clr = "#06b6d4" if val >= 0.85 else ("#f59e0b" if val >= 0.70 else "#ef4444")
                with col:
                    st.markdown(f"""
                    <div style="background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);
                                border-radius:14px;padding:22px;text-align:center">
                        <div style="font-size:1.6rem">{icon}</div>
                        <p style="color:{clr};font-size:2rem;font-weight:800;margin:6px 0">{val*100:.1f}%</p>
                        <p style="color:rgba(255,255,255,.6);font-size:.8rem;margin:0">{name}</p>
                    </div>""", unsafe_allow_html=True)

            cv = m.get("cv_mean", 0)
            st.info(f"**5-Fold Cross-Validation Accuracy:** {cv*100:.2f}%")
        else:
            st.warning("Model not trained. Go to Data Management to retrain.")

        # Feature Importance + Confusion Matrix
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### 🏆 Feature Importance")
            fi_img = os.path.join(ROOT, "static", "feature_importance.png")
            if os.path.exists(fi_img):
                st.image(fi_img, use_column_width=True)
            else:
                st.info("Train the model to generate this chart.")

        with c2:
            st.markdown("### 📊 Confusion Matrix")
            cm_img = os.path.join(ROOT, "static", "confusion_matrix.png")
            if os.path.exists(cm_img):
                st.image(cm_img, use_column_width=True)
            else:
                st.info("Train the model to generate this chart.")

        # Correlation heatmap
        raw2 = _get_cached("/students", token)
        if raw2 and raw2.get("success"):
            df2 = pd.DataFrame(raw2["students"])
            num_cols = ["attendance", "assignment_score", "internal_marks", "quiz_score",
                        "previous_semester_marks", "average_score", "performance_drop", "score_variance"]
            num_cols = [c for c in num_cols if c in df2.columns]
            if len(num_cols) > 2:
                st.markdown("#### 🌡️ Feature Correlation Heatmap")
                corr = df2[num_cols].corr()
                fig  = px.imshow(corr, color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
                                 aspect="auto", text_auto=".2f")
                fig.update_layout(**PLOTLY_BASE, height=460,
                                  margin=dict(t=10, b=10, l=10, r=10),
                                  coloraxis_colorbar=dict(tickfont=dict(color="white")))
                st.plotly_chart(fig, use_container_width=True)

            # Box + Violin
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("#### Score Variance by Risk Level")
                if {"score_variance", "risk_level"}.issubset(df2.columns):
                    fig = px.box(df2, x="risk_level", y="score_variance",
                                 color="risk_level", color_discrete_map=RISK_COLORS, points="outliers")
                    fig.update_layout(**PLOTLY_BASE, height=300, showlegend=False,
                                      margin=dict(t=5, b=10, l=5, r=5))
                    st.plotly_chart(fig, use_container_width=True)
            with c2:
                st.markdown("#### Performance Drop Distribution")
                if {"performance_drop", "risk_level"}.issubset(df2.columns):
                    fig = px.violin(df2, x="risk_level", y="performance_drop",
                                    color="risk_level", color_discrete_map=RISK_COLORS,
                                    box=True, points="outliers")
                    fig.update_layout(**PLOTLY_BASE, height=300, showlegend=False,
                                      margin=dict(t=5, b=10, l=5, r=5))
                    st.plotly_chart(fig, use_container_width=True)

    # ── TAB 3: Data Management ─────────────────────────────────────────────────
    with tab3:
        st.markdown("### 📁 Dataset Upload")
        uploaded = st.file_uploader("Upload student CSV file", type=["csv"])
        if uploaded:
            if st.button("Upload & Load into Database", use_container_width=True):
                with st.spinner("Uploading…"):
                    try:
                        r = requests.post(
                            f"{API_BASE}/upload_data",
                            files={"file": (uploaded.name, uploaded.getvalue(), "text/csv")},
                            headers=_auth_header(), timeout=20,
                        )
                        if r.status_code == 200:
                            st.success("Dataset uploaded and loaded into database.")
                            st.cache_data.clear()
                        else:
                            st.error(r.json().get("error", "Upload failed."))
                    except Exception as exc:
                        st.error(f"Upload error: {exc}")

        st.markdown("---")
        st.markdown("### 🤖 Model Retraining")
        st.markdown("""
        <div class="info-box">
            <p style="color:rgba(255,255,255,.7);font-size:.85rem;margin:0">
                Click below to retrain the Random Forest classifier on the current dataset.
                This will update the model and regenerate feature importance and confusion matrix plots.
            </p>
        </div>""", unsafe_allow_html=True)

        if st.button("Retrain Model Now", use_container_width=True):
            with st.spinner("Training in progress — this may take 30-60 seconds…"):
                result = _post("/retrain")
            if result and result.get("success"):
                m = result.get("metrics", {})
                st.success("Model retrained successfully!")
                mc2 = st.columns(4)
                for col2, (name, key) in zip(mc2, [
                    ("Accuracy", "accuracy"), ("Precision", "precision"),
                    ("Recall", "recall"), ("F1", "f1_score"),
                ]):
                    with col2:
                        st.metric(name, f"{m.get(key, 0)*100:.1f}%")
                st.cache_data.clear()
            else:
                err = result.get("error", "Unknown error") if result else "API not reachable"
                st.error(f"Retraining failed: {err}")

        st.markdown("---")
        st.markdown("### 📥 Export Reports")
        raw3 = _get_cached("/students", token)
        if raw3 and raw3.get("success"):
            df3 = pd.DataFrame(raw3["students"])
            c1, c2 = st.columns(2)
            with c1:
                st.download_button("📊 Download Full Dataset (CSV)",
                                   df3.to_csv(index=False), "all_students.csv",
                                   "text/csv", use_container_width=True)
            with c2:
                if "risk_level" in df3.columns:
                    hr = df3[df3["risk_level"] == "High Risk"]
                    if not hr.empty:
                        st.download_button("🚨 Download High Risk Report (CSV)",
                                           hr.to_csv(index=False), "high_risk_students.csv",
                                           "text/csv", use_container_width=True)

    # ── TAB 4: AI Prediction ───────────────────────────────────────────────────
    with tab4:
        st.markdown("### 🤖 AI Risk Prediction Engine")

        col1, col2 = st.columns([1, 1.2])
        with col1:
            st.markdown("""
            <div class="info-box">
                <p style="color:rgba(255,255,255,.7);font-size:.85rem;margin:0">
                    Enter student data to get instant AI risk prediction and personalised recommendations.
                </p>
            </div>""", unsafe_allow_html=True)
            with st.form("admin_predict"):
                sid_input = st.text_input("Student ID (optional)", placeholder="STU0001")
                att  = st.slider("Attendance (%)",             0, 100, 72)
                asgn = st.slider("Assignment Score",           0, 100, 65)
                intm = st.slider("Internal Marks",             0, 100, 60)
                quiz = st.slider("Quiz Score",                 0, 100, 62)
                prev = st.slider("Previous Semester Marks",    0, 100, 65)
                go_btn = st.form_submit_button("Predict Risk Level", use_container_width=True)

        with col2:
            if go_btn:
                payload = {
                    "attendance": att, "assignment_score": asgn,
                    "internal_marks": intm, "quiz_score": quiz,
                    "previous_semester_marks": prev,
                }
                if sid_input.strip():
                    payload["student_id"] = sid_input.strip()

                result = _post("/predict", payload)
                if result and result.get("success"):
                    pred = result["prediction"]
                    recs = result["recommendations"]
                    risk = pred["risk_level"]
                    conf = pred["confidence"]
                    rc   = RISK_COLORS.get(risk, "#6366f1")

                    st.markdown(f"""
                    <div style="background:linear-gradient(135deg,{rc}22,{rc}10);
                                border:2px solid {rc};border-radius:18px;
                                padding:26px;text-align:center;margin-bottom:16px">
                        <h2 style="color:{rc};margin:0">{risk}</h2>
                        <p style="color:rgba(255,255,255,.65);margin:8px 0 0">
                            Confidence: <strong style="color:#fff">{conf*100:.1f}%</strong>
                        </p>
                    </div>""", unsafe_allow_html=True)

                    for cls, prob in sorted(pred["class_probabilities"].items(),
                                            key=lambda x: x[1], reverse=True):
                        clr = RISK_COLORS.get(cls, "#6366f1")
                        st.markdown(f"""
                        <div style="margin:8px 0">
                            <div style="display:flex;justify-content:space-between;margin-bottom:4px">
                                <span style="color:{clr};font-size:.85rem">{cls}</span>
                                <span style="color:#fff;font-weight:700">{prob*100:.1f}%</span>
                            </div>
                            <div style="background:rgba(255,255,255,.1);border-radius:5px;height:8px">
                                <div style="background:{clr};width:{prob*100:.1f}%;height:100%;border-radius:5px"></div>
                            </div>
                        </div>""", unsafe_allow_html=True)

                    st.markdown("**Detected Difficulties:** " +
                                " | ".join(recs.get("difficulty_types", [])))
                    for rec in recs.get("recommendations", [])[:3]:
                        with st.expander(f"📌 {rec['category']} [{rec['priority']}]",
                                         expanded=rec["priority"] == "Critical"):
                            for s in rec.get("strategies", []):
                                st.markdown(f"- {s}")
                else:
                    st.error("Prediction failed.")
            else:
                st.markdown("""
                <div style="text-align:center;padding:60px 20px;
                            background:rgba(255,255,255,.03);
                            border:2px dashed rgba(255,255,255,.12);border-radius:18px">
                    <div style="font-size:4rem;margin-bottom:16px">🤖</div>
                    <h3 style="color:rgba(255,255,255,.5)">Awaiting Input</h3>
                    <p style="color:rgba(255,255,255,.3);font-size:.85rem">
                        Fill in the form and click "Predict Risk Level"
                    </p>
                </div>""", unsafe_allow_html=True)

    # ── TAB 5: Users ───────────────────────────────────────────────────────────
    with tab5:
        st.markdown("### 👥 Registered Users")
        users_data = _get_cached("/users", token)
        if users_data and users_data.get("success"):
            users_df = pd.DataFrame(users_data["users"])
            if not users_df.empty:
                # Colour roles
                def _role_color(val):
                    m = {"admin":   "background-color:rgba(99,102,241,.3);color:#818cf8;font-weight:700",
                         "faculty": "background-color:rgba(6,182,212,.25);color:#06b6d4;font-weight:700",
                         "student": "background-color:rgba(245,158,11,.25);color:#fbbf24;font-weight:700"}
                    return m.get(val, "")

                styled_users = users_df.style.applymap(_role_color, subset=["role"])
                st.dataframe(styled_users, use_container_width=True, height=450)

                # Summary chips
                role_counts = users_df["role"].value_counts()
                uc = st.columns(3)
                for col3, (r, icon, clr) in zip(uc, [
                    ("admin",   "🔑", "#818cf8"),
                    ("faculty", "👩‍🏫", "#06b6d4"),
                    ("student", "🎓", "#f59e0b"),
                ]):
                    with col3:
                        cnt = int(role_counts.get(r, 0))
                        st.markdown(f"""
                        <div style="background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);
                                    border-radius:12px;padding:16px;text-align:center">
                            <div style="font-size:1.8rem">{icon}</div>
                            <p style="color:{clr};font-size:1.5rem;font-weight:800;margin:4px 0">{cnt}</p>
                            <p style="color:rgba(255,255,255,.5);font-size:.75rem;text-transform:uppercase;
                                      letter-spacing:1px;margin:0">{r.title()} Accounts</p>
                        </div>""", unsafe_allow_html=True)
        else:
            st.error("Could not fetch user list.")
