import streamlit as st
from backend import db, resume_parser, eligibility, scoring, report_generator
import os, json, time
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# ============ PAGE SETUP ============
st.set_page_config(page_title="Admin Dashboard", layout="wide")

# --- Initialize Database ---
db.init_db()

if "user" not in st.session_state or not st.session_state["user"] or st.session_state["user"].get("role") != "admin":
    st.error("Access denied. Please log in as Admin.")
    st.stop()

# --- CSS ---
st.markdown(
    """
    <style>
    .card {
      background: rgba(255,255,255,0.85);
      border-radius: 12px;
      padding: 14px;
      box-shadow: 0 6px 18px rgba(0,0,0,0.06);
      transition: transform 0.12s ease, box-shadow 0.12s ease;
    }
    .card:hover { transform: translateY(-4px); box-shadow: 0 10px 24px rgba(0,0,0,0.1); }
    .small { font-size: 0.9rem; color:#444; }
    .muted { color: #666; font-size: 0.85rem; }
    .btn-inline { display:inline-block; margin-right:8px; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Admin Dashboard — Manage Jobs & Applications")

if st.button("Logout"):
    st.session_state.pop("user", None)
    st.rerun()

# ======================================================
# CREATE JOB SECTION
# ======================================================
with st.expander("Create Job Posting", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        title = st.text_input("Job Title")
        dept = st.text_input("Department")
    with col2:
        min_exp = st.number_input("Min Experience (years)", min_value=0, value=3)
        min_pubs = st.number_input("Min Publications", min_value=0, value=0)
    req_degree = st.text_input("Required Degree (e.g., B.Des) - optional")
    req_skills = st.text_input("Required Skills (comma separated) - mandatory")
    opt_skills = st.text_input("Optional Skills (comma separated) - bonus")
    max_applicants = st.number_input("Max Applicants (0 = unlimited)", min_value=0, value=0)

    if st.button("Create Job"):
        criteria = {
            "min_experience": int(min_exp),
            "min_publications": int(min_pubs),
            "required_degree": req_degree.strip() or None,
            "required_skills": [s.strip() for s in req_skills.split(",") if s.strip()],
            "optional_skills": [s.strip() for s in opt_skills.split(",") if s.strip()]
        }
        max_val = None if int(max_applicants) == 0 else int(max_applicants)
        jid = db.insert_job(title, dept, criteria, max_applicants=max_val)
        st.success(f"Job created (id={jid})")

st.markdown("---")

# ======================================================
# JOB LIST + ARCHIVE
# ======================================================
col_a, col_b = st.columns([3, 1])
with col_a:
    st.header("Job Postings")
with col_b:
    show_arch = st.checkbox("Show archived jobs", value=False)

jobs = db.get_jobs(include_archived=show_arch)
for job in jobs:
    job_id = job['id']
    crit = json.loads(job['criteria']) if job.get('criteria') else {}
    current = db.count_active_applications(job_id)
    max_val = job.get('max_applicants')
    is_full = max_val is not None and int(current) >= int(max_val)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([4, 1, 1])
    with col1:
        st.markdown(f"### {job['title']} — *{job['department']}*")
        st.markdown(
            f"<div class='muted'>Status: <strong>{job.get('status','active')}</strong> &nbsp;&nbsp; Applicants: <strong>{current}{' / '+str(max_val) if max_val else ''}</strong></div>",
            unsafe_allow_html=True,
        )
        st.markdown(f"**Criteria:** MinExp {crit.get('min_experience','N/A')} yrs | MinPubs {crit.get('min_publications','N/A')}")
        st.markdown(f"**Required Skills:** {', '.join(crit.get('required_skills', [])) or 'None'}")
        st.markdown(f"**Optional Skills:** {', '.join(crit.get('optional_skills', [])) or 'None'}")
        if is_full:
            st.warning("Application limit reached — job closed")

    with col2:
        if job.get('status') != 'archived':
            st.info("Use Admin panel to manage uploads.")
        else:
            st.info("Archived")

    with col3:
        if job.get('status') != 'archived':
            if st.button("Archive Job", key=f"archive_{job_id}"):
                st.session_state['pending_archive_job'] = job_id
        else:
            if st.button("Unarchive", key=f"unarchive_{job_id}"):
                db.update_job_status(job_id, 'active')
                st.success("Job unarchived")

    st.markdown("</div>", unsafe_allow_html=True)

# Handle archive confirmation
if st.session_state.get('pending_archive_job'):
    pid = st.session_state.get('pending_archive_job')
    jobx = db.get_job(pid)
    st.warning(f"You're archiving job: {jobx['title']} (id {pid}). Associated applications will be archived.")
    with st.form(key=f"archive_job_form_{pid}"):
        reason = st.text_area("Reason for archiving (>=5 chars)", height=120)
        submit = st.form_submit_button("Confirm Archive")
        cancel = st.form_submit_button("Cancel")

        if submit:
            if not reason or len(reason.strip()) < 5:
                st.error("Provide a short reason (>=5 chars).")
            else:
                db.archive_job(pid, admin_name="Admin", reason=reason.strip())
                st.success("Job archived (and linked applications archived).")
                st.session_state.pop('pending_archive_job', None)

        if cancel:
            st.session_state.pop('pending_archive_job', None)
            st.info("Archive cancelled.")

st.markdown("---")

# ======================================================
# MANAGE APPLICATIONS
# ======================================================
st.header("Manage Applications")

jobs_all = db.get_jobs(include_archived=True)
job_options = ["All"] + [f"{j['id']} - {j['title']}" for j in jobs_all]
filter_job = st.selectbox("Filter by job", options=job_options)
status_filter = st.multiselect("Status", options=["received", "shortlisted", "rejected", "archived"], default=["received", "shortlisted", "rejected"])
elig_filter = st.selectbox("Eligibility", options=["All", "Eligible", "Not Eligible"], index=0)
min_score = st.slider("Minimum score", 0, 100, 0)
search_text = st.text_input("Search candidate name or email")

# Collect and filter applications
apps = []
if filter_job and filter_job != "All":
    jid = int(filter_job.split(" - ")[0])
    apps = db.get_applications_by_job(jid, include_archived=True)
else:
    for j in jobs_all:
        apps += db.get_applications_by_job(j['id'], include_archived=True)

def app_matches(a):
    if a['status'] not in status_filter:
        return False
    if elig_filter == "Eligible" and not bool(a.get('eligible', 0)):
        return False
    if elig_filter == "Not Eligible" and bool(a.get('eligible', 0)):
        return False
    sc = a.get('score', 0) or 0
    if sc < min_score:
        return False
    if search_text:
        s = search_text.lower()
        parsed_email = json.loads(a.get('parsed_json') or "{}").get('email', '').lower()
        if not (s in (a.get('candidate_name') or "").lower() or s in (a.get('email') or "").lower() or s in parsed_email):
            return False
    return True

filtered = [a for a in sorted(apps, key=lambda x: (x.get('score') or 0), reverse=True) if app_matches(a)]
st.write(f"Showing {len(filtered)} applications (filtered)")

if filtered:
    import pandas as pd
    rows = []
    for a in filtered:
        try:
            parsed = json.loads(a['parsed_json']) if a['parsed_json'] else {}
            if not isinstance(parsed, dict):
                parsed = {}
        except Exception:
            parsed = {}
        rows.append({
            "app_id": a['id'],
            "candidate": a['candidate_name'],
            "job_id": a['job_id'],
            "score": a.get('score'),
            "eligible": bool(a.get('eligible')),
            "status": a.get('status')
        })
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True)

    # Expandable detailed candidate view
    for a in filtered:
        try:
            parsed = json.loads(a['parsed_json']) if a['parsed_json'] else {}
            if not isinstance(parsed, dict):
                parsed = {}
        except Exception:
            parsed = {}

        jobinfo = db.get_job(a['job_id'])
        title = f"{a['id']} — {a['candidate_name']} ({jobinfo['title'] if jobinfo else '—'})"

        with st.expander(title, expanded=False):
            col1, col2, col3 = st.columns([3, 1, 2])
            with col1:
                st.markdown(f"**Status:** `{a['status']}` | **Eligible:** `{bool(a.get('eligible'))}`")
                st.markdown(f"**Score:** {a.get('score')}")

            with col2:
                if os.path.exists(a['resume_path']):
                    st.markdown(f"[Download Resume]({a['resume_path']})")
                else:
                    st.write("Resume not found")

                if st.button("Download Candidate PDF", key=f"candpdf_{a['id']}"):
                    fname = f"candidate_report_{a['id']}.pdf"
                    fpath = os.path.join(db.REPORTS_DIR, fname)
                    doc = SimpleDocTemplate(fpath, pagesize=A4)
                    styles = getSampleStyleSheet()
                    story = [Paragraph(f"Candidate Report: {a['candidate_name']}", styles['Title']), Spacer(1, 12)]
                    story.append(Paragraph(f"Applied for: {jobinfo['title'] if jobinfo else ''}", styles['Normal']))
                    story.append(Spacer(1, 12))
                    story.append(Paragraph(f"Score: {a.get('score')}", styles['Normal']))
                    story.append(Spacer(1, 12))
                    mi = parsed.get('match_info', {})
                    data = [["Field", "Value"],
                            ["Eligible", str(bool(a.get('eligible')))],
                            ["Status", a.get('status')]]
                    mr = mi.get('matched_required', {})
                    data.append(["Matched Required Skills", ", ".join([f"{k}=>{v.get('matched_with')}({v.get('score')})" for k, v in mr.items()])])
                    mo = mi.get('matched_optional', {})
                    data.append(["Matched Optional Skills", ", ".join([f"{k}=>{v.get('matched_with')}({v.get('score')})" for k, v in mo.items()])])
                    table = Table(data, colWidths=[150, 350])
                    table.setStyle(TableStyle([
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke)
                    ]))
                    story.append(table)
                    doc.build(story)
                    st.success(f"Candidate PDF created: {fpath}")
                    st.markdown(f"[Download PDF]({fpath})")

            with col3:
                if a['status'] != 'archived':
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("Shortlist", key=f"short_{a['id']}"):
                            db.update_application_parsed(a['id'], parsed, True, a['score'], status='shortlisted')
                            st.success("Shortlisted")
                    with c2:
                        with st.form(key=f"rejform_{a['id']}"):
                            rej_reason = st.text_input("Rejection reason (optional)", key=f"rejtxt_{a['id']}")
                            rej_btn = st.form_submit_button("Reject")
                            if rej_btn:
                                db.update_application_parsed(a['id'], parsed, False, a['score'], status='rejected')
                                if rej_reason and len(rej_reason.strip()) > 0:
                                    db.insert_evaluation(a['id'], "Admin", {"rejected": True}, rej_reason.strip())
                                st.success("Rejected")
                    if st.button("Archive Candidate", key=f"arcapp_{a['id']}"):
                        st.session_state['pending_archive_app'] = a['id']
                else:
                    st.info("This application is archived")

            tab1, tab2 = st.tabs(["Overview", "Full Resume"])
            with tab1:
                st.subheader("Overview")
                st.markdown("**Eligibility & Match Info**")
                mi = parsed.get('match_info', {})
                if mi:
                    if mi.get('degree'):
                        deg = mi['degree']
                        if deg.get('required'):
                            if deg.get('matched'):
                                st.write(f"- Degree `{deg.get('required')}` matched with `{deg.get('matched_with')}` (method: {deg.get('method')}, score: {deg.get('score')})")
                            else:
                                st.write(f"- Degree `{deg.get('required')}` NOT matched")
                        else:
                            st.write("- No degree requirement")
                    if mi.get('matched_required'):
                        st.write("**Matched Required Skills:**")
                        for k, v in mi['matched_required'].items():
                            st.write(f"- {k} → matched with '{v.get('matched_with')}' (score {v.get('score')})")
                    if mi.get('missing_required'):
                        st.write("**Missing Required Skills:**")
                        for m in mi['missing_required']:
                            st.write(f"- {m}")
                    if mi.get('matched_optional'):
                        st.write("**Matched Optional Skills:**")
                        for k, v in mi['matched_optional'].items():
                            st.write(f"- {k} → matched with '{v.get('matched_with')}' (score {v.get('score')})")
                    st.write(f"Optional skill bonus count: {mi.get('optional_bonus_count', 0)}")
                else:
                    st.write("No match info available.")

            with tab2:
                st.subheader("Full Resume Data (parsed)")
                st.write("Degrees:", parsed.get('degrees'))
                st.write("Experience years:", parsed.get('experience_years'))
                st.write("Publications:", parsed.get('publications'))
                st.write("Skills:", parsed.get('skills'))
                st.write("Soft skills:", parsed.get('soft_skills'))
                st.markdown("**Raw excerpt**")
                st.text_area("Raw excerpt", parsed.get('raw_text_excerpt', ''), key=f"raw_excerpt_{a['id']}")

# Handle pending archive form
if st.session_state.get('pending_archive_app'):
    aid = st.session_state.get('pending_archive_app')
    app = db.get_application(aid)
    st.warning(f"You're archiving application #{aid} - {app['candidate_name']}")
    with st.form(key=f"confirm_archive_app_{aid}"):
        reason = st.text_area("Reason for archiving applicant (for audit)", height=120)
        confirm = st.form_submit_button("Confirm Archive")
        cancel = st.form_submit_button("Cancel")
        if confirm:
            if not reason or len(reason.strip()) < 5:
                st.error("Please provide a short reason (>=5 chars).")
            else:
                db.archive_application(aid, admin_name="Admin", reason=reason.strip())
                st.success("Application archived.")
                st.session_state.pop('pending_archive_app', None)
        if cancel:
            st.session_state.pop('pending_archive_app', None)
            st.info("Archive canceled.")

st.markdown("---")

# ======================================================
# REPORTS
# ======================================================
st.header("Reports")
colr1, colr2 = st.columns(2)
with colr1:
    sel_report = st.selectbox("Select job for job-level report", options=["-- select --"] + [f"{j['id']} - {j['title']}" for j in db.get_jobs(include_archived=True)])
with colr2:
    if sel_report and sel_report != "-- select --":
        jr = int(sel_report.split(" - ")[0])
        if st.button("Generate Job PDF Report"):
            path = report_generator.generate_pdf_report(jr)
            st.success(f"Report generated: {path}")
            st.markdown(f"[Download report]({path})")