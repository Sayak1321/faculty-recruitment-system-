# pages/2_Login.py
import streamlit as st
import bcrypt
from backend import db
from ui import layout

st.set_page_config(page_title="Hire grounds — Login")
db.init_db()
layout.header("Hire grounds")

st.markdown('<div class="hg-card" style="max-width:640px; margin:auto;">', unsafe_allow_html=True)
st.markdown("### 🔐 Login")
st.markdown("<div class='muted-small'>Enter username or email and password.</div>", unsafe_allow_html=True)

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
                    # normalize role
                    user["role"] = (user.get("role") or "candidate").lower().strip()
                    st.session_state["user"] = user
                    st.success(f"Welcome, {user.get('full_name','User')}!")
                    st.experimental_rerun()
                else:
                    st.error("Invalid username or password.")
            except Exception:
                st.error("")
st.markdown("</div>", unsafe_allow_html=True)
layout.footer()