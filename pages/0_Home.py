# pages/0_Home.py
import streamlit as st
from backend import db
from ui import layout

st.set_page_config(page_title="Hire grounds — Home", layout="wide", page_icon="💼")
db.init_db()
layout.header("Hire grounds")

# --- Vibrant Custom CSS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');

html, body {
    font-family: 'Poppins', sans-serif !important;
}

/* Hero Section */
.hero-section {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding: 90px 20px 60px 20px;
    background: linear-gradient(180deg, rgba(138,182,155,0.1) 0%, rgba(35,83,71,0.3) 100%);
    border-radius: 20px;
    box-shadow: 0 0 60px rgba(138,182,155,0.15);
    max-width: 1100px;
    margin: 0 auto 60px auto;
    transition: all 0.3s ease;
}

.hero-section:hover {
    box-shadow: 0 0 80px rgba(138,182,155,0.25);
}

.hero-title {
    font-size: 3rem;
    font-weight: 700;
    background: linear-gradient(90deg, #8EB69B, #DAF1DE, #00E6A8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -0.02em;
    margin-bottom: 0.5rem;
}
.hero-sub {
    color: rgba(234,246,242,0.8);
    font-size: 1.1rem;
    max-width: 640px;
    line-height: 1.5;
}
.hero-buttons {
    margin-top: 1.4rem;
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    justify-content: center;
}
.hg-cta {
    background: linear-gradient(90deg, #00E6A8, #8EB69B, #DAF1DE);
    color: #03201F !important;
    font-weight: 700;
    padding: 12px 28px;
    border-radius: 12px;
    font-size: 1rem;
    text-decoration: none;
    transition: all 0.3s ease-in-out;
}
.hg-cta:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 24px rgba(0,230,168,0.35);
}
.hg-ghost {
    color: #DAF1DE;
    border: 1.5px solid rgba(218,241,222,0.25);
    padding: 12px 28px;
    border-radius: 12px;
    font-weight: 600;
    text-decoration: none;
    transition: all 0.3s ease-in-out;
}
.hg-ghost:hover {
    background: rgba(218,241,222,0.1);
    border-color: rgba(218,241,222,0.5);
    transform: translateY(-2px);
}

/* Features Section */
.features {
    display: flex;
    justify-content: center;
    flex-wrap: wrap;
    gap: 28px;
    margin: 40px auto;
    max-width: 1100px;
}
.feature-card {
    background: linear-gradient(180deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 16px;
    padding: 26px;
    text-align: center;
    width: 300px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.25);
    transition: transform 0.25s ease, box-shadow 0.25s ease;
}
.feature-card:hover {
    transform: translateY(-6px);
    box-shadow: 0 14px 40px rgba(0,230,168,0.3);
}
.feature-icon {
    font-size: 40px;
    background: linear-gradient(90deg, #8EB69B, #00E6A8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.feature-title {
    font-size: 1.2rem;
    font-weight: 700;
    color: var(--mint2);
    margin-top: 10px;
}
.feature-desc {
    color: rgba(234,246,242,0.7);
    font-size: 0.95rem;
    margin-top: 6px;
}

/* Stats Section */
.stats-wrapper {
    display: flex;
    justify-content: center;
    flex-wrap: wrap;
    gap: 24px;
    margin: 60px auto;
    max-width: 900px;
}
.stat-card {
    background: linear-gradient(180deg, rgba(0,230,168,0.1), rgba(255,255,255,0.03));
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    padding: 20px 28px;
    min-width: 180px;
    text-align: center;
    transition: all 0.25s ease;
}
.stat-card:hover {
    background: linear-gradient(90deg, rgba(0,230,168,0.2), rgba(218,241,222,0.1));
    transform: translateY(-4px);
}
.stat-number {
    font-size: 26px;
    font-weight: 700;
    color: #00E6A8;
}
.stat-label {
    font-size: 0.95rem;
    color: rgba(234,246,242,0.75);
}
</style>
""", unsafe_allow_html=True)

# --- HERO SECTION ---
st.markdown("""
<div class="hero-section">
    <h1 class="hero-title">Hire Smarter. Faster. Fairer.</h1>
    <p class="hero-sub">Empower your academic recruitment process with intelligent automation, secure workflows, and transparent evaluation tools designed for modern hiring teams.</p>
    <div class="hero-buttons">
        <a href="#" class="hg-cta" onclick="return false;">🚀 Get Started</a>
        <a href="#" class="hg-ghost" onclick="return false;">🎨 Explore Features</a>
    </div>
</div>
""", unsafe_allow_html=True)

# --- FEATURES SECTION ---
st.markdown('<div class="features">', unsafe_allow_html=True)

features = [
    ("⚡", "AI Resume Screening", "Automatically parse, evaluate, and score resumes using adaptive algorithms and customizable rules."),
    ("🔐", "Secure Workflow", "End-to-end encryption, role-based access, and audit-safe data management."),
    ("💬", "Collaborative Evaluation", "Multiple evaluators can score, review, and leave comments in one transparent platform."),
    ("📊", "Smart Reports", "Generate visual insights and downloadable analytics to support fair hiring decisions."),
]

for icon, title, desc in features:
    st.markdown(f"""
    <div class="feature-card">
        <div class="feature-icon">{icon}</div>
        <div class="feature-title">{title}</div>
        <div class="feature-desc">{desc}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# --- STATS SECTION ---
try:
    total_jobs = len(db.get_jobs())
except Exception:
    total_jobs = 0
try:
    conn = db.get_conn(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as c FROM applications WHERE status!='archived'")
    row = cur.fetchone()
    total_applicants = row['c'] if row else 0
    conn.close()
except Exception:
    total_applicants = 0
try:
    conn = db.get_conn(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as c FROM applications WHERE status='shortlisted'")
    row = cur.fetchone()
    total_shortlisted = row['c'] if row else 0
    conn.close()
except Exception:
    total_shortlisted = 0

st.markdown(f"""
<div class="stats-wrapper">
    <div class="stat-card">
        <div class="stat-number">{total_jobs}</div>
        <div class="stat-label">Active Jobs</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">{total_applicants}</div>
        <div class="stat-label">Applicants</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">{total_shortlisted}</div>
        <div class="stat-label">Shortlisted</div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- FOOTER ---
layout.footer()