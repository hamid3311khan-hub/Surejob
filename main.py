from flask import Flask, request, render_template, redirect, url_for, session, flash, send_from_directory
import sqlite3
import os
from werkzeug.utils import secure_filename
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io

app = Flask(__name__)
app.secret_key = 'surejob_secret_key_123'

UPLOAD_FOLDER = 'static/resumes'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_db():
    conn = sqlite3.connect('surejob.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            mobile TEXT,
            full_name TEXT,
            resume TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            company_name TEXT,
            mobile TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            location TEXT,
            salary TEXT,
            job_type TEXT,
            experience TEXT,
            openings INTEGER DEFAULT 1,
            requirements TEXT,
            skills TEXT,
            perks TEXT,
            company_id INTEGER,
            posted_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies (id)
        )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER,
            candidate_id INTEGER,
            applied_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobs (id),
            FOREIGN KEY (candidate_id) REFERENCES candidates (id)
        )''')
    conn.commit()
    conn.close()

with app.app_context():
    init_db()

def get_db_connection():
    conn = sqlite3.connect('surejob.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    conn = get_db_connection()
    jobs = conn.execute('''SELECT jobs.*, companies.company_name
        FROM jobs JOIN companies ON jobs.company_id = companies.id
        ORDER BY jobs.id DESC LIMIT 6''').fetchall()
    conn.close()
    return render_template('index.html', jobs=jobs)

@app.route('/jobs')
def jobs():
    search = request.args.get('search', '')
    location = request.args.get('location', '')
    job_type = request.args.get('job_type', '')
    
    conn = get_db_connection()
    query = "SELECT * FROM jobs WHERE 1=1"
    params = []
    
    if search:
        query += " AND (title LIKE ? OR company_name LIKE ?)"
        params.extend([f'%{search}%', f'%{search}%'])
    
    if location:
        query += " AND location LIKE ?"
        params.append(f'%{location}%')
        
    if job_type:
        query += " AND job_type = ?"
        params.append(job_type)
    
    query += " ORDER BY id DESC"
    jobs = conn.execute(query, params).fetchall()
    conn.close()
    
    return render_template('jobs.html', jobs=jobs, search=search, location=location, job_type=job_type)
    
@app.route('/job/<int:job_id>')
def job_detail(job_id):
    conn = get_db_connection()
    job = conn.execute('''SELECT jobs.*, companies.company_name
        FROM jobs JOIN companies ON jobs.company_id = companies.id
        WHERE jobs.id =?''', (job_id,)).fetchone()
    already_applied = False
    if 'user_id' in session and session['user_type'] == 'candidate':
        check = conn.execute('SELECT id FROM applications WHERE job_id =? AND candidate_id =?',
                           (job_id, session['user_id'])).fetchone()
        already_applied = True if check else False
    conn.close()
    return render_template('job_detail.html', job=job, already_applied=already_applied)

@app.route('/apply-job/<int:job_id>')
def apply_job(job_id):
    if 'user_id' not in session or session['user_type']!= 'candidate':
        return redirect(url_for('candidate_login'))
    conn = get_db_connection()
    candidate = conn.execute('SELECT resume FROM candidates WHERE id =?', (session['user_id'],)).fetchone()
    if not candidate['resume']:
        flash('Please upload your resume before applying', 'warning')
        conn.close()
        return redirect(url_for('candidate_dashboard'))
    existing = conn.execute('SELECT id FROM applications WHERE job_id =? AND candidate_id =?',
                          (job_id, session['user_id'])).fetchone()
    if existing:
        flash('You have already applied to this job', 'info')
    else:
        conn.execute('INSERT INTO applications (job_id, candidate_id) VALUES (?,?)',
                    (job_id, session['user_id']))
        conn.commit()
        flash('Applied successfully!', 'success')
    conn.close()
    return redirect(url_for('job_detail', job_id=job_id))

@app.route('/candidate/register', methods=['GET', 'POST'])
def candidate_register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        mobile = request.form.get('mobile')
        full_name = request.form.get('full_name')
        conn = get_db_connection()
        try:
            cursor = conn.execute('INSERT INTO candidates (email, password, mobile, full_name) VALUES (?,?,?,?)',
                         (email, password, mobile, full_name))
            user_id = cursor.lastrowid
            if 'resume' in request.files:
                file = request.files['resume']
                if file and file.filename!= '' and allowed_file(file.filename):
                    new_filename = secure_filename(f"user_{user_id}_{file.filename}")
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], new_filename))
                    conn.execute('UPDATE candidates SET resume =? WHERE id =?', (new_filename, user_id))
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('candidate_login'))
        except sqlite3.IntegrityError:
            flash('Email already exists', 'danger')
        finally:
            conn.close()
    return render_template('candidate_register.html')

@app.route('/candidate/login', methods=['GET', 'POST'])
def candidate_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM candidates WHERE email =? AND password =?',
                          (email, password)).fetchone()
        conn.close()
        if user:
            session['user_id'] = user['id']
            session['user_type'] = 'candidate'
            session['name'] = user['full_name'] if user['full_name'] else user['email'].split('@')[0]
            return redirect(url_for('candidate_dashboard'))
        else:
            flash('Invalid email or password', 'danger')
    return render_template('candidate_login.html')

@app.route('/candidate/dashboard')
def candidate_dashboard():
    if 'user_id' not in session or session['user_type']!= 'candidate':
        return redirect(url_for('candidate_login'))
    conn = get_db_connection()
    candidate = conn.execute('SELECT * FROM candidates WHERE id =?', (session['user_id'],)).fetchone()
    applications = conn.execute('''SELECT applications.*, jobs.title, jobs.location, companies.company_name
        FROM applications JOIN jobs ON applications.job_id = jobs.id
        JOIN companies ON jobs.company_id = companies.id
        WHERE applications.candidate_id =? ORDER BY applications.id DESC''', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('candidate_dashboard.html', candidate=candidate, applications=applications)

@app.route('/candidate/create-resume', methods=['GET', 'POST'])
def create_resume():
    if 'user_id' not in session or session['user_type']!= 'candidate':
        return redirect(url_for('candidate_login'))

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    conn = get_db_connection()
    candidate = conn.execute('SELECT * FROM candidates WHERE id =?', (session['user_id'],)).fetchone()

    if request.method == 'POST':
        try:
            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter

            full_name = request.form.get('full_name') or 'Candidate'
            email = request.form.get('email') or ''
            phone = request.form.get('phone') or ''

            p.setFont("Helvetica-Bold", 16)
            p.drawString(50, height - 50, full_name)
            p.setFont("Helvetica", 10)
            p.drawString(50, height - 70, f"Email: {email} | Phone: {phone}")
            y = height - 120

            sections = [("Summary", request.form.get('summary')), ("Education", request.form.get('education')),
                        ("Experience", request.form.get('experience')), ("Skills", request.form.get('skills'))]
            for title, content in sections:
                if content:
                    p.setFont("Helvetica-Bold", 12)
                    p.drawString(50, y, title)
                    y -= 20
                    p.setFont("Helvetica", 10)
                    for line in content.split('\n'):
                        if y < 50: p.showPage(); y = height - 50
                        p.drawString(50, y, line[:90])
                        y -= 15
                    y -= 10
            p.save()
            buffer.seek(0)
            filename = secure_filename(f"user_{session['user_id']}_generated.pdf")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            with open(filepath, 'wb') as f: f.write(buffer.getvalue())
            conn.execute('UPDATE candidates SET resume =? WHERE id =?', (filename, session['user_id']))
            conn.commit()
            flash('Resume created successfully!', 'success')
            return redirect(url_for('candidate_dashboard'))
        except Exception as e:
            flash(f'Error creating resume: {str(e)}', 'danger')
        finally:
            conn.close()

    conn.close()
    return render_template('create_resume.html', candidate=candidate)

@app.route('/candidate/upload-resume', methods=['POST'])
def upload_resume():
    if 'user_id' not in session or session['user_type']!= 'candidate':
        return redirect(url_for('candidate_login'))
    
    if 'resume' not in request.files:
        flash('No file selected', 'danger')
        return redirect(url_for('candidate_dashboard'))
    
    file = request.files['resume']
    if file.filename == '':
        flash('No file selected', 'danger')
        return redirect(url_for('candidate_dashboard'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(f"user_{session['user_id']}_{file.filename}")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        conn = get_db_connection()
        conn.execute('UPDATE candidates SET resume =? WHERE id =?', (filename, session['user_id']))
        conn.commit()
        conn.close()
        flash('Resume uploaded successfully!', 'success')
    else:
        flash('Invalid file. Only PDF, DOC, DOCX allowed', 'danger')
    
    return redirect(url_for('candidate_dashboard'))
    
@app.route('/company/register', methods=['GET', 'POST'])
def company_register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        company_name = request.form.get('company_name')
        mobile = request.form.get('mobile')
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO companies (email, password, company_name, mobile) VALUES (?,?,?,?)',
                         (email, password, company_name, mobile))
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('company_login'))
        except sqlite3.IntegrityError:
            flash('Email already exists', 'danger')
        finally:
            conn.close()
    return render_template('company_register.html')

@app.route('/company/login', methods=['GET', 'POST'])
def company_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM companies WHERE email =? AND password =?',
                          (email, password)).fetchone()
        conn.close()
        if user:
            session['user_id'] = user['id']
            session['user_type'] = 'company'
            session['name'] = user['company_name']
            return redirect(url_for('company_dashboard'))
        else:
            flash('Invalid email or password', 'danger')
    return render_template('company_login.html')

@app.route('/company/dashboard')
def company_dashboard():
    if 'user_id' not in session or session['user_type']!= 'company':
        return redirect(url_for('company_login'))
    conn = get_db_connection()
    jobs = conn.execute('SELECT * FROM jobs WHERE company_id =? ORDER BY id DESC',
                       (session['user_id'],)).fetchall()
    total_jobs = len(jobs)
    total_apps = conn.execute('''SELECT COUNT(*) as count FROM applications
        JOIN jobs ON applications.job_id = jobs.id WHERE jobs.company_id =?''',
        (session['user_id'],)).fetchone()['count']
    conn.close()
    return render_template('company_dashboard.html', jobs=jobs, total_jobs=total_jobs, total_apps=total_apps)

@app.route('/post-job', methods=['GET', 'POST'])
def post_job():
    if 'user_id' not in session or session['user_type']!= 'company':
        return redirect(url_for('company_login'))
    if request.method == 'POST':
        conn = get_db_connection()
        conn.execute('''INSERT INTO jobs (title, description, location, salary, job_type, experience,
                            openings, requirements, skills, perks, company_id)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)''', (
            request.form.get('title'), request.form.get('description'), request.form.get('location'),
            request.form.get('salary'), request.form.get('job_type'), request.form.get('experience'),
            request.form.get('openings'), request.form.get('requirements'), request.form.get('skills'),
            request.form.get('perks'), session['user_id']))
        conn.commit()
        conn.close()
        flash('Job posted successfully!', 'success')
        return redirect(url_for('company_dashboard'))
    return render_template('post_job.html')

@app.route('/job-applications/<int:job_id>')
def job_applications(job_id):
    if 'user_id' not in session or session['user_type']!= 'company':
        return redirect(url_for('company_login'))
    conn = get_db_connection()
    job = conn.execute('SELECT * FROM jobs WHERE id =? AND company_id =?',
                      (job_id, session['user_id'])).fetchone()
    if not job:
        flash('Job not found', 'danger')
        return redirect(url_for('company_dashboard'))
    applications = conn.execute('''SELECT applications.*, candidates.full_name, candidates.email, candidates.mobile, candidates.resume
        FROM applications JOIN candidates ON applications.candidate_id = candidates.id
        WHERE applications.job_id =? ORDER BY applications.id DESC''', (job_id,)).fetchall()
    conn.close()
    return render_template('job_applications.html', job=job, applications=applications)

@app.route('/company/download-resume/<int:candidate_id>')
def download_resume(candidate_id):
    if 'user_id' not in session: return redirect(url_for('candidate_login'))
    conn = get_db_connection()
    candidate = conn.execute('SELECT resume FROM candidates WHERE id =?', (candidate_id,)).fetchone()
    conn.close()
    if candidate and candidate['resume']:
        return send_from_directory(app.config['UPLOAD_FOLDER'], candidate['resume'],
                                 as_attachment=request.args.get('download')=='1')
    flash('Resume not found', 'danger')
    return redirect(request.referrer or url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
