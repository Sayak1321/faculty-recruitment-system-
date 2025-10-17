import streamlit as st
from backend import db
import json
import os
import mimetypes

st.set_page_config(page_title="Panel Evaluation")
db.init_db()

# --- ACCESS CONTROL: allow panelists and admins ---
if "user" not in st.session_state or not st.session_state["user"] or st.session_state["user"].get("role") not in ("panel", "admin"):
    st.error("Access denied. Please log in as Panel member.")
    st.stop()

st.title("Panel Evaluation Portal")
st.write(f"Welcome, {st.session_state['user'].get('full_name','Panelist')}")

# Logout: clear user and redirect to Home
if st.button("Logout"):
    st.session_state.pop("user", None)
    st.success("Logged out. Redirecting to Home...")
    st.switch_page("pages/0_Home.py")

jobs = db.get_jobs()
job_map = {f"{j['id']} - {j['title']}": j['id'] for j in jobs}
selected = st.selectbox("Select Job", options=["-- select --"] + list(job_map.keys()))
job_id = job_map.get(selected)

if job_id:
    st.header("Shortlisted Applications")
    apps = db.get_applications_by_job(job_id)
    shortlisted = [a for a in apps if a.get('status') == 'shortlisted' or a.get('eligible') == 1]
    if not shortlisted:
        st.info("No shortlisted applications. Admin should shortlist eligible apps.")
    else:
        for a in shortlisted:
            st.subheader(f"{a.get('candidate_name')} (app id {a.get('id')})")
            parsed = json.loads(a.get('parsed_json') or "{}")
            st.markdown(f"**Email:** {parsed.get('email') or a.get('email')}")
            st.markdown(f"**Experience (yrs)**: {parsed.get('experience_years')}")
            st.markdown(f"**Publications:** {parsed.get('publications')}")
            st.markdown(f"**Skills:** {', '.join(parsed.get('skills', []))}")
            # Resume download using st.download_button (safe for deployed apps)
            resume_path = a.get("resume_path")
            if resume_path and os.path.exists(resume_path):
                mime_type, _ = mimetypes.guess_type(resume_path)
                mime_type = mime_type or "application/octet-stream"
                with open(resume_path, "rb") as fh:
                    st.download_button(
                        label="Download resume",
                        data=fh.read(),
                        file_name=os.path.basename(resume_path),
                        mime=mime_type,
                    )
            else:
                st.markdown("Resume file missing or unavailable.")

            with st.form(f"eval_{a.get('id')}"):
                panelist = st.text_input("Your name / Panelist", key=f"name_{a.get('id')}")
                teaching = st.slider("Teaching ability (1-10)", 1, 10, 7, key=f"t_{a.get('id')}")
                research = st.slider("Research strength (1-10)", 1, 10, 7, key=f"r_{a.get('id')}")
                communication = st.slider("Communication (1-10)", 1, 10, 7, key=f"c_{a.get('id')}")
                fit = st.slider("Overall fit (1-10)", 1, 10, 7, key=f"f_{a.get('id')}")
                comments = st.text_area("Comments", key=f"comm_{a.get('id')}")
                submit = st.form_submit_button("Submit Evaluation")
                if submit:
                    scores = {"teaching": teaching, "research": research, "communication": communication, "fit": fit}
                    # Fall back to panelist input or the logged-in user's name
                    panel_name = (panelist.strip() or st.session_state['user'].get('full_name', 'Anonymous'))
                    db.insert_evaluation(a.get('id'), panel_name, scores, comments)
                    st.success("Evaluation saved")