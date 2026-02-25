"""
Shared CSS styles
Project: IDENTIFY SLOW LEARNERS FOR REMEDIAL TEACHING AND CAPACITY BUILDING FOR INNOVATIVE METHODS
"""

MAIN_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }

/* ── App background ── */
.stApp {
    background: linear-gradient(135deg, #0a0a1a 0%, #0d1b3e 50%, #0a0a1a 100%);
    background-attachment: fixed;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1117 0%, #161b27 60%, #0d1f3c 100%);
    border-right: 1px solid rgba(99,102,241,0.25);
}

/* ── Page header ── */
.page-header {
    background: linear-gradient(90deg,#4f46e5 0%,#7c3aed 60%,#a855f7 100%);
    padding: 22px 28px; border-radius: 18px; margin-bottom: 22px; color:#fff;
    box-shadow: 0 12px 35px rgba(79,70,229,.4);
}
.page-header h1 { margin:0; font-size:1.75rem; font-weight:800; }
.page-header p  { margin:4px 0 0; opacity:.82; font-size:.9rem; }

/* ── Metric cards ── */
.metric-card {
    border-radius:18px; padding:22px 20px; margin:6px 0;
    transition: transform .25s ease, box-shadow .25s ease;
}
.metric-card:hover { transform:translateY(-6px); }
.metric-icon  { font-size:2.2rem; margin-bottom:8px; }
.metric-value { font-size:2.6rem; font-weight:800; margin:4px 0; line-height:1; }
.metric-label { font-size:.75rem; font-weight:600; text-transform:uppercase;
                letter-spacing:1.5px; opacity:.85; margin:0; }
.metric-delta { font-size:.75rem; margin-top:6px; opacity:.8; }

.card-total  { background:linear-gradient(135deg,#6366f1,#8b5cf6); color:#fff;
               box-shadow:0 8px 32px rgba(99,102,241,.35); }
.card-high   { background:linear-gradient(135deg,#ef4444,#f97316); color:#fff;
               box-shadow:0 8px 32px rgba(239,68,68,.35); }
.card-medium { background:linear-gradient(135deg,#f59e0b,#fbbf24); color:#fff;
               box-shadow:0 8px 32px rgba(245,158,11,.35); }
.card-low    { background:linear-gradient(135deg,#06b6d4,#3b82f6); color:#fff;
               box-shadow:0 8px 32px rgba(6,182,212,.35); }

/* ── Risk badges ── */
.badge-high   { background:linear-gradient(135deg,#ef4444,#f97316); color:#fff;
                padding:4px 14px; border-radius:20px; font-weight:700; font-size:.8rem; }
.badge-medium { background:linear-gradient(135deg,#f59e0b,#fbbf24); color:#fff;
                padding:4px 14px; border-radius:20px; font-weight:700; font-size:.8rem; }
.badge-low    { background:linear-gradient(135deg,#06b6d4,#3b82f6); color:#fff;
                padding:4px 14px; border-radius:20px; font-weight:700; font-size:.8rem; }

/* ── Section title ── */
.section-title {
    font-size:.7rem; font-weight:700; color:#a78bfa;
    text-transform:uppercase; letter-spacing:2px; margin:18px 0 8px;
}
.custom-divider {
    height:1px;
    background:linear-gradient(90deg,transparent,rgba(167,139,250,.3),transparent);
    margin:16px 0;
}

/* ── Buttons ── */
.stButton > button {
    background:linear-gradient(90deg,#6366f1,#8b5cf6) !important;
    color:#fff !important; border:none !important;
    border-radius:10px !important; font-weight:600 !important;
    transition:all .25s !important;
}
.stButton > button:hover {
    transform:translateY(-2px);
    box-shadow:0 10px 28px rgba(99,102,241,.45) !important;
}

/* ── Sliders ── */
.stSlider > div > div > div { background:linear-gradient(90deg,#6366f1,#8b5cf6) !important; }

/* ── Gradient animated title ── */
@keyframes gradShift {
  0%{background-position:0% 50%} 50%{background-position:100% 50%} 100%{background-position:0% 50%}
}
.gradient-title {
    background:linear-gradient(270deg,#818cf8,#c084fc,#f472b6,#fb923c);
    background-size:400% 400%;
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    animation:gradShift 5s ease infinite;
    font-weight:800; font-size:1.3rem; line-height:1.3;
}

/* ── Pulse ── */
@keyframes pulse {
  0%{box-shadow:0 0 0 0 rgba(239,68,68,.6)} 70%{box-shadow:0 0 0 12px rgba(239,68,68,0)}
  100%{box-shadow:0 0 0 0 rgba(239,68,68,0)}
}
.pulse { animation:pulse 2.2s infinite; }

/* ── Scrollbar ── */
::-webkit-scrollbar{width:5px}
::-webkit-scrollbar-track{background:rgba(255,255,255,.04)}
::-webkit-scrollbar-thumb{background:linear-gradient(#6366f1,#8b5cf6);border-radius:3px}

/* ── Login card ── */
.login-card {
    background:linear-gradient(135deg,rgba(99,102,241,.12),rgba(139,92,246,.08));
    border:1px solid rgba(99,102,241,.35);
    border-radius:24px; padding:40px 36px;
    box-shadow:0 25px 60px rgba(0,0,0,.5);
    max-width:440px; margin:0 auto;
}
.login-title {
    font-size:1.7rem; font-weight:800; color:#fff;
    margin-bottom:4px; text-align:center;
}
.login-sub { color:rgba(255,255,255,.5); text-align:center; font-size:.88rem; margin-bottom:28px; }

/* ── Role pill ── */
.role-pill-admin   { background:linear-gradient(135deg,#6366f1,#8b5cf6); }
.role-pill-faculty { background:linear-gradient(135deg,#06b6d4,#3b82f6); }
.role-pill-student { background:linear-gradient(135deg,#f59e0b,#ef4444); }

/* ── Info box ── */
.info-box {
    background:rgba(99,102,241,.12); border:1px solid rgba(99,102,241,.35);
    border-radius:12px; padding:16px; margin:10px 0;
}

/* ── Dataframe ── */
.stDataFrame { border-radius:12px; overflow:hidden; }
</style>
"""
