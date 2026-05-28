from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
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
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    conn = sqlite3.connect('surejob.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("CREATE TABLE IF NOT EXISTS companies (id INTEGER PRIMARY KEY, company_name TEXT, gst_no TEXT, email TEXT UNIQUE, phone TEXT, password TEXT, logo TEXT, registered_on TEXT, plan_expiry TEXT, status TEXT DEFAULT 'Active')")
    conn.execute("CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY, company_id INTEGER, title TEXT, location TEXT, salary TEXT, experience TEXT, category TEXT, description TEXT, skills TEXT, contact TEXT, posted_on TEXT, status TEXT DEFAULT 'Active')")
    conn.execute("CREATE TABLE IF NOT EXISTS applications (id INTEGER PRIMARY KEY, job_id INTEGER, name TEXT, email TEXT, phone TEXT, resume TEXT, cover_letter TEXT, applied_on TEXT)")
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    try:
        conn = get_db()
        search = request.args.get('search', '')
        location = request.args.get('location', '')
        category = request.args.get('category', '')

        query = '''
            SELECT j.id, j.title, j.description, j.salary, j.location, j.category, j.skills,
                   c.company_name, c.logo
            FROM jobs j
            LEFT JOIN companies c ON j.company_id = c.id
            WHERE 1=1
        '''
        params = []
        if search:
            query += ' AND j.title LIKE?'
            params.append(f'%{search}%')
        if location:
            query += ' AND j.location =?'
            params.append(location)
        if category:
            query += ' AND j.category =?'
            params.append(category)
        query += ' ORDER BY j.id DESC LIMIT 50'

        jobs = conn.execute(query, params).fetchall()
        conn.close()
        return render_template('index.html', jobs=jobs, locations=LOCATIONS, categories=JOB_CATEGORIES, search=search, location=location, category=category)

    except Exception as e:
        print(f"Homepage Error: {e}")
        return f"Error: {e}", 500

@app.route('/job/<int:job_id>', methods=['GET', 'POST'])
def job_detail(job_id):
    conn = get_db()
    job = conn.execute('SELECT j.*, c.company_name, c.logo FROM jobs j JOIN companies c ON j.company_id = c.id WHERE j.id=?', (job_id,)).fetchone()
    if not job:
        conn.close()
        return "Job Not Found", 404
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()

        if not all([name, email, phone]):
            flash('Name, Email aur Phone required hai!')
            conn.close()
            return redirect(f'/job/{job_id}')

        resume = request.files.get('resume')
        resume_path = ''
        if resume and resume.filename and allowed_file(resume.filename):
            filename = secure_filename(f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{resume.filename}")
            resume_path = os.path.join(RESUME_FOLDER, filename)
            resume.save(resume_path)

        conn.execute('INSERT INTO applications (job_id, name, email, phone, resume, cover_letter, applied_on) VALUES (?,?,?,?,?,?,?)',
            (job_id, name, email, phone, resume_path, request.form.get('cover_letter',''), datetime.now().strftime('%Y-%m-%d %H:%M')))
        conn.commit()
        flash('Application submitted successfully!')
        conn.close()
        return redirect(f'/job/{job_id}')
    conn.close()
    return render_template('job_detail.html', job=job)

@app.route('/company-register', methods=['GET', 'POST'])
def company_register():
    if request.method == 'POST':
        company_name = request.form.get('company_name', '').strip()
        gst_no = request.form.get('gst_no', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '').strip()

        if not all([company_name, email, phone, password]):
            flash('Company Name, Email, Phone aur Password required hai!')
            return render_template('company_register.html')

        logo = request.files.get('logo')
        logo_path = ''
        if logo and logo.filename and allowed_file(logo.filename):
            filename = secure_filename(f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{logo.filename}")
            logo_path = os.path.join(UPLOAD_FOLDER, filename)
            logo.save(logo_path)

        conn = get_db()
        try:
            conn.execute('INSERT INTO companies (company_name, gst_no, email, phone, password, logo, registered_on, plan_expiry) VALUES (?,?,?,?,?,?,?,?)',
                (company_name, gst_no, email, phone, password, logo_path,
                 datetime.now().strftime('%Y-%m-%d'),
                 (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')))
            conn.commit()
            flash('Registration successful! Please login.')
            conn.close()
            return redirect('/company-login')
        except sqlite3.IntegrityError:
            conn.close()
            flash('Ye Email already registered hai! Dusra email use karo.')
        except Exception as e:
            conn.close()
            flash(f'Kuch error aa gaya: {str(e)}')

    return render_template('company_register.html')

@app.route('/company-login', methods=['GET', 'POST'])
def company_login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        if not email or not password:
            flash('Email aur Password dono dalo!')
            return render_template('company_login.html')

        conn = get_db()
        company = conn.execute('SELECT * FROM companies WHERE email=? AND password=?', (email, password)).fetchone()
        conn.close()
        if company:
            session['company_id'] = company['id']
            session['company_name'] = company['company_name']
            return redirect('/company-dashboard')
        flash('Invalid credentials!')
    return render_template('company_login.html')
@app.route('/company-dashboard')
def company_dashboard():
    if 'company_id' not in session:
        return redirect('/company-login')
    conn = get_db()
    company = conn.execute('SELECT * FROM companies WHERE id=?', (session['company_id'],)).fetchone()
    jobs = conn.execute('''
        SELECT * FROM jobs WHERE id IN (
            SELECT MIN(id) FROM jobs 
            WHERE company_id=? 
            GROUP BY title, location, salary, category
        ) ORDER BY id DESC
    ''', (session['company_id'],)).fetchall()
    apps = conn.execute('SELECT a.*, j.title FROM applications a JOIN jobs j ON a.job_id = j.id WHERE j.company_id=? ORDER BY a.id DESC LIMIT 10', (session['company_id'],)).fetchall()
    conn.close()
    return render_template('company_dashboard.html', jobs=jobs, apps=apps, company=company)

@app.route('/post-job', methods=['GET', 'POST'])
def post_job():
    if 'company_id' not in session:
        return redirect('/company-login')

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        salary = request.form.get('salary', '').strip()
        location = request.form.get('location', '').strip()
        category = request.form.get('category', '').strip()
        experience = request.form.get('experience', '').strip()
        skills = request.form.get('skills', '').strip()
        contact = request.form.get('contact', '').strip()

        if not all([title, salary, location, category]):
            flash('Title, Salary, Location aur Category required hai!')
            return render_template('post_job.html', categories=JOB_CATEGORIES, locations=LOCATIONS)

        conn = get_db()
        conn.execute('INSERT INTO jobs (company_id, title, location, salary, experience, category, description, skills, contact, posted_on) VALUES (?,?,?,?,?,?,?,?,?,?)',
            (session['company_id'], title, location, salary, experience, category, description, skills, contact, datetime.now().strftime('%Y-%m-%d')))
        conn.commit()
        conn.close()
        flash('Job posted successfully!')
        return redirect('/company-dashboard')
    return render_template('post_job.html', categories=JOB_CATEGORIES, locations=LOCATIONS)
@app.route('/check-db')
def check_db():
    conn = get_db()
    job_count = conn.execute('SELECT COUNT(*) as total FROM jobs').fetchone()
    jobs = conn.execute('SELECT id, title, company_id, location, category FROM jobs').fetchall()
    companies = conn.execute('SELECT id, company_name FROM companies').fetchall()
    conn.close()
    return f"<h2>Jobs: {job_count['total']}</h2><br><b>Jobs:</b> {jobs}<br><br><b>Companies:</b> {companies}"
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect('/admin')
        flash('Wrong Password!')
    if not session.get('admin'):
        return render_template('admin_login.html')
    conn = get_db()
    companies = conn.execute('SELECT * FROM companies ORDER BY id DESC').fetchall()
    jobs = conn.execute('SELECT j.*, c.company_name FROM jobs j JOIN companies c ON j.company_id = c.id ORDER BY j.id DESC').fetchall()
    apps = conn.execute('SELECT COUNT(*) as total FROM applications').fetchone()
    conn.close()
    return render_template('admin.html', companies=companies, jobs=jobs, apps=apps)

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('.', filename)

@app.route('/company-logout')
def company_logout():
    session.pop('company_id', None)
    session.pop('company_name', None)
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# if __name__ == '__main__':
# app.run(debug=False)
