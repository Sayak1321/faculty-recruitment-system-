# pages/2_Login.py
import streamlit as st
import bcrypt
from backend import db
from ui import layout

# --- Page Setup ---
st.set_page_config(page_title="Hire grounds — Login", page_icon="🔐")
db.init_db()
layout.header("Hire grounds")

# --- Vibrant Style ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Poppins', sans-serif !important;
}

.hg-card {
    background: linear-gradient(145deg, rgba(35,83,71,0.8) 0%, rgba(138,182,155,0.15) 100%);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 20px;
    padding: 48px 40px 52px 40px;
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

/* Buttons */
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
div[data-testid="stButton"] > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 28px rgba(0,230,168,0.35);
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

# --- LOGIN CARD ---
st.markdown('<div class="hg-card" style="max-width:640px; margin:auto;">', unsafe_allow_html=True)
st.markdown("### 🔐 Login")
st.markdown("<div class='muted-small'>Enter your username or email and password to continue.</div>", unsafe_allow_html=True)

username_or_email = st.text_input("Username or Email", key="login_username")
password = st.text_input("Password", type="password", key="login_password")

if st.button("Login", key="login_submit"):
    if not username_or_email or not password:
        st.error("Enter username/email and password.")
    else:
        user = db.get_user_by_username(username_or_email) or db.get_user_by_email(username_or_email)
        if not user:
            st.error("Invalid username or password.")
        else:
            stored_hash = user.get("password_hash")
            try:
                if stored_hash and bcrypt.checkpw(password.encode(), stored_hash.encode()):
                    user["role"] = (user.get("role") or "candidate").lower().strip()
                    st.session_state["user"] = user
                    st.success(f"Welcome, {user.get('full_name','User')}! Redirecting...")
                    st.experimental_rerun()
                else:
                    st.error("Invalid username or password.")
            except Exception:
                st.error("")
st.markdown("</div>", unsafe_allow_html=True)

layout.footer()