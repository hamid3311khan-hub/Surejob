from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'surejob-super-secret-key-2026'

# ==================== DATABASE SETUP ====================
def init_db():
    conn = sqlite3.connect('surejob.db')
    c = conn.cursor()
    
    # Companies Table
    c.execute('''CREATE TABLE IF NOT EXISTS companies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        phone TEXT,
        industry TEXT,
        address TEXT,
        description TEXT,
        website TEXT,
        logo TEXT,
        founded TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Baaki tables ka code same rehne de...
# ==================== DATABASE SETUP ====================
def init_db():
    conn = sqlite3.connect('surejob.db')
    c = conn.cursor()

    # Companies Table
    c.execute('''CREATE TABLE IF NOT EXISTS companies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        phone TEXT,
        industry TEXT,
        address TEXT,
        description TEXT,
        website TEXT,
        logo TEXT,
        founded TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # Candidates Table
    c.execute('''CREATE TABLE IF NOT EXISTS candidates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        phone TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # Jobs Table
    c.execute('''CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        job_type TEXT,
        experience TEXT,
        location TEXT,
        openings INTEGER DEFAULT 1,
        salary TEXT,
        description TEXT,
        requirements TEXT,
        skills TEXT,
        perks TEXT,
        status TEXT DEFAULT 'Active',
        posted_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (company_id) REFERENCES companies (id)
    )''')

    # Applications Table
    c.execute('''CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL,
        candidate_id INTEGER NOT NULL,
        status TEXT DEFAULT 'Applied',
        applied_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (job_id) REFERENCES jobs (id),
        FOREIGN KEY (candidate_id) REFERENCES candidates (id)
    )''')

    # Saved Jobs Table
    c.execute('''CREATE TABLE IF NOT EXISTS saved_jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL,
        candidate_id INTEGER NOT NULL,
        saved_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (job_id) REFERENCES jobs (id),
        FOREIGN KEY (candidate_id) REFERENCES candidates (id)
    )''')

    conn.commit()
    conn.close()

init_db()

# ==================== HOME & JOB LISTING ====================
@app.route('/')
def index():
    conn = sqlite3.connect('surejob.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('''SELECT j.*, c.company_name, c.logo as company_logo
                 FROM jobs j JOIN companies c ON j.company_id = c.id
                 WHERE j.status = 'Active' ORDER BY j.id DESC LIMIT 6''')
    jobs = c.fetchall()
    conn.close()
    return render_template('index.html', jobs=jobs)

@app.route('/jobs')
def jobs():
    conn = sqlite3.connect('surejob.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('''SELECT j.*, c.company_name, c.logo as company_logo
                 FROM jobs j JOIN companies c ON j.company_id = c.id
                 WHERE j.status = 'Active' ORDER BY j.id DESC''')
    jobs = c.fetchall()
    conn.close()
    return render_template('jobs.html', jobs=jobs)

@app.route('/job/<int:job_id>')
def job_detail(job_id):
    conn = sqlite3.connect('surejob.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('''SELECT j.*, c.company_name, c.logo as company_logo, c.id as company_id
                 FROM jobs j JOIN companies c ON j.company_id = c.id
                 WHERE j.id =?''', (job_id,))
    job = c.fetchone()
    conn.close()
    if not job:
        return "Job not found", 404

    already_applied = False
    if 'candidate_id' in session:
        c = sqlite3.connect('surejob.db').cursor()
        c.execute('SELECT id FROM applications WHERE job_id =? AND candidate_id =?',
                  (job_id, session['candidate_id']))
        already_applied = c.fetchone() is not None
        c.connection.close()

    return render_template('job_detail.html', job=job, already_applied=already_applied)

# ==================== CANDIDATE ROUTES ====================
@app.route('/candidate-register', methods=['GET', 'POST'])
def candidate_register():
    if request.method == 'POST':
        data = request.form
        hashed_pw = generate_password_hash(data['password'])
        conn = sqlite3.connect('surejob.db')
        c = conn.cursor()
        try:
            c.execute('INSERT INTO candidates (name, email, password, phone) VALUES (?,?,?,?)',
                     (data['name'], data['email'], hashed_pw, data.get('phone')))
            candidate_id = c.lastrowid
            conn.commit()
            conn.close()
            session['candidate_id'] = candidate_id
            session['name'] = data['name']
            session['email'] = data['email']
            session['phone'] = data.get('phone')
            session['user_type'] = 'candidate'
            return redirect('/candidate-dashboard')
        except sqlite3.IntegrityError:
            conn.close()
            return render_template('candidate_register.html', error='Email already exists')
    return render_template('candidate_register.html')

@app.route('/candidate-login', methods=['GET', 'POST'])
def candidate_login():
    if request.method == 'POST':
        data = request.form
        conn = sqlite3.connect('surejob.db')
        c = conn.cursor()
        c.execute('SELECT id, name, password, email, phone FROM candidates WHERE email =?', (data['email'],))
        user = c.fetchone()
        conn.close()
        if user and check_password_hash(user[2], data['password']):
            session['candidate_id'] = user[0]
            session['name'] = user[1]
            session['email'] = user[3]
            session['phone'] = user[4]
            session['user_type'] = 'candidate'
            return redirect('/candidate-dashboard')
        return render_template('candidate_login.html', error='Invalid credentials')
    return render_template('candidate_login.html')

@app.route('/candidate-dashboard')
def candidate_dashboard():
    if 'candidate_id' not in session:
        return redirect('/candidate-login')
    conn = sqlite3.connect('surejob.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('''SELECT a.*, j.title as job_title, j.location, c.company_name
                 FROM applications a
                 JOIN jobs j ON a.job_id = j.id
                 JOIN companies c ON j.company_id = c.id
                 WHERE a.candidate_id =? ORDER BY a.id DESC''', (session['candidate_id'],))
    applications = c.fetchall()
    conn.close()
    return render_template('candidate_dashboard.html', applications=applications)

@app.route('/download-resume/<filename>')
def download_resume(filename):
    return send_from_directory('static/uploads/resumes', filename)

@app.route('/apply-job/<int:job_id>')
def apply_job(job_id):
    if 'candidate_id' not in session:
        return redirect('/candidate-login')
    conn = sqlite3.connect('surejob.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO applications (job_id, candidate_id) VALUES (?,?)',
                  (job_id, session['candidate_id']))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()
    return redirect(f'/job/{job_id}')

# ==================== COMPANY ROUTES ====================
@app.route('/company-register', methods=['GET', 'POST'])
def company_register():
    if request.method == 'POST':
        data = request.form
        hashed_pw = generate_password_hash(data['password'])
        conn = sqlite3.connect('surejob.db')
        c = conn.cursor()
        try:
            c.execute('''INSERT INTO companies (company_name, email, password, phone, industry, address, website)
                        VALUES (?,?,?,?,?,?,?)''',
                     (data['company_name'], data['email'], hashed_pw,
                      data.get('phone'), data.get('industry'), data.get('address'), data.get('website')))
            company_id = c.lastrowid
            conn.commit()
            conn.close()
            session['company_id'] = company_id
            session['company_name'] = data['company_name']
            session['user_type'] = 'company'
            return redirect('/company-dashboard')
        except sqlite3.IntegrityError:
            conn.close()
            return render_template('company_register.html', error='Email already exists')
    return render_template('company_register.html')

@app.route('/company-login', methods=['GET', 'POST'])
def company_login():
    if request.method == 'POST':
        data = request.form
        conn = sqlite3.connect('surejob.db')
        c = conn.cursor()
        c.execute('SELECT id, company_name, password FROM companies WHERE email =?', (data['email'],))
        company = c.fetchone()
        conn.close()
        if company and check_password_hash(company[2], data['password']):
            session['company_id'] = company[0]
            session['company_name'] = company[1]
            session['user_type'] = 'company'
            return redirect('/company-dashboard')
        return render_template('company_login.html', error='Invalid credentials')
    return render_template('company_login.html')

@app.route('/company-dashboard')
def company_dashboard():
    if 'company_id' not in session:
        return redirect('/company-login')
    conn = sqlite3.connect('surejob.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute('''SELECT j.*,
                 (SELECT COUNT(*) FROM applications WHERE job_id = j.id) as app_count
                 FROM jobs j WHERE j.company_id =? ORDER BY j.posted_on DESC''',
                 (session['company_id'],))
    jobs = c.fetchall()
    conn.close()
    return render_template('company_dashboard.html', jobs=jobs)

@app.route('/company/<int:company_id>')
def company_profile(company_id):
    conn = sqlite3.connect('surejob.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM companies WHERE id =?', (company_id,))
    company = c.fetchone()
    if not company:
        return "Company not found", 404
    c.execute("SELECT * FROM jobs WHERE company_id =? AND status = 'Active' ORDER BY id DESC", (company_id,))
    jobs = c.fetchall()
    conn.close()
    return render_template('company.html', company=company, jobs=jobs)

@app.route('/post-job', methods=['GET', 'POST'])
def post_job():
    if 'company_id' not in session:
        return redirect('/company-login')
    if request.method == 'POST':
        data = request.form
        company_id = session['company_id']
        salary = data.get('salary', 'Not Disclosed')
        conn = sqlite3.connect('surejob.db')
        c = conn.cursor()
        c.execute('''INSERT INTO jobs (company_id, title, job_type, experience, location, openings,
                     salary, description, requirements, skills, perks, status)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''',
                 (company_id, data.get('title'), data.get('job_type'), data.get('experience'),
                  data.get('location'), data.get('openings'), salary, data.get('description'),
                  data.get('requirements'), data.get('skills'), data.get('perks'), 'Active'))
        conn.commit()
        conn.close()
        return redirect('/company-dashboard')
    return render_template('post_job.html')

@app.route('/edit-job/<int:job_id>', methods=['GET', 'POST'])
def edit_job(job_id):
    if 'company_id' not in session:
        return redirect('/company-login')

    conn = sqlite3.connect('surejob.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    if request.method == 'POST':
        data = request.form
        c.execute('''UPDATE jobs SET
                     title=?, job_type=?, experience=?, location=?,
                     openings=?, salary=?, description=?, requirements=?,
                     skills=?, perks=?
                     WHERE id=? AND company_id=?''',
                 (data.get('title'),
                  data.get('job_type'),
                  data.get('experience'),
                  data.get('location'),
                  data.get('openings'),
                  data.get('salary'),
                  data.get('description'),
                  data.get('requirements'),
                  data.get('skills', ''),
                  data.get('perks', ''),
                  job_id,
                  session['company_id']))
        conn.commit()
        conn.close()
        return redirect('/company-dashboard')

    c.execute('SELECT * FROM jobs WHERE id=? AND company_id=?', (job_id, session['company_id']))
    job = c.fetchone()
    conn.close()
    if not job:
        return "Job not found", 404
    return render_template('edit_job.html', job=job)

@app.route('/job-applications/<int:job_id>')
def job_applications(job_id):
    if 'company_id' not in session:
        return redirect('/company-login')
    conn = sqlite3.connect('surejob.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM jobs WHERE id=? AND company_id=?', (job_id, session['company_id']))
    job = c.fetchone()
    if not job:
        conn.close()
        return "Job not found", 404
    c.execute('''SELECT a.*, c.name as candidate_name, c.email as candidate_email, c.phone as candidate_phone
                 FROM applications a
                 JOIN candidates c ON a.candidate_id = c.id
                 WHERE a.job_id =? ORDER BY a.id DESC''', (job_id,))
    applications = c.fetchall()
    conn.close()
    return render_template('job_applications.html', applications=applications, job=job)

@app.route('/update-application-status/<int:app_id>', methods=['POST'])
def update_application_status(app_id):
    if 'company_id' not in session:
        return redirect('/company-login')
    status = request.form.get('status')
    conn = sqlite3.connect('surejob.db')
    c = conn.cursor()
    c.execute('''UPDATE applications SET status=? WHERE id=? AND job_id IN
                 (SELECT id FROM jobs WHERE company_id=?)''', (status, app_id, session['company_id']))
    conn.commit()
    conn.close()
    return redirect(request.referrer)

@app.route('/delete-job/<int:job_id>')
def delete_job(job_id):
    if 'company_id' not in session:
        return redirect('/company-login')
    conn = sqlite3.connect('surejob.db')
    c = conn.cursor()
    c.execute('DELETE FROM jobs WHERE id =? AND company_id =?', (job_id, session['company_id']))
    conn.commit()
    conn.close()
    return redirect('/company-dashboard')

# ==================== LOGOUT ====================
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/company-logout')
def company_logout():
    session.clear()
    return redirect('/')

# ==================== RUN APP ====================
# ==================== AUTO CHECK ROUTE ====================
@app.route('/check-project')
def check_project():
    import py_compile
    import re
    import os
    
    result = []
    result.append("=== SUREJOB PROJECT CHECK ===\n")
    
    # 1. Python Syntax Check
    try:
        py_compile.compile('main.py', doraise=True)
        result.append("✅ main.py - Syntax OK")
    except Exception as e:
        result.append(f"❌ main.py - ERROR: {str(e)}")
    
    # 2. Template Files Check
    if os.path.exists('templates'):
        templates = os.listdir('templates')
        result.append(f"\n✅ Templates Found: {len(templates)} files")
        
        for file in templates:
            if file.endswith('.html'):
                filepath = os.path.join('templates', file)
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                ifs = len(re.findall(r'{%\s*if\s+', content))
                endifs = len(re.findall(r'{%\s*endif\s*%}', content))
                
                if ifs == endifs:
                    result.append(f"✅ {file} - Jinja OK")
                else:
                    result.append(f"❌ {file} - if/endif mismatch: {ifs} if, {endifs} endif")
    else:
        result.append("❌ templates folder missing")
    
    # 3. Database Check
    if os.path.exists('surejob.db'):
        result.append("\n✅ surejob.db - Database exists")
    else:
        result.append("\n⚠️ surejob.db - Not created yet")
    
    result.append("\n=== CHECK COMPLETE ===")
    return "<br>".join(result)
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
