# backend/db.py
import sqlite3
import os
import json
from datetime import datetime, timedelta

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(BASE_DIR, "recruitment.db")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")


def ensure_dirs():
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)


def get_conn():
    ensure_dirs()
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # enable foreign keys (if needed later)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    """
    Initialize database schema. Safe to call multiple times.
    Also normalizes any stored role values to lowercase/trimmed so access checks
    are consistent across the app. Also creates a simple settings table for
    admin-managed secrets and other small key/value settings.
    """
    conn = get_conn()
    cur = conn.cursor()

    # jobs table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        department TEXT,
        criteria TEXT,
        status TEXT DEFAULT 'active',
        max_applicants INTEGER DEFAULT 0,
        created_at TEXT
    )
    """)

    # applications table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        candidate_name TEXT,
        email TEXT,
        phone TEXT,
        job_id INTEGER,
        resume_path TEXT,
        parsed_json TEXT,
        score REAL,
        eligible INTEGER DEFAULT 0,
        status TEXT DEFAULT 'received',
        created_at TEXT,
        FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE SET NULL
    )
    """)

    # evaluations table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS evaluations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        application_id INTEGER,
        panelist_name TEXT,
        scores TEXT,
        comments TEXT,
        created_at TEXT,
        FOREIGN KEY(application_id) REFERENCES applications(id) ON DELETE CASCADE
    )
    """)

    # reports table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER,
        file_path TEXT,
        created_at TEXT,
        FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE SET NULL
    )
    """)

    # users table (single definition, using otp_hash for secure OTP storage)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT,
        department TEXT,
        username TEXT UNIQUE,
        email TEXT UNIQUE,
        mobile TEXT,
        password_hash TEXT,
        role TEXT CHECK(role IN ('admin','candidate','panel')) NOT NULL DEFAULT 'candidate',
        is_active INTEGER DEFAULT 1,
        is_email_verified INTEGER DEFAULT 0,
        otp_hash TEXT,
        otp_expires_at TEXT,
        oauth_provider TEXT,
        oauth_sub TEXT,
        created_at TEXT
    )
    """)

    # settings table (small key/value store for admin-managed secrets and flags)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT,
        updated_at TEXT
    )
    """)

    conn.commit()

    # Normalize any pre-existing role values to lowercase/trim
    try:
        cur.execute("UPDATE users SET role = LOWER(TRIM(role)) WHERE role IS NOT NULL")
        conn.commit()
    except Exception:
        # if anything goes wrong with normalization, ignore to avoid blocking init
        pass

    # create default admin if none exists
    cur.execute("SELECT COUNT(*) as c FROM users WHERE role='admin'")
    row = cur.fetchone()
    admin_count = row['c'] if row else 0
    if admin_count == 0:
        try:
            import bcrypt
            DEFAULT_ADMIN_USERNAME = os.environ.get("DEFAULT_ADMIN_USERNAME", "admin")
            DEFAULT_ADMIN_EMAIL = os.environ.get("DEFAULT_ADMIN_EMAIL", "admin@system.com")
            DEFAULT_ADMIN_PASSWORD = os.environ.get("DEFAULT_ADMIN_PASSWORD", "admin123")
            ph = bcrypt.hashpw(DEFAULT_ADMIN_PASSWORD.encode(), bcrypt.gensalt()).decode()
            cur.execute("""
            INSERT OR IGNORE INTO users
            (full_name, department, username, email, mobile, password_hash, role, is_email_verified, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'admin', 1, ?)
            """, (
                "Default Admin",
                "Administration",
                DEFAULT_ADMIN_USERNAME,
                DEFAULT_ADMIN_EMAIL,
                "",
                ph,
                datetime.utcnow().isoformat()
            ))
            conn.commit()
        except Exception:
            # if bcrypt not available, skip default admin creation
            pass

    conn.close()


# ----------------------------
# Jobs & Applications helpers
# ----------------------------
def insert_job(title, department, criteria_dict, max_applicants=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO jobs (title, department, criteria, max_applicants, status, created_at) VALUES (?, ?, ?, ?, 'active', ?)",
        (title, department, json.dumps(criteria_dict), max_applicants if max_applicants is not None else None, datetime.utcnow().isoformat())
    )
    conn.commit()
    job_id = cur.lastrowid
    conn.close()
    return job_id


def get_jobs(include_archived=False):
    conn = get_conn()
    cur = conn.cursor()
    if include_archived:
        cur.execute("SELECT * FROM jobs ORDER BY id DESC")
    else:
        cur.execute("SELECT * FROM jobs WHERE status!='archived' ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_active_jobs():
    """Return jobs visible to candidates: active status and not full."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM jobs WHERE status='active' ORDER BY id DESC")
    rows = cur.fetchall()
    out = []
    for r in rows:
        job = dict(r)
        job['current_applicants'] = count_active_applications(job['id'])
        job['is_full'] = False
        if job.get('max_applicants') is not None:
            try:
                if int(job['current_applicants']) >= int(job['max_applicants']):
                    job['is_full'] = True
            except Exception:
                job['is_full'] = False
        out.append(job)
    conn.close()
    return out


def get_job(job_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM jobs WHERE id=?", (job_id,))
    r = cur.fetchone()
    conn.close()
    return dict(r) if r else None


def update_job_status(job_id, status):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE jobs SET status=? WHERE id=?", (status, job_id))
    conn.commit()
    conn.close()


def insert_application(candidate_name, email, phone, job_id, resume_path):
    # check job capacity first
    job = get_job(job_id)
    if not job or job.get('status') == 'archived':
        raise ValueError("Job not found or archived")
    max_app = job.get('max_applicants')
    if max_app not in (None, 0):
        cur_count = count_active_applications(job_id)
        if int(cur_count) >= int(max_app):
            raise ValueError("Application limit reached for this job")
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""INSERT INTO applications
                   (candidate_name, email, phone, job_id, resume_path, parsed_json, score, eligible, status, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (candidate_name, email, phone, job_id, resume_path, json.dumps(None), None, 0, 'received', datetime.utcnow().isoformat()))
    conn.commit()
    app_id = cur.lastrowid
    conn.close()
    return app_id


def get_applications_by_job(job_id, include_archived=False):
    conn = get_conn()
    cur = conn.cursor()
    if include_archived:
        cur.execute("SELECT * FROM applications WHERE job_id=? ORDER BY created_at DESC", (job_id,))
    else:
        cur.execute("SELECT * FROM applications WHERE job_id=? AND status!='archived' ORDER BY created_at DESC", (job_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_application(app_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM applications WHERE id=?", (app_id,))
    r = cur.fetchone()
    conn.close()
    return dict(r) if r else None


def update_application_parsed(app_id, parsed_dict, eligible, score, status=None):
    conn = get_conn()
    cur = conn.cursor()
    new_status = status or ('shortlisted' if eligible else 'rejected')
    cur.execute("UPDATE applications SET parsed_json=?, eligible=?, score=?, status=? WHERE id=?",
                (json.dumps(parsed_dict), 1 if eligible else 0, float(score) if score is not None else None, new_status, app_id))
    conn.commit()
    conn.close()


def count_active_applications(job_id):
    """Count applications for a job that are not archived."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as c FROM applications WHERE job_id=? AND status!='archived'", (job_id,))
    r = cur.fetchone()
    conn.close()
    return r['c'] if r else 0


# ----------------------------
# Archive (soft-delete) operations
# ----------------------------
def archive_job(job_id, admin_name="Admin", reason="No reason provided"):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE jobs SET status='archived' WHERE id=?", (job_id,))
    cur.execute("UPDATE applications SET status='archived' WHERE job_id=?", (job_id,))
    conn.commit()
    conn.close()
    # log job-level action as an evaluation record (application_id NULL)
    try:
        conn = get_conn(); cur = conn.cursor()
        cur.execute("INSERT INTO evaluations (application_id, panelist_name, scores, comments, created_at) VALUES (?, ?, ?, ?, ?)",
                    (None, admin_name, json.dumps({"action": "archive_job"}), f"Job archived: {reason}", datetime.utcnow().isoformat()))
        conn.commit(); conn.close()
    except Exception:
        pass


def archive_application(app_id, admin_name="Admin", reason="No reason provided"):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE applications SET status='archived' WHERE id=?", (app_id,))
    conn.commit()
    conn.close()
    try:
        conn = get_conn(); cur = conn.cursor()
        cur.execute("INSERT INTO evaluations (application_id, panelist_name, scores, comments, created_at) VALUES (?, ?, ?, ?, ?)",
                    (app_id, admin_name, json.dumps({"action": "archive_application"}), f"Application archived: {reason}", datetime.utcnow().isoformat()))
        conn.commit(); conn.close()
    except Exception:
        pass


# ----------------------------
# Evaluations
# ----------------------------
def insert_evaluation(application_id, panelist_name, scores_dict, comments):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO evaluations (application_id, panelist_name, scores, comments, created_at) VALUES (?, ?, ?, ?, ?)",
                (application_id, panelist_name, json.dumps(scores_dict), comments, datetime.utcnow().isoformat()))
    conn.commit()
    eid = cur.lastrowid
    conn.close()
    return eid


def get_evaluations(application_id=None):
    conn = get_conn()
    cur = conn.cursor()
    if application_id:
        cur.execute("SELECT * FROM evaluations WHERE application_id=? ORDER BY created_at DESC", (application_id,))
    else:
        cur.execute("SELECT * FROM evaluations ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ----------------------------
# Reports
# ----------------------------
def insert_report(job_id, file_path):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO reports (job_id, file_path, created_at) VALUES (?, ?, ?)",
                (job_id, file_path, datetime.utcnow().isoformat()))
    conn.commit()
    rid = cur.lastrowid
    conn.close()
    return rid


# ----------------------------
# Users & Authentication helpers
# ----------------------------
def create_user(full_name, department, username, email, mobile, password_hash, role="candidate", is_email_verified=0):
    """
    Create a user while normalizing role to lowercase and trimming whitespace.
    Validate role against allowed roles to avoid DB CHECK failures.
    """
    # normalize role
    safe_role = (role or "candidate").lower().strip()
    if safe_role not in ("admin", "candidate", "panel"):
        safe_role = "candidate"

    conn = get_conn(); cur = conn.cursor()
    cur.execute("""INSERT INTO users
                   (full_name, department, username, email, mobile, password_hash, role, is_email_verified, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (full_name, department, username, email, mobile, password_hash, safe_role, int(is_email_verified), datetime.utcnow().isoformat()))
    conn.commit()
    uid = cur.lastrowid
    conn.close()
    return uid


def _normalize_user_row(row):
    """Helper to normalize returned user row dict (role lowercased and trimmed)."""
    if not row:
        return None
    d = dict(row)
    d['role'] = (d.get('role') or 'candidate').lower().strip()
    return d


def get_user_by_username(username):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=?", (username,))
    r = cur.fetchone(); conn.close()
    return _normalize_user_row(r)


def get_user_by_email(email):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email=?", (email,))
    r = cur.fetchone(); conn.close()
    return _normalize_user_row(r)


def update_user_otp(user_id, otp_hash, expires_at_iso):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("UPDATE users SET otp_hash=?, otp_expires_at=? WHERE id=?", (otp_hash, expires_at_iso, user_id))
    conn.commit(); conn.close()


def verify_user_otp_and_mark(user_id, otp_plain):
    """
    Verify OTP by comparing hashed otp stored in DB (bcrypt). If valid and not expired, mark email verified.
    Returns True/False.
    """
    import bcrypt
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT otp_hash, otp_expires_at FROM users WHERE id=?", (user_id,))
    r = cur.fetchone()
    if not r:
        conn.close(); return False
    otp_hash = r['otp_hash']; expires = r['otp_expires_at']
    if not otp_hash or not expires:
        conn.close(); return False
    try:
        exp_dt = datetime.fromisoformat(expires)
    except:
        conn.close(); return False
    if datetime.utcnow() > exp_dt:
        conn.close(); return False
    ok = bcrypt.checkpw(otp_plain.encode(), otp_hash.encode())
    if ok:
        cur.execute("UPDATE users SET is_email_verified=1, otp_hash=NULL, otp_expires_at=NULL WHERE id=?", (user_id,))
        conn.commit()
    conn.close()
    return ok


def set_user_password(user_id, password_hash):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("UPDATE users SET password_hash=? WHERE id=?", (password_hash, user_id))
    conn.commit(); conn.close()


# ----------------------------
# Settings helpers (key/value)
# ----------------------------
def set_setting(key, value):
    """
    Insert or update a setting. value should be string (or None to remove).
    """
    conn = get_conn(); cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    if value is None:
        cur.execute("DELETE FROM settings WHERE key=?", (key,))
    else:
        # upsert
        cur.execute("""
            INSERT INTO settings (key, value, updated_at) VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
        """, (key, value, now))
    conn.commit(); conn.close()


def get_setting(key):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT value FROM settings WHERE key=?", (key,))
    r = cur.fetchone()
    conn.close()
    return r['value'] if r else None


def delete_setting(key):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("DELETE FROM settings WHERE key=?", (key,))
    conn.commit(); conn.close()