from flask import Flask, render_template_string, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime, timedelta
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'surejob_final_secret_2026'
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

BASE_HTML = '''<!DOCTYPE html><html><head><title>Surejob - India ka Sabse Imaandaar Job Portal</title>
<meta name="viewport" content="width=device-width, initial-scale=1">''' + CSS + '''</head><body>
<div class="header"><h1>Surejob 🔥</h1><p>India ka Sabse Imaandaar Job Portal - 100% FREE</p></div>
<div class="nav">
<a href="/">🏠 Home</a>
<a href="/login">🔐 Company Login</a>
<a href="/register">✨ 60 Din FREE</a>
</div>'''

@app.route('/')
def home():
    search = request.args.get('search', '').strip()
    category = request.args.get('category', '')
    conn = get_db()
    query = '''SELECT j.*, c.company_name, c.logo FROM jobs j JOIN companies c ON j.company_id = c.id WHERE 1=1'''
    params = []
    if search:
        query += ' AND (j.title LIKE? OR j.location LIKE? OR c.company_name LIKE?)'
        params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
    if category:
        query += ' AND j.category=?'
        params.append(category)
    query += ' ORDER BY j.id DESC'
    jobs = conn.execute(query, params).fetchall()
    conn.close()
    return render_template_string(BASE_HTML + '''
<div class="search-filter">
<form method="GET" action="/">
<input type="text" name="search" placeholder="Job Title, Company ya Location dhoondo..." value="{{search}}">
<select name="category"><option value="">All Categories</option>
{% for cat in categories %}<option value="{{cat}}" {% if category==cat %}selected{% endif %}>{{cat}}</option>{% endfor %}
</select><button type="submit">🔍 Search Jobs</button></form></div>
<div class="container"><h2>Latest Jobs - {{jobs|length}} Openings</h2>
{% if jobs %}{% for job in jobs %}
<div class="job-card">
{% if job['logo'] %}<img src="{{job['logo']}}" class="company-logo">
{% else %}<div class="company-logo" style="background:linear-gradient(135deg,#ff6b35,#e85a2b);color:white;display:flex;align-items:center;justify-content:center;font-weight:bold;font-size:28px">{{job['company_name'][0]}}</div>{% endif %}
<div class="job-content"><h3 class="job-title">{{job['title']}}</h3>
<p><b>🏢 {{job['company_name']}}</b></p>
<p class="job-meta">📍 {{job['location']}} | 💰 {{job['salary'] or 'Not Disclosed'}}</p>
<p class="job-meta">💼 {{job['experience']}} | 📅 {{job['posted_on']}}</p>
<span class="job-badge">{{job['category']}}</span>
<div><a href="/apply/{{job['id']}}" class="btn apply-btn">📝 Apply Now</a>
<a href="tel:{{job['contact']}}" class="btn call-btn">📞 Call HR</a>
<a href="https://wa.me/91{{job['contact']}}?text=Hi, I saw {{job['title']}} job on Surejob. I am interested." class="btn wa-btn">💬 WhatsApp</a>
</div></div></div>{% endfor %}
{% else %}<div class="job-card" style="text-align:center;padding:50px;"><h3>😢 Koi job nahi mili</h3></div>{% endif %}
</div></body></html>''', jobs=jobs, search=search, category=category, categories=JOB_CATEGORIES)

@app.route('/apply/<int:job_id>', methods=['GET','POST'])
def apply_job(job_id):
    conn = get_db()
    job = conn.execute('''SELECT j.*, c.company_name FROM jobs j JOIN companies c ON j.company_id=c.id WHERE j.id=?''', (job_id,)).fetchone()
    if not job:
        conn.close()
        flash('Job not found', 'error')
        return redirect(url_for('home'))
    if request.method == 'POST':
        try:
            resume = request.files.get('resume')
            resume_path = ''
            if resume and resume.filename!= '' and allowed_file(resume.filename):
                filename = secure_filename(f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{resume.filename}")
                resume.save(os.path.join(RESUME_FOLDER, filename))
                resume_path = f"/static/resumes/{filename}"
            conn.execute('''INSERT INTO applications (job_id, candidate_name, candidate_phone, candidate_email, resume_path, applied_on) VALUES (?,?,?,?,?,?)''',
                         (job_id, request.form['name'], request.form['phone'], request.form['email'], resume_path, datetime.now().strftime('%d %b %Y %H:%M')))
            conn.commit()
            conn.close()
            flash('Application Submitted Successfully! Company will contact you 🎉', 'success')
            return redirect(url_for('home'))
        except Exception as e:
            flash('Error submitting application. Try again.', 'error')
    conn.close()
    return render_template_string(BASE_HTML + '''
<div class="form-card"><h2>Apply for {{job['title']}}</h2>
<p style="text-align:center;color:#666;margin-bottom:20px;">🏢 {{job['company_name']}} | 📍 {{job['location']}}</p>
{% with messages = get_flashed_messages(with_categories=true) %}
{% if messages %}{% for category, message in messages %}<div class="alert alert-{{category}}">{{message}}</div>{% endfor %}{% endif %}{% endwith %}
<form method="POST" enctype="multipart/form-data">
<input name="name" placeholder="Full Name" required>
<input name="phone" placeholder="Mobile Number" required>
<input type="email" name="email" placeholder="Email ID" required>
<label style="font-size:14px;color:#666;">Upload Resume (PDF/DOC - Optional):</label>
<input type="file" name="resume" accept=".pdf,.doc,.docx">
<button type="submit">Submit Application</button>
</form></div></body></html>''', job=job)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            data = request.form
            logo = request.files.get('logo')
            logo_path = ''
            if logo and logo.filename!= '' and allowed_file(logo.filename):
                filename = secure_filename(f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{logo.filename}")
                logo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                logo_path = f"/static/logos/{filename}"
            conn = get_db()
            reg_date = datetime.now()
            expiry = reg_date + timedelta(days=60)
            conn.execute('INSERT INTO companies (company_name,gst_no,email,phone,password,logo,registered_on,plan_expiry) VALUES (?,?,?,?,?,?,?,?)',
                (data['company_name'],data['gst_no'],data['email'],data['phone'],data['password'],logo_path,reg_date.strftime('%d %b %Y'),expiry.strftime('%d %b %Y')))
            conn.commit()
            conn.close()
            flash('Company Registered Successfully! 60 Din FREE Start 🔥', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email already registered! Login karo.', 'error')
        except Exception as e:
            flash('Kuch error aaya. Dobara try karo.', 'error')
    return render_template_string(BASE_HTML + '''
<div class="form-card"><h2>Company Register - 60 Din FREE</h2>
{% with messages = get_flashed_messages(with_categories=true) %}
{% if messages %}{% for category, message in messages %}<div class="alert alert-{{category}}">{{message}}</div>{% endfor %}{% endif %}{% endwith %}
<form method="POST" enctype="multipart/form-data">
<input name="company_name" placeholder="Company Name" required>
<input name="gst_no" placeholder="GST Number" required>
<input type="email" name="email" placeholder="Official Email" required>
<input name="phone" placeholder="Phone Number" required>
<input type="password" name="password" placeholder="Password" required>
<label style="font-size:14px;color:#666;">Company Logo (Optional, Max 2MB):</label>
<input type="file" name="logo" accept="image/*">
<button type="submit">Register FREE</button>
</form></div></body></html>''')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        conn = get_db()
        company = conn.execute('SELECT * FROM companies WHERE email=? AND password=?', (request.form['email'], request.form['password'])).fetchone()
        conn.close()
        if company:
            session['company_id'] = company['id']
            session['company_name'] = company['company_name']
            return redirect(url_for('dashboard'))
        flash('Wrong Email or Password!', 'error')
    return render_template_string(BASE_HTML + '''
<div class="form-card"><h2>Company Login</h2>
{% with messages = get_flashed_messages(with_categories=true) %}
{% if messages %}{% for category, message in messages %}<div class="alert alert-{{category}}">{{message}}</div>{% endfor %}{% endif %}{% endwith %}
<form method="POST">
<input type="email" name="email" placeholder="Email" required>
<input type="password" name="password" placeholder="Password" required>
<button type="submit">Login</button>
</form><p style="text-align:center;margin-top:15px;"><a href="/forgot-password" style="color:#ff6b35;">Password Bhool Gaye?</a></p>
</div></body></html>''')

@app.route('/forgot-password', methods=['GET','POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        new_pass = request.form['new_password']
        conn = get_db()
        company = conn.execute('SELECT * FROM companies WHERE email=?', (email,)).fetchone()
        if company:
            conn.execute('UPDATE companies SET password=? WHERE email=?', (new_pass, email))
            conn.commit()
            conn.close()
            flash('Password Reset Ho Gaya! Login Karo', 'success')
            return redirect(url_for('login'))
        conn.close()
        flash('Email database me nahi mila', 'error')
    return render_template_string(BASE_HTML + '''
<div class="form-card"><h2>Password Reset</h2>
{% with messages = get_flashed_messages(with_categories=true) %}
{% if messages %}{% for category, message in messages %}<div class="alert alert-{{category}}">{{message}}</div>{% endfor %}{% endif %}{% endwith %}
<form method="POST">
<input type="email" name="email" placeholder="Registered Email" required>
<input type="password" name="new_password" placeholder="Naya Password" required>
<button type="submit">Reset Password</button>
</form></div></body></html>''')

@app.route('/dashboard')
def dashboard():
    if 'company_id' not in session: return redirect(url_for('login'))
    conn = get_db()
    company = conn.execute('SELECT * FROM companies WHERE id=?', (session['company_id'],)).fetchone()
    jobs = conn.execute('SELECT * FROM jobs WHERE company_id=? ORDER BY id DESC', (session['company_id'],)).fetchall()
    jobs_with_apps = []
    for job in jobs:
        apps = conn.execute('SELECT * FROM applications WHERE job_id=? ORDER BY id DESC', (job['id'],)).fetchall()
        jobs_with_apps.append({'job': job, 'applications': apps})
    conn.close()
    return render_template_string(BASE_HTML + '''
<div class="container"><div class="dashboard-header">
<div style="display:flex;align-items:center;gap:20px;">
{% if company['logo'] %}<img src="{{company['logo']}}" style="width:80px;height:80px;border-radius:12px;object-fit:cover;">{% endif %}
<div><h2>Welcome, {{company['company_name']}}</h2>
<p>🎁 60 Din FREE Plan Active | Expiry: {{company['plan_expiry']}}</p></div></div>
<a href="/post-job" class="btn call-btn" style="margin-top:15px;">+ Nayi Job Post Karo</a></div>
<h3>Aapki Posted Jobs: {{jobs_with_apps|length}}</h3>
{% for item in jobs_with_apps %}
<div class="job-list-item"><div style="flex:1;">
<div style="display:flex;justify-content:space-between;align-items:center;">
<div><b>{{item['job']['title']}}</b> - {{item['job']['location']}} | {{item['job']['category']}}<br>
<small>Posted: {{item['job']['posted_on']}} | <b style="color:#9C27B0;">{{item['applications']|length}} Applications</b></small></div>
<a href="/delete-job/{{item['job']['id']}}" class="btn delete-btn" onclick="return confirm('Job delete karni hai?')">❌ Delete</a></div>
{% if item['applications'] %}<div style="margin-top:12px;"><b style="font-size:14px;">Applicants:</b>
{% for app in item['applications'] %}<div class="applicant-card">
<b>{{app['candidate_name']}}</b> | 📞 {{app['candidate_phone']}} | ✉️ {{app['candidate_email']}}<br>
<small>Applied: {{app['applied_on']}}</small>
{% if app['resume_path'] %} | <a href="{{app['resume_path']}}" target="_blank" style="color:#9C27B0;">📄 View Resume</a>{% endif %}
</div>{% endfor %}</div>{% endif %}</div></div>{% endfor %}
<div style="text-align:center;margin-top:30px;"><a href="/logout" style="color:#f44336;">🚪 Logout</a></div></div></body></html>
''', company=company, jobs_with_apps=jobs_with_apps)

@app.route('/post-job', methods=['GET','POST'])
def post_job():
    if 'company_id' not in session: return redirect(url_for('login'))
    if request.method == 'POST':
        try:
            conn = get_db()
            conn.execute('INSERT INTO jobs (company_id,title,location,salary,experience,category,description,contact,posted_on) VALUES (?,?,?,?,?,?,?,?,?)',
                (session['company_id'], request.form['title'], request.form['location'], request.form['salary'], request.form['experience'], request.form['category'], request.form['description'], request.form['contact'], datetime.now().strftime('%d %b %Y')))
            conn.commit()
            conn.close()
            flash('Job Successfully Posted! 🎉', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash('Error posting job. Try again.', 'error')
    return render_template_string(BASE_HTML + '''
<div class="form-card"><h2>Nayi Job Post Karo - FREE</h2>
{% with messages = get_flashed_messages(with_categories=true) %}
{% if messages %}{% for category, message in messages %}<div class="alert alert-{{category}}">{{message}}</div>{% endfor %}{% endif %}{% endwith %}
<form method="POST">
<input name="title" placeholder="Job Title" required>
<input name="location" placeholder="Location - Mumbai, Delhi" required>
<input name="salary" placeholder="Salary - 25000/month">
<select name="experience" required><option value="">Experience Select Karo</option><option>Fresher</option><option>1-2 Years</option><option>2-5 Years</option><option>5+ Years</option></select>
<select name="category" required><option value="">Category Select Karo</option>{% for cat in categories %}<option>{{cat}}</option>{% endfor %}</select>
<textarea name="description" placeholder="Job Description" rows="4" required></textarea>
<input name="contact" placeholder="HR Contact Number" required>
<button type="submit">Job Post Karo - FREE</button>
</form></div></body></html>''', categories=JOB_CATEGORIES)

@app.route('/delete-job/<int:job_id>')
def delete_job(job_id):
    if 'company_id' not in session: return redirect(url_for('login'))
    conn = get_db()
    conn.execute('DELETE FROM jobs WHERE id=? AND company_id=?', (job_id, session['company_id']))
    conn.execute('DELETE FROM applications WHERE job_id=?', (job_id,))
    conn.commit()
    conn.close()
    flash('Job Deleted Successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/admin-surejob-123', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form['password'] == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        flash('Galat Password!', 'error')
    return render_template_string(BASE_HTML + '''
<div class="form-card"><h2>👑 Surejob Admin Login</h2>
{% with messages = get_flashed_messages(with_categories=true) %}
{% if messages %}{% for category, message in messages %}<div class="alert alert-{{category}}">{{message}}</div>{% endfor %}{% endif %}{% endwith %}
<form method="POST"><input type="password" name="password" placeholder="Admin Password" required>
<button type="submit">Login as Admin</button></fo
