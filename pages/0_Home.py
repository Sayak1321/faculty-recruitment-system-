# pages/0_Home.py
import streamlit as st
from backend import db
from ui import layout

st.set_page_config(page_title="Hire grounds — Home", layout="wide")
db.init_db()

layout.header("Hire grounds")

# HERO (clean & modern)
st.markdown("""
<div class="hg-card" style="display:flex; gap:24px; align-items:center; justify-content:space-between; max-width:1100px; margin:auto;">
  <div style="flex:1;">
    <h1 style="margin:0; color: #DAF1DE; font-size:36px; line-height:1.02;">Hire smarter. Faster. Fairer.</h1>
    <p class="muted-small" style="margin-top:8px; font-size:16px;">
      Automate resume parsing, evaluate candidates with panels, and generate audit-ready reports. Built for academic hiring.
    </p>
    <div style="margin-top:14px;">
      <a class="hg-cta" href="#" onclick="return false;">Get started</a>
      <a class="hg-ghost" href="#" onclick="return false;" style="margin-left:10px;">Learn more</a>
    </div>
  </div>
  <div style="width:320px; text-align:center;">
    <img src="https://cdn-icons-png.flaticon.com/512/3135/3135810.png" width="180" alt="Hire grounds"/>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<br/>")

# Features (3 columns)
col1, col2, col3 = st.columns(3, gap="large")
with col1:
    st.markdown('<div class="hg-card">', unsafe_allow_html=True)
    st.markdown("### ⚡ AI Resume Screening")
    st.markdown("<div class='muted-small'>Parse and score resumes automatically using configurable rules.</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
with col2:
    st.markdown('<div class="hg-card">', unsafe_allow_html=True)
    st.markdown("### 🔐 Secure Workflow")
    st.markdown("<div class='muted-small'>Role-based access, safe file handling, and audit trails.</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
with col3:
    st.markdown('<div class="hg-card">', unsafe_allow_html=True)
    st.markdown("### 🤝 Transparent Evaluation")
    st.markdown("<div class='muted-small'>Panel scoring, comments and downloadable reports for transparency.</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<br/>")

# Quick stats (jobs, applicants, shortlisted)
try:
    total_jobs = len(db.get_jobs())
except Exception:
    total_jobs = 0
try:
    conn = db.get_conn(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as c FROM applications WHERE status!='archived'")
    total_applicants = cur.fetchone()['c'] if cur.fetchone() else 0
    conn.close()
except Exception:
    # query once safely
    try:
        conn = db.get_conn(); cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as c FROM applications")
        total_applicants = cur.fetchone()['c'] if cur.fetchone() else 0
        conn.close()
    except:
        total_applicants = 0
try:
    conn = db.get_conn(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as c FROM applications WHERE status='shortlisted'")
    total_shortlisted = cur.fetchone()['c'] if cur.fetchone() else 0
    conn.close()
except Exception:
    total_shortlisted = 0

st.markdown('<div style="max-width:1100px; margin:auto;">', unsafe_allow_html=True)
st.markdown('<div class="hg-card"><div class="hg-stats">', unsafe_allow_html=True)
st.markdown(f'<div class="hg-stat"><div style="font-size:18px; font-weight:700; color: #DAF1DE;">{total_jobs}</div><div class="muted-small">Jobs</div></div>', unsafe_allow_html=True)
st.markdown(f'<div class="hg-stat"><div style="font-size:18px; font-weight:700; color: #DAF1DE;">{total_applicants}</div><div class="muted-small">Applicants</div></div>', unsafe_allow_html=True)
st.markdown(f'<div class="hg-stat"><div style="font-size:18px; font-weight:700; color: #DAF1DE;">{total_shortlisted}</div><div class="muted-small">Shortlisted</div></div>', unsafe_allow_html=True)
st.markdown('</div></div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

layout.footer()