import streamlit as st
import bcrypt
from backend import db

st.set_page_config(page_title="Login", page_icon="🔐")

# --- Redirect if already logged in ---
if "user" in st.session_state and st.session_state["user"]:
    role = (st.session_state["user"].get("role") or "candidate").lower()
    if role == "admin":
        st.switch_page("pages/3_Admin_Dashboard.py")
    elif role == "panel":
        st.switch_page("pages/5_Panel_Dashboard.py")
    else:
        st.switch_page("pages/4_Candidate_Dashboard.py")

st.title("🔐 Login Portal")

username_or_email = st.text_input("Username or Email")
password = st.text_input("Password", type="password")

if st.button("Login"):
    if not username_or_email or not password:
        st.error("Enter username/email and password.")
    else:
        # try username first, then email
        user = db.get_user_by_username(username_or_email) or db.get_user_by_email(username_or_email)
        if not user:
            st.error("Invalid username or password.")
        else:
            stored_hash = user.get("password_hash")
            if not stored_hash:
                st.error("Account has no password set.")
            elif not bcrypt.checkpw(password.encode(), stored_hash.encode()):
                st.error("Invalid username or password.")
            else:
                # Optional: you may check is_active here
                if not user.get("is_active", 1):
                    st.error("Account is deactivated. Contact admin.")
                else:
                    # Normalize role value to lower-case to avoid case-sensitivity issues
                    role_raw = user.get("role") or "candidate"
                    user["role"] = role_raw.lower().strip()
                    # Save normalized user into session
                    st.session_state["user"] = user
                    st.success(f"Welcome, {user.get('full_name','User')}!")
                    # Redirect by role
                    if user["role"] == "admin":
                        st.rerun()
                    elif user["role"] == "panel":
                        st.rerun()
                    else:
                        st.rerun()