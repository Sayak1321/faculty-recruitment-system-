from backend.db import get_conn
from backend.auth import hash_password
from datetime import datetime

def reset_admin():
    conn = get_conn()
    cur = conn.cursor()

    # Clean any old admin user
    cur.execute("DELETE FROM users WHERE username='admin'")

    hashed_pw = hash_password("admin123")

    cur.execute("""
        INSERT INTO users (full_name, department, username, email, mobile, password_hash, role, is_email_verified, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "Default Admin",
        "Administration",
        "admin",
        "admin@system.com",
        "",
        hashed_pw,
        "admin",
        1,
        datetime.utcnow().isoformat()
    ))

    conn.commit()
    conn.close()
    print("✅ Admin user reset successfully! Username: admin | Password: admin123")

if __name__ == "__main__":
    reset_admin()
