from flask import Flask, render_template_string, request, redirect, url_for, session, flash, send_from_directory
import sqlite3
from datetime import datetime, timedelta
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'surejob_v2_2026_shine_type'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

UPLOAD_FOLDER = 'static/logos'
RESUME_FOLDER = 'static/resumes'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESUME_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}
JOB_CATEGORIES = ['Sales', 'Marketing', 'IT Software', 'HR', 'Finance', 'Operations', 'BPO', 'Customer Support', 'Engineering', 'Admin', 'Other']
LOCATIONS = ['Delhi', 'Mumbai', 'Bangalore', 'Hyderabad', 'Pune', 'Chennai', 'Kolkata', 'Noida', 'Gurgaon', 'Remote']
ADMIN_PASSWORD = 'surejob@admin123'
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    conn = sqlite3.connect('surejob.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''CREATE TABLE IF NOT EXISTS companies (id INTEGER PRIMARY KEY, company_name TEXT, gst_no TEXT, email TEXT UNIQUE, phone TEXT, password TEXT, logo TEXT, registered_on TEXT, plan_expiry TEXT, status TEXT DEFAULT 'Active')''')
    conn.execute('''CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY, company_id INTEGER, title TEXT, location TEXT, salary TEXT, experience TEXT, category TEXT, description TEXT, skills TEXT, contact TEXT, posted_on TEXT, status TEXT DEFAULT 'Active')''')
    conn.execute('''CREATE TABLE IF NOT EXISTS applications (id INTEGER PRIMARY KEY, job_id INTEGER, name TEXT, email TEXT, phone TEXT, resume TEXT, cover_letter TEXT, applied_on TEXT)''')
    conn.commit()
    conn.close()

init_db()

BASE_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <title>Surejob - India's Job Portal</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body { background: #f5f7fa; font-family: 'Segoe UI', sans-serif; }
      .navbar { background: linear-gradient(90deg, #4e54c8, #8f94fb)!important; }
      .hero { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 60px 0; }
      .job-card { transition: 0
      @app.route('/')
def home():
    conn = get_db()
    search = request.args.get('search', '')
    location = request.args.get('location', '')
    category = request.args.get('category', '')

    query = 'SELECT j.*, c.company_name, c.logo FROM jobs j JOIN companies c ON j.company_id = c.id WHERE j.status="Active"'
    params = []
    if search:
        query += ' AND j.title LIKE?'
        params.append(f'%{search}%')
    if location:
        query += ' AND j.location=?'
        params.append(location)
    if category:
        query += ' AND j.category=?'
        params.append(category)
    query += ' ORDER BY j.id DESC LIMIT 50'

    jobs = conn.execute(query, params).fetchall()
    conn.close()

    job_cards = ""
    for job in jobs:
        logo = f'<img src="/{job["logo"]}" width="60" height="60" class="rounded border">' if job["logo"] else '<div class="bg-primary text-white rounded d-flex align-items-center justify-content-center" style="width:60px;height:60px;"><i class="fas fa-building fa-2x"></i></div>'
        skills = job["skills"].split(',')[:3] if job["skills"] else []
        skill_badges = ''.join([f'<span class="badge badge-skill">{s.strip()}</span>' for s in skills])

        job_cards += f'''
        <div class="col-lg-6 mb-4">
            <div class="card job-card h-100">
                <div class="card-body">
                    <div class="d-flex mb-3">
                        {logo}
                        <div class="ms-3 flex-grow-1">
                            <h5 class="card-title mb-1">{job["title"]}</h5>
                            <p class="text-muted mb-0"><i class="fas fa-building"></i> {job["company_name"]}</p>
                        </div>
                        <span class="badge bg-success">Active</span>
                    </div>
                    <div class="mb-2">
                        <span class="me-3"><i class="fas fa-map-marker-alt text-danger"></i> {job["location"]}</span>
                        <span class="me-3"><i class="fas fa-rupee-sign text-success"></i> {job["salary"]}</span>
                        <span><i class="fas fa-briefcase text-info"></i> {job["experience"]}</span>
                    </div>
                    <div class="mb-3">{skill_badges}</div>
                    <div class="d-flex justify-content-between align-items-center">
                        <span class="badge bg-primary">{job["category"]}</span>
                        <a href="/job/{job["id"]}" class="btn btn-primary btn-sm">View & Apply <i class="fas fa-arrow-right"></i></a>
                    </div>
                </div>
            </div>
        '''

    search_form = f'''
    <div class="hero">
        <div class="container text-center">
            <h1 class="display-4 fw-bold mb-4">Find Your Dream Job</h1>
            <p class="lead mb-4">50,000+ Jobs from Top Companies</p>
            <form class="row g-2 justify-content-center" method="get">
                <div class="col-md-4">
                    <input name="search" class="form-control form-control-lg" placeholder="Job Title, Skills" value="{search}">
                </div>
                <div class="col-md-3">
                    <select name="location" class="form-select form-select-lg">
                        <option value="">All Locations</option>
                        {''.join([f'<option {"selected" if location==loc else ""}>{loc}</option>' for loc in LOCATIONS])}
                    </select>
                </div>
                <div class="col-md-3">
                    <select name="category" class="form-select form-select-lg">
                        <option value="">All Categories</option>
                        {''.join([f'<option {"selected" if category==cat else ""}>{cat}</option>' for cat in JOB_CATEGORIES])}
                    </select>
                </div>
                <div class="col-md-2">
                    <button class="btn btn-warning btn-lg w-100"><i class="fas fa-search"></i> Search</button>
                </div>
            </form>
        </div>
    </div>
    '''

    content = f'''
    {search_form}
    <div class="container mt-5">
        <h3 class="mb-4">Latest Jobs ({len(jobs)} Results)</h3>
        <div class="row">{job_cards if job_cards else '<div class="col-12 text-center py-5"><h4>No jobs found</h4><p>Try different keywords or check back later</p></div>'}</div>
    </div>
    '''
    return render_template_string(BASE_HTML, content=content)

@app.route('/job/<int:job_id>', methods=['GET', 'POST'])
def job_detail(job_id):
    conn = get_db()
    job = conn.execute('SELECT j.*, c.company_name, c.logo, c.email as company_email FROM jobs j JOIN companies c ON j.company_id = c.id WHERE j.id=?
    @app.route('/company-register', methods=['GET', 'POST'])
def company_register():
    if request.method == 'POST':
        logo = request.files.get('logo')
        logo_path = ''
        if logo and allowed_file(logo.filename):
            filename = secure_filename(f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{logo.filename}")
            logo_path = os.path.join(UPLOAD_FOLDER, filename)
            logo.save(logo_path)

        conn = get_db()
        try:
            conn.execute('INSERT INTO companies (company_name, gst_no, email, phone, password, logo, registered_on, plan_expiry) VALUES (?,?,?,?,?,?,?,?)',
                (request.form['company_name'], request.form['gst_no'], request.form['email'], request.form['phone'],
                 request.form['password'], logo_path, datetime.now().strftime('%Y-%m-%d'), (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')))
            conn.commit()
            flash('Registration successful! Please login.')
            return redirect('/company-login')
        except sqlite3.IntegrityError:
            flash('Email already registered!')
        finally:
            conn.close()

    content = '''
    <div class="container mt-4">
        <div class="row justify-content-center">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        <h3 class="text-center mb-4">Employer Registration</h3>
                        <form method="post" enctype="multipart/form-data">
                            <input name="company_name" class="form-control mb-2" placeholder="Company Name" required>
                            <input name="gst_no" class="form-control mb-2" placeholder="GST Number" required>
                            <input name="email" type="email" class="form-control mb-2" placeholder="Official Email" required>
                            <input name="phone" class="form-control mb-2" placeholder="Contact Number" required>
                            <input name="password" type="password" class="form-control mb-2
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        if request.form['password'] == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect('/admin')
        flash('Wrong Password!')

    if not session.get('admin'):
        content = '''
        <div class="container mt-5">
            <div class="row justify-content-center">
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-body">
                            <h3 class="text-center mb-4">Admin Login</h3>
                            <form method="post">
                                <input name="password" type="password" class="form-control mb-3" placeholder="Admin Password" required>
                                <button class="btn btn-dark w-100">Login</button>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        '''
        return render_template_string(BASE_HTML, content=content)

    conn = get_db()
    companies = conn.execute('SELECT * FROM companies ORDER BY id DESC').fetchall()
    jobs = conn.execute('SELECT j.*, c.company_name FROM jobs j JOIN companies c ON j.company_id = c.id ORDER BY j.id DESC').fetchall()
    apps = conn.execute('SELECT COUNT(*) as total FROM applications').fetchone()
    conn.close()

    comp_rows = ''.join([f'<tr><td>{c["id"]}</td><td>{c["company_name"]}</td><td>{c["email"]}</td><td>{c["registered_on"]}</td><td><span class="badge bg-success">{c["status"]}</span></td></tr>' for c in companies])
    job_rows = ''.join([f'<tr><td>{j["id"]}</td><td>{j["title"]}</td><td>{j["company_name"]}</td><td>{j["location"]}</td><td>{j["posted_on"]}</td></tr>' for j in jobs])

    content = f'''
    <div class="container mt-4">
        <h3>Admin Dashboard - Surejob</h3>
        <a href="/logout" class="btn btn-danger btn-sm mb-3">Logout
