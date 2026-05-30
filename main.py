from flask import Flask, render_template_string, request, redirect, session
import sqlite3
from datetime import datetime
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", 'surejob_final_2026')

def get_db():
    conn = sqlite3.connect('surejob.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("CREATE TABLE IF NOT EXISTS companies (id INTEGER PRIMARY KEY, company_name TEXT, email TEXT UNIQUE, phone TEXT, password TEXT, registered_on TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS candidates (id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, phone TEXT, password TEXT, registered_on TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY, company_id INTEGER, title TEXT, location TEXT, salary TEXT, category TEXT, description TEXT, posted_on TEXT, views INTEGER DEFAULT 0)")
    conn.execute("CREATE TABLE IF NOT EXISTS applications (id INTEGER PRIMARY KEY, job_id INTEGER, name TEXT, email TEXT, phone TEXT, applied_on TEXT, status TEXT DEFAULT 'New')")
    conn.commit()
    conn.close()

init_db()

BASE_HTML = '''
<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>SureJob</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
<style>
.hero {background: linear-gradient(135deg, #0d6efd 0%, #0a58ca 100%); color: white; padding: 60px 0;}
.search-box {background: white; border-radius: 10px; padding: 20px; margin-top: -40px; box-shadow: 0 5px 15px rgba(0,0,0,0.1);}
.job-card:hover {transform: translateY(-5px); transition: 0.3s; box-shadow: 0 5px 15px rgba(0,0,0,0.1);}
</style>
</head><body>
<nav class="navbar navbar-expand-lg navbar-light bg-white shadow-sm">
<div class="container">
<a class="navbar-brand fw-bold text-primary" href="/">Sure Job</a>
<div class="ms-auto d-flex gap-2">
{% if session.candidate_id %}
<a class="btn btn-outline-primary btn-sm" href="/candidate-dashboard"><i class="bi bi-person"></i> {{ session.candidate_name }}</a>
<a class="btn btn-primary btn-sm" href="/logout">Logout</a>
{% elif session.company_id %}
<a class="btn btn-outline-primary btn-sm" href="/company-dashboard"><i class="bi bi-building"></i> {{ session.company_name }}</a>
<a class="btn btn-primary btn-sm" href="/logout">Logout</a>
{% else %}
<a class="btn btn-outline-primary btn-sm" href="/candidate-login"><i class="bi bi-box-arrow-in-right"></i> Job Seeker Login</a>
<a class="btn btn-outline-primary btn-sm" href="/candidate-register"><i class="bi bi-person-plus"></i> Job Seeker Register</a>
<a class="btn btn-primary btn-sm" href="/company-login"><i class="bi bi-building"></i> Employer</a>
{% endif %}
</div></div></nav>
{{ content|safe }}
<footer class="bg-dark text-white text-center py-3 mt-5"><p class="mb-0">© 2026 SureJob</p></footer>
</body></html>
'''

@app.route('/')
def home():
    conn = get_db()
    search = request.args.get('search', '')
    location = request.args.get('location', '')
    query = 'SELECT j.*, c.company_name FROM jobs j LEFT JOIN companies c ON j.company_id = c.id WHERE 1=1'
    params = []
    if search:
        query += ' AND (j.title LIKE ? OR j.category LIKE ? OR c.company_name LIKE ?)'
        params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
    if location:
        query += ' AND j.location LIKE ?'
        params.append(f'%{location}%')
    query += ' ORDER BY j.id DESC LIMIT 20'
    jobs = conn.execute(query, params).fetchall()
    conn.close()
    
    job_cards = ""
    for job in jobs:
        job_cards += f'''
        <div class="col-md-6 col-lg-4 mb-4">
        <div class="card job-card h-100"><div class="card-body">
        <h5 class="card-title">{job['title']}</h5>
        <p class="text-muted mb-2"><i class="bi bi-building"></i> {job['company_name'] or 'Company'} | <i class="bi bi-geo-alt"></i> {job['location']}</p>
        <p class="mb-2"><span class="badge bg-success">{job['salary']}</span> <span class="badge bg-secondary">{job['category']}</span></p>
        <p class="text-muted small"><i class="bi bi-eye"></i> {job['views']} views</p>
        <a href="/job/{job['id']}" class="btn btn-primary btn-sm w-100">View Details</a>
        </div></div></div>'''
    
    content = f'''
    <div class="hero text-center">
        <div class="container">
            <h1 class="display-4 fw-bold">Find Your Dream Job Today</h1>
            <p class="lead">Explore 5000+ opportunities from India's top companies</p>
        </div>
    </div>
    <div class="container">
        <div class="search-box">
            <form method="get" class="row g-2">
                <div class="col-md-5"><input name="search" class="form-control form-control-lg" placeholder="Job title, skills, or company" value="{search}"></div>
                <div class="col-md-5"><input name="location" class="form-control form-control-lg" placeholder="All Locations" value="{location}"></div>
                <div class="col-md-2"><button class="btn btn-primary btn-lg w-100">Search</button></div>
            </form>
        </div>
        <h3 class="mt-5 mb-4">Latest Jobs</h3>
        <div class="row">{job_cards if jobs else '<div class="col-12"><div class="alert alert-info">No jobs found</div></div>'}</div>
    </div>'''
    return render_template_string(BASE_HTML.replace('{{ content|safe }}', content))

@app.route('/candidate-register', methods=['GET', 'POST'])
def candidate_register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '').strip()
        if not all([name, email, phone, password]):
            msg = '<div class="container my-5"><div class="alert alert-danger">All fields required</div></div>'
            return render_template_string(BASE_HTML.replace('{{ content|safe }}', msg))
        hashed_password = generate_password_hash(password)
        conn = get_db()
        try:
            conn.execute('INSERT INTO candidates (name, email, phone, password, registered_on) VALUES (?,?,?,?,?)', (name, email, phone, hashed_password, datetime.now().strftime('%Y-%m-%d %H:%M')))
            conn.commit()
            conn.close()
            return redirect('/candidate-login')
        except:
            conn.close()
            msg = '<div class="container my-5"><div class="alert alert-danger">Email already exists</div></div>'
            return render_template_string(BASE_HTML.replace('{{ content|safe }}', msg))
    form = '''<div class="container my-5"><div class="row justify-content-center"><div class="col-md-6">
    <div class="card"><div class="card-body p-4"><h3 class="text-center mb-4">Job Seeker Registration</h3>
    <form method="post">
    <div class="mb-3"><label>Full Name</label><input name="name" class="form-control" required></div>
    <div class="mb-3"><label>Email</label><input name="email" type="email" class="form-control" required></div>
    <div class="mb-3"><label>Phone</label><input name="phone" class="form-control" required></div>
    <div class="mb-3"><label>Password</label><input name="password" type="password" class="form-control" required></div>
    <button class="btn btn-primary w-100">Register Now</button>
    </form></div></div></div>'''
    return render_template_string(BASE_HTML.replace('{{ content|safe }}', form))

@app.route('/candidate-login', methods=['GET', 'POST'])
def candidate_login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        conn = get_db()
        candidate = conn.execute('SELECT * FROM candidates WHERE email=?', (email,)).fetchone()
        conn.close()
        if candidate and check_password_hash(candidate['password'], password):
            session['candidate_id'] = candidate['id']
            session['candidate_name'] = candidate['name']
            session['candidate_email'] = candidate['email']
            return redirect('/candidate-dashboard')
        msg = '<div class="container my-5"><div class="alert alert-danger">Invalid credentials</div></div>'
        return render_template_string(BASE_HTML.replace('{{ content|safe }}', msg))
    form = '''<div class="container my-5"><div class="row justify-content-center"><div class="col-md-6">
    <div class="card"><div class="card-body p-4"><h3 class="text-center mb-4">Job Seeker Login</h3>
    <form method="post">
    <div class="mb-3"><label>Email</label><input name="email" type="email" class="form-control" required></div>
    <div class="mb-3"><label>Password</label><input name="password" type="password" class="form-control" required></div>
    <button class="btn btn-primary w-100">Login</button>
    </form><p class="text-center mt-3">New user? <a href="/candidate-register">Register here</a></p>
    </div></div></div></div></div>'''
    return render_template_string(BASE_HTML.replace('{{ content|safe }}', form))

@app.route('/candidate-dashboard')
def candidate_dashboard():
    if 'candidate_id' not in session:
        return redirect('/candidate-login')
    conn = get_db()
    apps = conn.execute('SELECT a.*, j.title, j.location, c.company_name FROM applications a JOIN jobs j ON a.job_id = j.id LEFT JOIN companies c ON j.company_id = c.id WHERE a.email =? ORDER BY a.id DESC', (session['candidate_email'],)).fetchall()
    conn.close()
    rows = ""
    for app in apps:
        rows += f"<tr><td>{app['title']}</td><td>{app['company_name'] or ''}</td><td>{app['location']}</td><td><span class='badge bg-info'>{app['status']}</span></td></tr>"
    content = f'''<div class="container my-5"><h3>Welcome {session['candidate_name']}</h3>
    <h5 class="mt-4">My Applications</h5>
    <div class="card"><div class="card-body"><table class="table"><thead><tr><th>Job</th><th>Company</th><th>Location</th><th>Status</th></tr></thead>
    <tbody>{rows}</tbody></table></div></div></div>''' if apps else f'<div class="container my-5"><h3>Welcome {session["candidate_name"]}</h3><div class="alert alert-info">No applications yet. Start applying!</div></div>'
    return render_template_string(BASE_HTML.replace('{{ content|safe }}', content))

@app.route('/company-register', methods=['GET', 'POST'])
def company_register():
    if request.method == 'POST':
        company_name = request.form.get('company_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '').strip()
        if not all([company_name, email, phone, password]):
            msg = '<div class="container my-5"><div class="alert alert-danger">All fields required</div></div>'
            return render_template_string(BASE_HTML.replace('{{ content|safe }}', msg))
        hashed_password = generate_password_hash(password)
        conn = get_db()
        try:
            conn.execute('INSERT INTO companies (company_name, email, phone, password, registered_on) VALUES (?,?,?,?,?)', (company_name, email, phone, hashed_password, datetime.now().strftime('%Y-%m-%d')))
            conn.commit()
            conn.close()
            return redirect('/company-login')
        except:
            conn.close()
            msg = '<div class="container my-5"><div class="alert alert-danger">Email already exists</div></div>'
            return render_template_string(BASE_HTML.replace('{{ content|safe }}', msg))
    form = '''<div class="container my-5"><div class="row justify-content-center"><div class="col-md-6">
    <div class="card"><div class="card-body p-4"><h3 class="text-center mb-4">Employer Registration</h3>
    <form method="post">
    <div class="mb-3"><label>Company Name</label><input name="company_name" class="form-control" required></div>
    <div class="mb-3"><label>Email</label><input name="email" type="email" class="form-control" required></div>
    <div class="mb-3"><label>Phone</label><input name="phone" class="form-control" required></div>
    <div class="mb-3"><label>Password</label><input name="password" type="password" class="form-control" required></div>
    <button class="btn btn-primary w-100">Register Company</button>
    </form></div></div></div>'''
    return render_template_string(BASE_HTML.replace('{{ content|safe }}', form))

@app.route('/company-login', methods=['GET', 'POST'])
def company_login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        conn = get_db()
        company = conn.execute('SELECT * FROM companies WHERE email=?', (email,)).fetchone()
        conn.close()
        if company and check_password_hash(company['password'], password):
            session['company_id'] = company['id']
            session['company_name'] = company['company_name']
            return redirect('/company-dashboard')
        msg = '<div class="container my-5"><div class="alert alert-danger">Invalid credentials</div></div>'
        return render_template_string(BASE_HTML.replace('{{ content|safe }}', msg))
    form = '''<div class="container my-5"><div class="row justify-content-center"><div class="col-md-6">
    <div class="card"><div class="card-body p-4"><h3 class="text-center mb-4">Employer Login</h3>
    <form method="post">
    <div class="mb-3"><label>Email</label><input name="email" type="email" class="form-control" required></div>
    <div class="mb-3"><label>Password</label><input name="password" type="password" class="form-control" required></div>
    <button class="btn btn-primary w-100">Login</button>
    </form><p class="text-center mt-3">New company? <a href="/company-register">Register here</a></p>
    </div></div></div></div></div>'''
    return render_template_string(BASE_HTML.replace('{{ content|safe }}', form))

@app.route('/company-dashboard')
def company_dashboard():
    if 'company_id' not in session:
        return redirect('/company-login')
    conn = get_db()
    jobs = conn.execute('SELECT j.*, COUNT(a.id) as app_count FROM jobs j LEFT JOIN applications a ON j.id = a.job_id WHERE j.company_id=? GROUP BY j.id ORDER BY j.id DESC', (session['company_id'],)).fetchall()
    conn.close()
    rows = ""
    for job in jobs:
        rows += f"<tr><td>{job['title']}</td><td>{job['location']}</td><td>{job['views']}</td><td>{job['app_count']}</td><td><a href='/job-apps/{job['id']}' class='btn btn-sm btn-info'>View Apps</a></td></tr>"
    content = f'''<div class="container my-5"><h3>{session['company_name']} Dashboard</h3>
    <a href="/post-job" class="btn btn-success mb-3"><i class="bi bi-plus-circle"></i> Post New Job</a>
    <div class="card"><div class="card-body"><table class="table"><thead><tr><th>Job Title</th><th>Location</th><th>Views</th><th>Applications</th><th>Action</th></tr></thead>
    <tbody>{rows}</tbody></table></div></div></div>''' if jobs else f'<div class="container my-5"><h3>{session["company_name"]} Dashboard</h3><a href="/post-job" class="btn btn-success mb-3"><i class="bi bi-plus-circle"></i> Post New Job</a><div class="alert alert-info">No jobs posted yet</div></div>'
    return render_template_string(BASE_HTML.replace('{{ content|safe }}', content))

@app.route('/post-job', methods=['GET', 'POST'])
def post_job():
    if 'company_id' not in session:
        return redirect('/company-login')
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        location = request.form.get('location', '').strip()
        salary = request.form.get('salary', '').strip()
        category = request.form.get('category', '').strip()
        description = request.form.get('description', '').strip()
        if not all([title, location, salary, category]):
            msg = '<div class="container my-5"><div class="alert alert-danger">Fill all required fields</div></div>'
            return render_template_string(BASE_HTML.replace('{{ content|safe }}', msg))
        conn = get_db()
        conn.execute('INSERT INTO jobs (company_id, title, location, salary, category, description, posted_on) VALUES (?,?,?,?,?,?,?)', (session['company_id'], title, location, salary, category, description, datetime.now().strftime('%Y-%m-%d')))
        conn.commit()
        conn.close()
        return redirect('/company-dashboard')
    form = '''<div class="container my-5"><div class="row justify-content-center"><div class="col-md-8">
    <div class="card"><div class="card-body p-4"><h3 class="mb-4">Post New Job</h3>
    <form method="post">
    <div class="mb-3"><label>Job Title *</label><input name="title" class="form-control" required></div>
    <div class="mb-3"><label>Location *</label><input name="location" class="form-control" required></div>
    <div class="mb-3"><label>Salary *</label><input name="salary" class="form-control" placeholder="e.g. 5-8 LPA" required></div>
    <div class="mb-3"><label>Category *</label><select name="category" class="form-control" required>
    <option value="">Select Category</option><option>IT Software</option><option>Sales & Marketing</option><option>BPO</option><option>HR & Admin</option><option>Other</option>
    </select></div>
    <div class="mb-3"><label>Job Description</label><textarea name="description" class="form-control" rows="5"></textarea></div>
    <button class="btn btn-primary w-100">Post Job</button>
    </form></div></div></div></div></div>'''
    return render_template_string(BASE_HTML.replace('{{ content|safe }}', form))

@app.route('/job/<int:job_id>', methods=['GET', 'POST'])
def job_detail(job_id):
    conn = get_db()
    conn.execute('UPDATE jobs SET views = views + 1 WHERE id=?', (job_id,))
    conn.commit()
    job = conn.execute('SELECT j.*, c.company_name FROM jobs j LEFT JOIN companies c ON j.company_id = c.id WHERE j.id=?', (job_id,)).fetchone()
    if not job:
        conn.close()
        return redirect('/')
    if request.method == 'POST':
        if 'candidate_id' not in session:
            conn.close()
            return redirect('/candidate-login')
        name = session['candidate_name']
        email = session['candidate_email']
        phone = request.form.get('phone', '')
        conn.execute('INSERT INTO applications (job_id, name, email, phone, applied_on) VALUES (?,?,?,?,?)', (job_id, name, email, phone, datetime.now().strftime('%Y-%m-%d %H:%M')))
        conn.commit()
        conn.close()
        msg = '<div class="container my-5"><div class="alert alert-success">Applied Successfully!</div><a href="/" class="btn btn-primary">Back to Jobs</a></div>'
        return render_template_string(BASE_HTML.replace('{{ content|safe }}', msg))
    conn.close()
    apply_form = f'''<form method="post">
    <div class="mb-3"><label>Your Phone</label><input name="phone" class="form-control" required></div>
    <button class="btn btn-success w-100">Apply Now</button>
    </form>''' if 'candidate_id' in session else '<a href="/candidate-login" class="btn btn-primary w-100">Login to Apply</a>'
    content = f'''<div class="container my-5"><div class="row"><div class="col-md-8">
    <h2>{job['title']}</h2>
    <p class="text-muted"><i class="bi bi-building"></i> {job['company_name'] or 'Company'} | <i class="bi bi-geo-alt"></i> {job['location']}</p>
    <p><span class="badge bg-success fs-6">{job['salary']}</span> <span class="badge bg-secondary fs-6">{job['category']}</span> <span class="badge bg-info fs-6"><i class="bi bi-eye"></i> {job['views']} views</span></p>
    <hr><h5>Job Description</h5><p>{job['description'] or 'No description provided'}</p>
    </div><div class="col-md-4"><div class="card"><div class="card-body">
    <h5>Apply for this Job</h5>{ap
