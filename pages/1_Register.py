import streamlit as st
import bcrypt
import os
from backend import db
from ui import layout

st.set_page_config(page_title="Hire grounds — Register", page_icon="📝")
db.init_db()
layout.header("Hire grounds")

DEPARTMENTS = ["CSE", "ECE", "EE", "ME", "CE", "IT", "Administration"]

# Load admin/panel secret codes
try:
    ADMIN_SECRET = st.secrets["app"].get("admin_secret_code")
    PANEL_SECRET = st.secrets["app"].get("panel_secret_code")
except Exception:
    ADMIN_SECRET = os.environ.get("ADMIN_SECRET", "admin")
    PANEL_SECRET = os.environ.get("PANEL_SECRET", "panel")

# --- Vibrant Styles ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Poppins', sans-serif !important;
}

.hg-card {
    background: linear-gradient(145deg, rgba(35,83,71,0.85) 0%, rgba(138,182,155,0.18) 100%);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 20px;
    padding: 48px 40px;
    box-shadow: 0 0 60px rgba(0,230,168,0.12);
    transition: all 0.3s ease;
}
.hg-card:hover {
    box-shadow: 0 0 80px rgba(0,230,168,0.2);
}

h3, .stMarkdown h3 {
    text-align: center;
    background: linear-gradient(90deg, #8EB69B, #00E6A8, #DAF1DE);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 700;
    font-size: 1.8rem;
    margin-bottom: 0.5rem;
}

.muted-small {
    text-align: center;
    color: rgba(234,246,242,0.7);
    margin-bottom: 1.5rem;
    font-size: 0.95rem;
}

/* Inputs */
.stTextInput > div > div > input {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 10px;
    color: #EAF6F2 !important;
}
.stTextInput > div > div > input:focus {
    border-color: #00E6A8 !important;
    box-shadow: 0 0 6px rgba(0,230,168,0.4);
}

/* Selectboxes */
.stSelectbox > div > div {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 10px;
    color: #EAF6F2 !important;
}
.stSelectbox > div > div:focus {
    border-color: #00E6A8 !important;
    box-shadow: 0 0 6px rgba(0,230,168,0.4);
}

/* Buttons */
div[data-testid="stFormSubmitButton"] > button, 
div[data-testid="stButton"] > button {
    background: linear-gradient(90deg, #00E6A8, #8EB69B, #DAF1DE);
    color: #03201F !important;
    border: none;
    font-weight: 700;
    border-radius: 10px;
    padding: 0.6rem 1.2rem;
    transition: all 0.3s ease-in-out;
    width: 100%;
    box-shadow: 0 8px 24px rgba(0,230,168,0.25);
}
div[data-testid="stFormSubmitButton"] > button:hover,
div[data-testid="stButton"] > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 28px rgba(0,230,168,0.35);
}

/* Progress bar (password strength) */
div[data-testid="stProgressBar"] > div > div {
    background: linear-gradient(90deg, #8EB69B, #00E6A8);
    border-radius: 10px;
}

/* Messages */
.stSuccess {
    background: linear-gradient(90deg, rgba(0,230,168,0.15), rgba(138,182,155,0.05));
    border-radius: 10px;
    border-left: 4px solid #00E6A8;
}
.stError {
    background: rgba(255, 0, 0, 0.08);
    border-left: 4px solid #FF4B4B;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# --- Registration Form ---
st.markdown('<div class="hg-card" style="max-width:760px; margin:auto;">', unsafe_allow_html=True)
st.markdown("### 📝 Register")
st.markdown("<div class='muted-small'>Create an account to apply or evaluate candidates.</div>", unsafe_allow_html=True)

with st.form("reg_form"):
    full_name = st.text_input("Full Name")
    department = st.selectbox("Department", DEPARTMENTS)
    role_choice = st.selectbox("Role", ["candidate", "panel", "admin"])
    username = st.text_input("Username (unique)")
    email = st.text_input("Email")
    mobile = st.text_input("Mobile Number (optional)")
    pwd = st.text_input("Password", type="password")
    pwd2 = st.text_input("Confirm Password", type="password")

    # Password strength indicator
    def password_strength(p):
        score = 0
        if len(p) >= 8: score += 30
        if any(c.islower() for c in p): score += 10
        if any(c.isupper() for c in p): score += 15
        if any(c.isdigit() for c in p): score += 15
        if any(c in "!@#$%^&*()-_=+[]{};:,.<>?/" for c in p): score += 30
        return min(100, score)

    strength = password_strength(pwd or "")
    st.markdown("<div style='margin-top:6px;'>Password strength</div>", unsafe_allow_html=True)
    st.progress(strength / 100.0)

    admin_code = panel_code = ""
    if role_choice == "admin":
        admin_code = st.text_input("Admin Secret (required to register as admin)", type="password")
    elif role_choice == "panel":
        panel_code = st.text_input("Panel Secret (required to register as panel member)", type="password")

    submitted = st.form_submit_button("Register")

    if submitted:
        if not full_name or not email or not username or not pwd:
            st.error("Please fill required fields.")
        elif pwd != pwd2:
            st.error("Passwords do not match.")
        elif strength < 50:
            st.error("Choose a stronger password (use mix of letters, numbers and special chars).")
        else:
            if db.get_user_by_username(username):
                st.error("Username already taken. Choose another.")
            elif db.get_user_by_email(email):
                st.error("An account with this email already exists.")
            else:
                if role_choice == "admin" and admin_code != ADMIN_SECRET:
                    st.error("Invalid admin secret code. You cannot register as admin.")
                    st.stop()
                if role_choice == "panel" and panel_code != PANEL_SECRET:
                    st.error("Invalid panel secret code. You cannot register as panel member.")
                    st.stop()

                try:
                    password_hash = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()
                    uid = db.create_user(
                        full_name=full_name,
                        department=department,
                        username=username,
                        email=email,
                        mobile=mobile,
                        password_hash=password_hash,
                        role=role_choice,
                        is_email_verified=1
                    )
                except Exception as e:
                    st.error(f"Registration failed: {e}")
                else:
                    user = db.get_user_by_username(username)
                    if user:
                        st.session_state["user"] = user
                        st.success(f"Registered and logged in successfully as {role_choice}.")
                        st.experimental_rerun()
                    else:
                        st.info("Registered. Please login from the Login page.")

st.markdown("</div>", unsafe_allow_html=True)
layout.footer()