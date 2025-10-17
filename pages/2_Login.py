import streamlit as st
import bcrypt
from backend import db

st.set_page_config(page_title="Login", page_icon="🔐")

# --- Redirect if already logged in ---
if "user" in st.session_state:
    role = st.session_state["user"]["role"]
    if role == "admin":
        st.switch_page("pages/3_Admin_Dashboard.py")
    elif role == "panel":
        st.switch_page("pages/5_Panel_Dashboard.py")
    elif role == "candidate":
        st.switch_page("pages/4_Candidate_Dashboard.py")

st.title("🔐 Login Portal")

username = st.text_input("Username")
password = st.text_input("Password", type="password")

if st.button("Login"):
    user = db.get_user_by_username(username)

    if not user:
        st.error("Invalid username or password.")
    else:
        stored_hash = user.get("password_hash")
        if stored_hash and bcrypt.checkpw(password.encode(), stored_hash.encode()):
            st.session_state["user"] = user
            st.success(f"Welcome, {user['full_name']}!")

            # --- Redirect by role ---
            if user["role"] == "admin":
                st.switch_page("pages/3_Admin_Dashboard.py")
            elif user["role"] == "panel":
                st.switch_page("pages/5_Panel_Dashboard.py")
            elif user["role"] == "candidate":
                st.switch_page("pages/4_Candidate_Dashboard.py")
            else:
                st.warning("Unknown role. Contact system admin.")
        else:
            st.error("Invalid username or password.")
