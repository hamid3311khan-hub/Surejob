from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, jsonify
import sqlite3
from datetime import datetime, timedelta
import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", 'surejob_v3_2026_secure_key_change_this')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024

UPLOAD_FOLDER = 'static/logos'
RESUME_FOLDER = 'static/resumes'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESUME_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}
JOB_CATEGORIES = ['IT Software', 'Sales & Marketing', 'BPO / Telecaller', 'Accounts & Finance', 'HR & Admin', 'Engineering', 'Customer Support', 'Operations', 'Other']
LOCATIONS = ['Mumbai', 'Delhi', 'Bangalore', 'Pune', 'Hyderabad', 'Chennai', 'Kolkata', 'Noida', 'Gurgaon', 'Ahmedabad', 'Remote']
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    conn = sqlite3.connect('surejob.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""CREATE TABLE IF NOT EXISTS companies (
        id INTEGER PRIMARY KEY,
        company_name TEXT,
        gst_no TEXT,
        email TEXT UNIQUE,
        phone TEXT,
        password TEXT,
        logo TEXT,
        registered_on TEXT,
        plan_expiry TEXT,
        status TEXT DEFAULT 'Active')""")

    conn.execute("""CREATE TABLE IF NOT EXISTS candidates (
        id INTEGER PRIMARY KEY,
        name TEXT,
        email TEXT UNIQUE,
        phone TEXT,
        password TEXT,
        resume TEXT,
        registered_on TEXT)""")

    conn.execute("""CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY,
        company_id INTEGER,
        title TEXT,
        location TEXT,
        salary TEXT,
        experience TEXT,
        category TEXT,
        description TEXT,
        skills TEXT,
        contact TEXT,
        posted_on TEXT,
        views INTEGER DEFAULT 0,
        featured INTEGER DEFAULT 0,
        status TEXT DEFAULT 'Active')""")

    conn.execute("""CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY,
        job_id INTEGER,
        name TEXT,
        email TEXT,
        phone TEXT,
        resume TEXT,
        cover_letter TEXT,
        applied_on TEXT,
        status TEXT DEFAULT 'New')""")

    conn.execute("""CREATE TABLE IF NOT EXISTS saved_jobs (
        id INTEGER PRIMARY KEY,
        email TEXT,
        job_id INTEGER,
        saved_on TEXT,
        UNIQUE(email, job_id))""")

    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    try:
        conn = get_db()
        search = request.args.get('q', '').strip()
        location = request.args.get('location', 'All Locations')
        category = request.args.get('category', 'All Categories')
        experience = request.args.get('exp', '')
        remote = request.args.get('remote', '')

        query = '''
            SELECT j.id, j.title, j.description, j.salary, j.location, j.category, j.skills, j.experience, j.posted_on, j.featured,
                   c.company_name, c.logo
            FROM jobs j
            LEFT JOIN companies c ON j.company_id = c.id
            WHERE j.status = 'Active'
        '''
        params = []

        if search:
            query += ''' AND (j.title LIKE? OR j.description LIKE? OR j.skills LIKE? OR c.company_name LIKE?)'''
            like_search = f'%{search}%'
            params.extend([like_search, like_search, like_search, like_search])

        if location and location!= 'All Locations':
            query += ' AND j.location =?'
            params.append(location)

        if remote == '1':
            query += ' AND j.location =?'
            params.append('Remote')

        if category and category!= 'All Categories':
            query += ' AND j.category =?'
            params.append(category)

        if experience:
            query += ' AND j.experience LIKE?'
            params.append(f'%{experience}%')

        query += ' ORDER BY j.featured DESC, j.id DESC LIMIT 50'
        jobs = conn.execute(query, params).fetchall()

        top_companies = conn.execute('''
            SELECT c.company_name, c.logo, COUNT(j.id) as job_count
            FROM companies c
            JOIN jobs j ON c.id = j.company_id
            WHERE j.status='Active'
            GROUP BY c.id
            ORDER BY job_count DESC LIMIT 8
        ''').fetchall()

        conn.close()
        return render_template('index.html',
            jobs=jobs, locations=LOCATIONS, categories=JOB_CATEGORIES,
            search=search, location=location, category=category,
            experience=experience, remote=remote, top_companies=top_companies)
    except Exception as e:
        print(f"Homepage Error: {e}")
        return f"Error: {e}", 500

@app.route('/job/<int:job_id>', methods=['GET', 'POST'])
def job_detail(job_id):
    conn = get_db()
    conn.execute('UPDATE jobs SET views = views + 1 WHERE id=?', (job_id,))
    conn.commit()

    job = conn.execute('''
        SELECT j.*, c.company_name, c.logo, c.email as company_email
        FROM jobs j LEFT JOIN companies c ON j.company_id = c.id
        WHERE j.id=?
    ''', (job_id,)).fetchone()

    if not job:
        conn.close()
        return "Job Not Found", 404

    similar_jobs = conn.execute('''
        SELECT j.id, j.title, j.location, c.company_name
        FROM jobs j LEFT JOIN companies c ON j.company_id = c.id
        WHERE j.category=? AND j.id!=? AND j.status='Active'
        LIMIT 4
    ''', (job['category'], job_id)).fetchall()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()

        if not all([name, email, phone]):
            flash('Name, Email aur Phone required hai!', 'error')
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
        flash('Application submitted successfully!', 'success')
        conn.close()
        return redirect(f'/job/{job_id}')

    conn.close()
    return render_template('job_detail.html', job=job, similar_jobs=similar_jobs)

@app.route('/save-job/<int:job_id>', methods=['POST'])
def save_job(job_id):
    email = request.json.get('email', '').strip()
    if not email:
        return jsonify({'success': False, 'msg': 'Email required'})

    conn = get_db()
    try:
        conn.execute('INSERT INTO saved_jobs (email, job_id, saved_on) VALUES (?,?,?)',
            (email, job_id, datetime.now().strftime('%Y-%m-%d')))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'msg': 'Job saved!'})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'success': False, 'msg': 'Already saved'})

# ===== CANDIDATE ROUTES =====
@app.route('/candidate-register', methods=['GET', 'POST'])
def candidate_register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '').strip()

        if not all([name, email, phone, password]):
            flash('Sabhi fields required hain!', 'error')
            return render_template('candidate_register.html')

        hashed_password = generate_password_hash(password)
        conn = get_db()
        try:
            conn.execute('INSERT INTO candidates (name, email, phone, password, registered_on) VALUES (?,?,?,?,?)',
                (name, email, phone, hashed_password, datetime.now().strftime('%Y-%m-%d %H:%M')))
            conn.commit()
            flash('Registration successful! Ab login karo.', 'success')
            conn.close()
            return redirect('/candidate-login')
        except sqlite3.IntegrityError:
            conn.close()
            flash('Ye Email already registered hai!', 'error')
        except Exception as e:
            conn.close()
            flash(f'Error: {str(e)}', 'error')
    return render_template('candidate_register.html')

@app.route('/candidate-login', methods=['GET', 'POST'])
def candidate_login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        if not email or not password:
            flash('Email aur Password dono dalo!', 'error')
            return render_template('candidate_login.html')

        conn = get_db()
        candidate = conn.execute('SELECT * FROM candidates WHERE email=?', (email,)).fetchone()
        conn.close()

        if candidate and check_password_hash(candidate['password'], password):
            session['candidate_id'] = candidate['id']
            session['candidate_name'] = candidate['name']
            session['candidate_email'] = candidate['email']
            flash('Login successful!', 'success')
            return redirect('/candidate-dashboard')
        flash('Invalid credentials!', 'error')
    return render_template('candidate_login.html')

@app.route('/candidate-dashboard')
def candidate_dashboard():
    if 'candidate_id' not in session:
        return redirect('/candidate-login')

    conn = get_db()
    applications = conn.execute('''
        SELECT a.*, j.title, j.location, j.salary, c.company_name
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        LEFT JOIN companies c ON j.company_id = c.id
        WHERE a.email =?
        ORDER BY a.id DESC
    ''', (session['candidate_email'],)).fetchall()
    conn.close()

    return render_template('candidate_dashboard.html', applications=applications)

@app.route('/candidate-logout')
def candidate_logout():
    session.pop('candidate_id', None)
    session.pop('candidate_name', None)
    session.pop('candidate_email', None)
    flash('Logged out successfully', 'success')
    return redirect('/')

@app.route('/quick-apply/<int:job_id>', methods=['POST'])
def quick_apply(job_id):
    if 'candidate_id' not in session:
        flash('Pehle login karo!', 'error')
        return redirect('/candidate-login')

    conn = get_db()
    existing = conn.execute('SELECT id FROM applications WHERE job_id=? AND email=?',
                           (job_id, session['candidate_email'])).fetchone()
    if existing:
        flash('Aap is job pe already apply kar chuke ho!', 'error')
        conn.close()
        return redirect(f'/job/{job_id}')

    candidate = conn.execute('SELECT * FROM candidates WHERE id=?', (session['candidate_id'],)).fetchone()

    conn.execute('INSERT INTO applications (job_id, name, email, phone, resume, applied_on) VALUES (?,?,?,?,?,?)',
        (job_id, candidate['name'], candidate['email'], candidate['phone'],
         candidate['resume'] or '', datetime.now().strftime('%Y-%m-%d %H:%M')))
    conn.commit()
    conn.close()
    flash('1-Click me apply ho gaya! Best of luck 🎉', 'success')
    return redirect(f'/job/{job_id}')

# ===== COMPANY ROUTES =====
@app.route('/company-register', methods=['GET', 'POST'])
def company_register():
    if request.method == 'POST':
        company_name = request.form.get('company_name', '').strip()
        gst_no = request.form.get('gst_no', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '').strip()

        if not all([company_name, email, phone, password]):
            flash('Company Name, Email, Phone aur Password required hai!', 'error')
            return render_template('company_register.html')

        hashed_password = generate_password_hash(password)

        logo = request.files.get('logo')
        logo_path = ''
        if logo and logo.filename and allowed_file(logo.filename):
            filename = secure_filename(f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{logo.filename}")
            logo_path = os.path.join(UPLOAD_FOLDER, filename)
            logo.save(logo_path)

        conn = get_db()
        try:
            conn.execute('INSERT INTO companies (company_name, gst_no, email, phone, password, logo, registered_on, plan_expiry) VALUES (?,?,?,?,?,?,?,?)',
                (company_name, gst_no, email, phone, hashed_password, logo_path,
                 datetime.now().strftime('%Y-%m-%d'),
                 (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')))
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            conn.close()
            return redirect('/company-login')
        except sqlite3.IntegrityError:
            conn.close()
            flash('Ye Email already registered hai!', 'error')
        except Exception as e:
            conn.close()
            flash(f'Error: {str(e)}', 'error')
    return render_template('company_register.html')

@app.route('/company-login', methods=['GET', 'POST'])
def company_login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        if not email or not password:
            flash('Email aur Password dono dalo!', 'error')
            return render_template('company_login.html')

        conn = get_db()
        company = conn.execute('SELECT * FROM companies WHERE email=?', (email,)).fetchone()
        conn.close()

        if company and check_password_hash(company['password'], password):
            session['company_id'] = company['id']
            session['company_name'] = company['company_name']
            return redirect('/company-dashboard')
        flash('Invalid credentials!', 'error')
    return render_template('company_login.html')

@app.route('/company-dashboard')
def company_dashboard():
    if 'company_id' not in session:
        return redirect('/company-login')
    conn = get_db()
    company = conn.execute('SELECT * FROM companies WHERE id=?', (session['company_id'],)).fetchone()

    stats = {
        'total_jobs': conn.execute('SELECT COUNT(*) as c FROM jobs WHERE company_id=? AND status="Active"', (session['company_id'],)).fetchone()['c'],
        'total_apps': conn.execute('SELECT COUNT(*) as c FROM applications a JOIN jobs j ON a.job_id=j.id WHERE j.company_id=?', (session['company_id'],)).fetchone()['c'],
        'total_views': conn.execute('SELECT SUM(views) as c FROM jobs WHERE company_id=?', (session['company_id'],)).fetchone()['c'] or 0
    }

    jobs = conn.execute('''
        SELECT j.*, COUNT(a.id) as app_count
        FROM jobs j
        LEFT JOIN applications a ON j.id = a.job_id
        WHERE j.company_id=?
        GROUP BY j.id
        ORDER BY j.id DESC
    ''', (session['company_id'],)).fetchall()

    conn.close()
    return render_template('company_dashboard.html', jobs=jobs, company=company, stats=stats)

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
            flash('Title, Salary, Location aur Category required hai!', 'error')
            return render_template('post_job.html', categories=JOB_CATEGORIES, locations=LOCATIONS)

        conn = get_db()
        conn.execute('INSERT INTO jobs (company_id, title, location, salary, experience, category, description, skills, contact, posted_on) VALUES (?,?,?,?,?,?,?,?,?,?)',
            (session['company_id'], title, location, salary, experience, category, description, skills, contact, datetime.now().strftime('%Y-%m-%d')))
        conn.commit()
        conn.close()
        flash('Job posted successfully!', 'success')
        return redirect('/company-dashboard')
    return render_template('post_job.html', categories=JOB_CATEGORIES, locations=LOCATIONS)

@app.route('/edit-job/<int:job_id>', methods=['GET', 'POST'])
def edit_job(job_id):
    if 'company_id' not in session:
        return redirect('/company-login')
    conn = get_db()
    job = conn.execute('SELECT * FROM jobs WHERE id=? AND company_id=?', (job_id, session['company_id'])).fetchone()
    if not job:
        conn.close()
        flash('Job not found!', 'error')
        return redirect('/company-dashboard')
    if request.method == 'POST':
        conn.execute('''UPDATE jobs SET title=?, description=?, salary=?, location=?,
                        category=?, experience=?, skills=?, contact=? WHERE id=?''',
                    (request.form['title'], request.form['description'], request.form['salary'],
                     request.form['location'], request.form['category'], request.form.get('experience',''),
                     request.form.get('skills',''), request.form.get('contact',''), job_id))
        conn.commit()
        conn.close()
        flash('Job updated successfully!', 'success')
        return redirect('/company-dashboard')
    conn.close()
    return render_template('edit_job.html', job=job, categories=JOB_CATEGORIES, locations=LOCATIONS)

@app.route('/delete-job/<int:job_id>')
def delete_job(job_id):
    if 'company_id' not in session:
        return redirect('/company-login')
    conn = get_db()
    conn.execute('DELETE FROM jobs WHERE id=? AND company_id=?', (job_id, session['company_id']))
    conn.commit()
    conn.close()
    flash('Job deleted successfully!', 'success')
    return redirect('/company-dashboard')

@app.route('/job-applications/<int:job_id>')
def job_applications(job_id):
    if 'company_id' not in session:
        return redirect('/company-login')
    conn = get_db()
    job = conn.execute('SELECT * FROM jobs WHERE id=? AND company_id=?', (job_id, session['company_id'])).fetchone()
    if not job:
        conn.close()
        flash('Job not found!', 'error')
        return redirect('/company-dashboard')
    applications = conn.execute('SELECT * FROM applications WHERE job_id=? ORDER BY id DESC', (job_id,)).fetchall()
    conn.close()
    return render_template('job_applications.html', job=job, applications=applications)

@app.route('/update-status/<int:app_id>/<status>')
def update_status(app_id, status):
    if 'company_id' not in session:
        return redirect('/company-login')

    if status not in ['Shortlisted', 'Interview', 'Rejected']:
        flash('Invalid status!', 'error')
        return redirect('/company-dashboard')

    conn = get_db()
    app_data = conn.execute('''
        SELECT a.id, a.job_id, a.email, a.name, j.title, j.company_id
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        WHERE a.id =? AND j.company_id =?
    ''', (app_id, sessi
