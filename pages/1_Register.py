import streamlit as st
import bcrypt
import os
from backend import db
from datetime import datetime

st.set_page_config(page_title="Register")

DEPARTMENTS = ["CSE", "ECE", "EE", "ME", "CE", "IT", "Administration"]

# Load admin/panel secret codes from Streamlit secrets or environment variables
try:
    ADMIN_SECRET = st.secrets["app"].get("admin_secret_code")
    PANEL_SECRET = st.secrets["app"].get("panel_secret_code")
except Exception:
    ADMIN_SECRET = os.environ.get("ADMIN_SECRET", "admin")
    PANEL_SECRET = os.environ.get("PANEL_SECRET", "panel")

st.markdown("<h2>Register</h2>", unsafe_allow_html=True)

with st.form("reg_form"):
    full_name = st.text_input("Full Name")
    department = st.selectbox("Department", DEPARTMENTS)
    role_choice = st.selectbox("Role", ["candidate", "panel", "admin"])
    username = st.text_input("Username (unique)")
    email = st.text_input("Email")
    mobile = st.text_input("Mobile Number (optional)")
    pwd = st.text_input("Password", type="password")
    pwd2 = st.text_input("Confirm Password", type="password")

    # show secret code field conditionally
    admin_code = ""
    panel_code = ""
    if role_choice == "admin":
        admin_code = st.text_input("Admin Secret (required to register as admin)", type="password")
    elif role_choice == "panel":
        panel_code = st.text_input("Panel Secret (required to register as panel member)", type="password")

    submitted = st.form_submit_button("Register")

    if submitted:
        # basic validation
        if not full_name or not email or not username or not pwd:
            st.error("Please fill required fields.")
        elif pwd != pwd2:
            st.error("Passwords do not match.")
        else:
            # uniqueness checks
            if db.get_user_by_username(username):
                st.error("Username already taken. Choose another.")
            elif db.get_user_by_email(email):
                st.error("An account with this email already exists.")
            else:
                # role-specific secret checks
                if role_choice == "admin":
                    if admin_code != ADMIN_SECRET:
                        st.error("Invalid admin secret code. You cannot register as admin.")
                        st.stop()
                if role_choice == "panel":
                    if panel_code != PANEL_SECRET:
                        st.error("Invalid panel secret code. You cannot register as panel member.")
                        st.stop()

                # create user (simple flow: no OTP, mark email verified)
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
                    # fetch created user and log them in
                    user = db.get_user_by_username(username)
                    if user:
                        st.session_state["user"] = user
                        st.success(f"Registered and logged in successfully as {role_choice}.")
                        # redirect based on role
                        if role_choice == "admin":
                            st.rerun()  # top-of-page redirect logic will switch
                            # alternatively: st.switch_page("pages/3_Admin_Dashboard.py")
                        elif role_choice == "panel":
                            st.rerun()
                            # alternatively: st.switch_page("pages/5_Panel_Dashboard.py")
                        else:
                            st.rerun()
                            # alternatively: st.switch_page("pages/4_Candidate_Dashboard.py")
                    else:
                        st.info("Registered. Please login from Login page.")