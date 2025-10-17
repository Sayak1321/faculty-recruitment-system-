# pages/Register.py
import streamlit as st
from backend import auth, db
from datetime import datetime
import time

st.set_page_config(page_title="Register")

DEPARTMENTS = ["CSE", "ECE", "EE", "ME", "CE", "IT"]
ADMIN_SECRET = None
try:
    ADMIN_SECRET = st.secrets["app"]["admin_secret_code"]
except Exception:
    ADMIN_SECRET = "admin"  # fallback (ensure you set in secrets)

st.markdown("<h2>Register</h2>", unsafe_allow_html=True)
with st.form("reg_form"):
    full_name = st.text_input("Full Name")
    department = st.selectbox("Department", DEPARTMENTS)
    role_choice = st.selectbox("Role", ["candidate","admin"])  # admin allowed but protected by secret
    username = st.text_input("Username (unique)")
    email = st.text_input("Email")
    mobile = st.text_input("Mobile Number")
    pwd = st.text_input("Password", type="password")
    pwd2 = st.text_input("Confirm Password", type="password")
    admin_code = st.text_input("Admin Secret (only if registering as admin)", type="password")
    submitted = st.form_submit_button("Register")

    if submitted:
        # basic validation
        if not full_name or not email or not username or not pwd or pwd != pwd2:
            st.error("Please fill required fields and ensure passwords match.")
        else:
            # admin secret check
            role = "candidate"
            if role_choice == "admin":
                if admin_code != ADMIN_SECRET:
                    st.error("Invalid admin secret code. You cannot register as admin.")
                    st.stop()
                role = "admin"
            try:
                uid = auth.create_user_and_send_otp(full_name, department, username, email, mobile, pwd, role=role)
            except Exception as e:
                st.error(f"Registration failed: {e}")
            else:
                st.success("Registered. OTP sent to your email. Please check inbox (and spam).")
                # store pending verification in session and show OTP box
                st.session_state.pending_verify_user = uid
                st.session_state.pending_email = email
                st.experimental_rerun()

# OTP verification box
if "pending_verify_user" in st.session_state and st.session_state.pending_verify_user:
    uid = st.session_state.pending_verify_user
    st.markdown("---")
    st.subheader("Verify Your Email")
    code = st.text_input("Enter 6-digit OTP sent to your email", key=f"otp_{uid}")
    if st.button("Verify OTP"):
        ok = db.verify_user_otp_and_mark(uid, code.strip())
        if ok:
            st.success("Email verified. Logging you in...")
            # fetch user and auto-login
            u = db.get_user_by_username(st.session_state.get("pending_username")) if st.session_state.get("pending_username") else None
            # better fetch by id
            conn = db.get_conn(); cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE id=?", (uid,))
            r = cur.fetchone(); conn.close()
            if r:
                user = dict(r)
                st.session_state.logged_in = True
                st.session_state.user = user
                st.session_state.role = user['role']
                # cleanup
                st.session_state.pop('pending_verify_user', None)
                st.experimental_rerun()
        else:
            st.error("Invalid or expired OTP. Click 'Resend OTP' to try again.")
    if st.button("Resend OTP"):
        try:
            auth.resend_otp_for_user(uid)
            st.success("OTP resent to your email.")
        except Exception as e:
            st.error("Failed to resend OTP: " + str(e))
