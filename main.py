from flask import Flask, render_template_string, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime, timedelta
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'surejob_level5_secret_2026'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024

UPLOAD_FOLDER = 'static/logos'
RESUME_FOLDER = 'static/resumes'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESUME_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}
JOB_CATEGORIES = ['Sales', 'Marketing', 'IT', 'HR', 'Finance', 'Operations', 'Admin', 'Customer Support', 'Other']
ADMIN_PASSWORD = 'surejob@admin123'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    conn = sqlite3.connect('surejob.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''CREATE TABLE IF NOT EXISTS companies (id INTEGER PRIMARY KEY, company_name TEXT, gst_no TEXT, email TEXT UNIQUE, phone TEXT, password TEXT, logo TEXT, registered_on TEXT, plan_expiry TEXT)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY, company_id INTEGER, title TEXT, location TEXT, salary TEXT, experience TEXT, category TEXT, description TEXT, contact TEXT, posted_on TEXT)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS applications (id INTEGER PRIMARY KEY, job_id INTEGER, candidate_name TEXT, candidate_phone TEXT, candidate_email TEXT, resume_path TEXT, applied_on TEXT)''')
    conn.commit()
    conn.close()

init_db()

CSS = '''<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',Arial,sans-serif;background:#f4f6f9;color:#333}
.header{background:linear-gradient(135deg,#ff6b35,#e85a2b);color:white;padding:25px;text-align:center}
.header h1{font-size:32px}
.nav{display:flex;justify-content:center;gap:25px;background:#fff;padding:15px}
.nav a{color:#ff6b35;text-decoration:none;font-weight:600;padding:8px 16px;border-radius:5px}
.nav a:hover{background:#ff6b35;color:white}
.search-filter{background:white;padding:20px;margin:20px auto;max-width:1000px;border-radius:10px}
.search-filter form{display:flex;gap:10px;flex-wrap:wrap}
.search-filter input,.search-filter select{flex:1;min-width:200px;padding:12px;border:2px solid #e0e0e0;border-radius:6px}
.search-filter button{padding:12px 30px;background:#ff6b35;color:white;border:none;border-radius:6px;font-weight:bold;cursor:pointer}
.container{max-width:1000px;margin:20px auto;padding:0 15px}
.job-card{background:white;padding:20px;margin:15px 0;border-radius:12px;display:flex;gap:20px}
.company-logo{width:70px;height:70px;border-radius:10px;object-fit:cover;border:2px solid #f0f0f0}
.job-content{flex:1}
.job-title{color:#ff6b35;font-size:23px;margin:0 0 8px 0}
.job-meta{color:#666;margin:6px 0;font-size:14px}
.job-badge{display:inline-block;background:#e8f5e9;color:#2e7d32;padding:4px 10px;border-radius:20px;font-size:12px;font-weight:600}
.btn{display:inline-block;padding:11px 22px;margin:12px 10px 0 0;border-radius:6px;text-decoration:none;font-weight:600;border:none;cursor:pointer}
.call-btn{background:#2196F3;color:white}
.wa-btn{background:#25D366;color:white}
.apply-btn{background:#9C27B0;color:white}
.delete-btn{background:#f44336;color:white;padding:8px 16px;font-size:13px}
.form-card{background:white;max-width:500px;margin:30px auto;padding:30px;border-radius:12px}
.form-card h2{color:#ff6b35;margin-bottom:20px;text-align:center}
.form-card input,.form-card select,.form-card textarea{width:100%;padding:12px;margin:8px 0 15px 0;border:2px solid #e0e0e0;border-radius:6px}
.form-card button{width:100%;padding:14px;background:#ff6b35;color:white;border:none;border-radius:6px;font-weight:bold;font-size:16px;cursor:pointer}
.alert{padding:12px;margin:15px 0;border-radius:6px;text-align:center}
.alert-success{background:#d4edda;color:#155724}
.alert-error{background:#f8d7da;color:#721c24}
.dashboard-header{background:white;padding:25px;margin:20px 0;border-radius:12px}
.job-list-item{background:#f9f9f9;padding:15px;margin:10px 0;border-radius:8px}
.applicant-card{background:white;padding:12px;margin:8px 0;border-radius:6px;border-left:4px solid #9C27B0}
@media(max-width:768px){.job-card{flex-direction:column}.company-logo{align-self:center}}
</style>'''

BASE_HTML
