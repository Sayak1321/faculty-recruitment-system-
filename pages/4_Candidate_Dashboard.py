# pages/3_Candidate_Portal.py
import streamlit as st
from backend import db, resume_parser, eligibility, scoring
import os, json, time

# Access control
if "user" not in st.session_state or st.session_state["user"]["role"] != "admin":
    st.error("Access denied. Please log in as Admin.")
    st.stop()

st.title("🧭 Admin Dashboard")
st.write("Welcome, Admin!")

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.error("Please login first.")
    st.stop()

if st.session_state.role != "admin":
    st.error("Access denied: admin only.")
    st.stop()




st.set_page_config(page_title="Candidate Portal")
db.init_db()
st.title("Candidate Portal - Apply for Jobs")

st.subheader("📌 Available Job Openings")
jobs = db.get_active_jobs()

if not jobs:
    st.info("No job postings available at the moment. Please check back later.")
else:
    for job in jobs:
        with st.container():
            crit = json.loads(job['criteria']) if job['criteria'] else {}
            is_full = job.get('is_full', False)
            st.markdown(f"""
            ### 🏫 {job['title']}  —  *{job['department']} Department*
            **Eligibility Criteria:**
            - Minimum Experience: `{crit.get('min_experience', 'N/A')} years`
            - Minimum Publications: `{crit.get('min_publications', 'N/A')}`
            - Required Degree: `{crit.get('required_degree', 'Any')}`
            - Required Skills: `{', '.join(crit.get('required_skills', [])) if crit.get('required_skills') else 'Not specified'}`
            - Optional Skills (bonus): `{', '.join(crit.get('optional_skills', [])) if crit.get('optional_skills') else 'None'}`
            """)
            if is_full:
                st.error("Applications closed for this position (applicant limit reached).")
            else:
                apply_button = st.button(f"Apply Now for Job ID {job['id']}", key=f"apply_{job['id']}")
                if apply_button:
                    st.session_state['selected_job'] = job['id']
                    st.session_state['show_apply_form'] = True

st.markdown("---")
if 'show_apply_form' in st.session_state and st.session_state['show_apply_form']:
    selected_job_id = st.session_state['selected_job']
    job = db.get_job(selected_job_id)
    st.subheader(f"📝 Application Form — {job['title']}")

    with st.form("apply_form"):
        name = st.text_input("Full Name")
        email = st.text_input("Email")
        phone = st.text_input("Phone")
        resume = st.file_uploader("Upload Resume (PDF/DOCX)", type=["pdf","docx"])
        submit = st.form_submit_button("Submit Application")

        if submit:
            if not name or not resume:
                st.error("⚠️ Please fill your name and upload your resume.")
            else:
                save_path = os.path.join(db.UPLOADS_DIR, f"{int(time.time())}_{resume.name}")
                with open(save_path, "wb") as out:
                    out.write(resume.getbuffer())
                try:
                    app_id = db.insert_application(name, email, phone, selected_job_id, save_path)
                except ValueError as e:
                    st.error(str(e))
                    try:
                        os.remove(save_path)
                    except:
                        pass
                else:
                    # Call parser with job skills and debug ON (for now)
                    crit = json.loads(job['criteria']) if job['criteria'] else {}
                    job_skill_list = crit.get('required_skills', []) + crit.get('optional_skills', [])
                    parsed = resume_parser.parse_resume(save_path, job_skills=job_skill_list, extra_synonyms=None, debug=True)
                    eligible, reasons, match_info = eligibility.check_eligibility(parsed, crit, debug=True)
                    score = scoring.compute_score(parsed, crit, match_info)
                    parsed_with_match = parsed.copy()
                    parsed_with_match['match_info'] = match_info
                    db.update_application_parsed(app_id, parsed_with_match, eligible, score)

                    st.success(f"Application ID: {app_id}")
                    st.markdown(f"**Auto-screen result:** {'✅ Eligible' if eligible else '❌ Not Eligible'}  — **Score:** {score}")
                    if reasons:
                        st.warning("⚠️ Reasons for non-eligibility:")
                        for r in reasons:
                            st.write("- " + r)

                    st.markdown("**Match details:**")
                    deg_info = match_info.get("degree", {})
                    if deg_info:
                        st.write("**Degree Matching**")
                        if deg_info.get("required"):
                            if deg_info.get("matched"):
                                st.write(f"- Required degree `{deg_info.get('required')}` matched with `{deg_info.get('matched_with')}` (method: {deg_info.get('method')}, score: {deg_info.get('score')})")
                            else:
                                st.write(f"- Required degree `{deg_info.get('required')}` NOT matched")
                        else:
                            st.write("- No required degree for this job")

                    if match_info.get("matched_required"):
                        st.write("**Matched Required Skills:**")
                        for k,v in match_info["matched_required"].items():
                            st.write(f"- {k} → matched with '{v.get('matched_with')}' (score {v.get('score')})")
                    if match_info.get("missing_required"):
                        st.write("**Missing Required Skills:**")
                        for m in match_info["missing_required"]:
                            st.write(f"- {m}")

                    if match_info.get("matched_optional"):
                        st.write("**Matched Optional Skills (bonus):**")
                        for k,v in match_info["matched_optional"].items():
                            st.write(f"- {k} → matched with '{v.get('matched_with')}' (score {v.get('score')})")
                    st.write(f"Optional skill bonus count: {match_info.get('optional_bonus_count',0)}")

    if st.button("🔙 Back to Job List"):
        st.session_state['show_apply_form'] = False
