import streamlit as st

st.set_page_config(page_title="Faculty Recruitment System", layout="centered")

# --- PAGE STYLING ---
page_bg = """
<style>
body {
    background-color: #f7f9fc;
}
.main-title {
    font-size: 40px;
    font-weight: bold;
    color: #2b547e;
    text-align: center;
    margin-top: 30px;
}
.sub-title {
    text-align: center;
    color: #4a4a4a;
    margin-top: -10px;
    font-size: 18px;
}
.button-box {
    display: flex;
    justify-content: center;
    gap: 30px;
    margin-top: 40px;
}
.stButton>button {
    height: 50px;
    width: 200px;
    font-size: 18px;
    border-radius: 8px;
}
.info-box {
    margin-top: 50px;
    padding: 15px;
    background-color: #eef3f8;
    border-radius: 10px;
    text-align: center;
    color: #2B547E;
}
</style>
"""
st.markdown(page_bg, unsafe_allow_html=True)

# --- PAGE CONTENT ---
st.markdown('<div class="main-title">🎓 Faculty Recruitment System</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Smart Hiring for Educational Institutions</div>', unsafe_allow_html=True)

with st.container():
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135810.png", width=140)
    st.markdown(
        """
        <div style="text-align:center; font-size:16px;">
            Welcome to the Faculty Recruitment Portal.<br>
            A platform designed to simplify the hiring process for academic institutions using AI-powered resume evaluation and secure workflows.
        </div>
        """,
        unsafe_allow_html=True
    )

# --- BUTTONS FOR NAVIGATION ---
col1, col2 = st.columns(2)
with col1:
    if st.button("📝 Register"):
        st.switch_page("pages/1_Register.py")


with col2:
    if st.button("🔑 Login"):
        st.switch_page("pages/2_Login.py")

# --- INFORMATION BOX ---
st.markdown(
    """
    <div class="info-box">
        ✅ Apply for faculty positions<br>
        ✅ AI-based resume screening<br>
        ✅ Transparent evaluation system<br>
        ✅ Secure & user-friendly portal
    </div>
    """,
    unsafe_allow_html=True
)
