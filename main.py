from flask import Flask, render_template_string, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime, timedelta
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'surejob_final_2026_secret_key'
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
    conn.execute
