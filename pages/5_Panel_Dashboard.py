
import streamlit as st
from backend import db
import json

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




st.set_page_config(page_title="Panel Evaluation")
db.init_db()
st.title("Panel Evaluation Portal")

jobs = db.get_jobs()
job_map = {f"{j['id']} - {j['title']}": j['id'] for j in jobs}
selected = st.selectbox("Select Job", options=["-- select --"] + list(job_map.keys()))
job_id = job_map.get(selected)

if job_id:
    st.header("Shortlisted Applications")
    apps = db.get_applications_by_job(job_id)
    shortlisted = [a for a in apps if a['status']=='shortlisted' or a['eligible']==1]
    if not shortlisted:
        st.info("No shortlisted applications. Admin should shortlist eligible apps.")
    else:
        for a in shortlisted:
            st.subheader(f"{a['candidate_name']} (app id {a['id']})")
            parsed = json.loads(a['parsed_json']) if a['parsed_json'] else {}
            st.markdown(f"**Email:** {parsed.get('email') or a.get('email')}")
            st.markdown(f"**Experience (yrs)**: {parsed.get('experience_years')}")
            st.markdown(f"**Publications:** {parsed.get('publications')}")
            st.markdown(f"**Skills:** {', '.join(parsed.get('skills', []))}")
            st.markdown(f"[Download resume]({a['resume_path']})")
            with st.form(f"eval_{a['id']}"):
                panelist = st.text_input("Your name / Panelist", key=f"name_{a['id']}")
                teaching = st.slider("Teaching ability (1-10)", 1, 10, 7, key=f"t_{a['id']}")
                research = st.slider("Research strength (1-10)", 1, 10, 7, key=f"r_{a['id']}")
                communication = st.slider("Communication (1-10)", 1, 10, 7, key=f"c_{a['id']}")
                fit = st.slider("Overall fit (1-10)", 1, 10, 7, key=f"f_{a['id']}")
                comments = st.text_area("Comments", key=f"comm_{a['id']}")
                submit = st.form_submit_button("Submit Evaluation")
                if submit:
                    scores = {"teaching":teaching,"research":research,"communication":communication,"fit":fit}
                    db.insert_evaluation(a['id'], panelist or "Anonymous", scores, comments)
                    st.success("Evaluation saved")
