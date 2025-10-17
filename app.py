
import streamlit as st
from backend import db

st.set_page_config(page_title="Faculty Recruitment System", layout="wide")
db.init_db()

st.title("Faculty Recruitment System (Streamlit prototype)")
st.write("""
Use the left sidebar (Streamlit 'Pages') to go to:
- **Admin Dashboard** — create jobs, upload resumes, shortlist
- **Panel Evaluation** — evaluate shortlisted candidates
- **Candidate Portal** — apply for jobs
""")
st.info("Run the app: `streamlit run app.py`")
