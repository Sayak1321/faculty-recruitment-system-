# backend/auth.py
import bcrypt, secrets, smtplib, os
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from . import db


# ---------- PASSWORD HANDLING ----------
def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()

def check_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


# ---------- OTP GENERATION ----------
def generate_otp_code() -> str:
    """Generate a 6-digit numeric OTP."""
    return f"{secrets.randbelow(1000000):06d}"


# ---------- EMAIL HANDLER ----------
def send_otp_via_email(to_email: str, otp_code: str):
    """Send OTP using SMTP (configured via Streamlit secrets or environment)."""
    try:
        import streamlit as st
        smtp_cfg = st.secrets.get("smtp", {})
    except Exception:
        smtp_cfg = {}

    smtp_cfg = {**smtp_cfg, **os.environ}
    host = smtp_cfg.get("host")
    port = int(smtp_cfg.get("port", 587))
    username = smtp_cfg.get("username")
    password = smtp_cfg.get("password")

    if not host or not username or not password:
        raise RuntimeError("SMTP not configured properly in .streamlit/secrets.toml or env vars")

    body = f"Your verification code (OTP) is: {otp_code}\nThis code expires in 10 minutes."
    msg = MIMEText(body)
    msg["Subject"] = "Your OTP for Faculty Recruitment System"
    msg["From"] = username
    msg["To"] = to_email

    with smtplib.SMTP(host, port) as s:
        s.starttls()
        s.login(username, password)
        s.sendmail(username, [to_email], msg.as_string())


# ---------- USER CREATION + OTP ----------
def create_user_and_send_otp(full_name, department, username, email, mobile, plain_password, role="candidate"):
    """Create user, store hashed password + OTP, and email OTP."""
    if db.get_user_by_username(username) or db.get_user_by_email(email):
        raise ValueError("Username or email already exists")

    password_hash = hash_password(plain_password)
    uid = db.create_user(full_name, department, username, email, mobile, password_hash, role=role, is_email_verified=0)

    otp = generate_otp_code()
    otp_hash = bcrypt.hashpw(otp.encode(), bcrypt.gensalt()).decode()
    expires = (datetime.utcnow() + timedelta(minutes=10)).isoformat()
    db.update_user_otp(uid, otp_hash, expires)

    send_otp_via_email(email, otp)
    return uid


# ---------- OTP RESEND ----------
def resend_otp_for_user(user_id):
    u = db.get_user_by_id(user_id)
    if not u:
        raise ValueError("User not found")

    otp = generate_otp_code()
    otp_hash = bcrypt.hashpw(otp.encode(), bcrypt.gensalt()).decode()
    expires = (datetime.utcnow() + timedelta(minutes=10)).isoformat()
    db.update_user_otp(user_id, otp_hash, expires)
    send_otp_via_email(u["email"], otp)
    return True


# ---------- AUTHENTICATION ----------
def authenticate_user(username_or_email, plain_password, role=None, debug=False):
    """Authenticate by username/email and password, with optional role check."""
    u = db.get_user_by_username(username_or_email) or db.get_user_by_email(username_or_email)
    if not u:
        if debug: print("❌ User not found")
        return None

    if role and u["role"].lower() != role.lower():
        if debug: print(f"❌ Role mismatch ({u['role']} != {role})")
        return None

    if not check_password(plain_password, u["password_hash"]):
        if debug: print("❌ Password mismatch")
        return None

    if not u.get("is_email_verified"):
        if debug: print("⚠️ Email not verified yet")
        return u

    if debug: print(f"✅ Authentication successful for {u['username']}")
    return u
