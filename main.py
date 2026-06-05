from flask import Flask, render_template, request, redirect, url_for, session, flash, g
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash
from job_routes import job_bp
from column import column_bp
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'surejob-v3-final')

# Register Blueprints
app.register_blueprint(job_bp)
app.register_blueprint(column_bp)

def get_db():
    if 'db' not in g:
        g.db = psycopg2.connect(os.environ.get('DATABASE_URL'), cursor_factory=RealDictCursor)
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        c = db.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password TEXT NOT NULL, role TEXT NOT NULL,
            location TEXT, skills TEXT, experience TEXT, phone TEXT, education TEXT, about TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS jobs (
            id SERIAL PRIMARY KEY, company_id INTEGER NOT NULL, title TEXT NOT NULL,
            description TEXT NOT NULL, location TEXT NOT NULL, salary TEXT NOT NULL, job_type TEXT NOT NULL,
            skills_required TEXT, experience_required TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES users (id)
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS applications (
            id SERIAL PRIMARY KEY, job_id INTEGER NOT NULL, candidate_id INTEGER NOT NULL,
            status TEXT DEFAULT 'Applied', interview_date TEXT, applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobs (id), FOREIGN KEY (candidate_id) REFERENCES users (id),
            UNIQUE(job_id, candidate_id)
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS saved_jobs (
            id SERIAL PRIMARY KEY, candidate_id INTEGER NOT NULL, job_id INTEGER NOT NULL,
            saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (candidate_id) REFERENCES users (id),
            FOREIGN KEY (job_id) REFERENCES jobs (id), UNIQUE(candidate_id, job_id)
        )''')
        try:
            c.execute("INSERT INTO users (name, email, password, role) VALUES (%s,%s,%s,%s) ON CONFLICT (email) DO NOTHING",
                      ('Admin', 'admin@surejob.com', generate_password_hash('admin123'), 'admin'))
            db.commit()
        except Exception as e:
            db.rollback()
        finally:
            c.close()

# DB BANAYEGA RENDER PE
with app.app_context():
    init_db()

@app.route('/')
def index():
    db = get_db()
    c = db.cursor()
    c.execute("SELECT j.*, u.name as company_name FROM jobs j JOIN users u ON j.company_id = u.id ORDER BY j.id DESC LIMIT 8")
    jobs = c.fetchall()
    c.close()
    return render_template('index.html', jobs=jobs)

@app.route('/candidate/register', methods=['GET', 'POST'])
def candidate_register():
    if request.method == 'POST':
        db = get_db()
        c = db.cursor()
        try:
            c.execute("INSERT INTO users (name, email, password, role, location, skills, experience, phone, education, about) VALUES (%s,%s,%s,%s)",
                      (request.form['name'], request.form['email'], generate_password_hash(request.form['password']),
                       'candidate', request.form.get('location',''), request.form.get('skills',''),
                       request.form.get('experience',''), request.form.get('phone',''), request.form.get('education',''), request.form.get('about','')))
            db.commit()
            flash('Registration successful! Please login', 'success')
            return redirect(url_for('candidate_login'))
        except psycopg2.IntegrityError:
            db.rollback()
            flash('Email already exists', 'error')
        finally:
            c.close()
    return render_template('candidate_register.html')

@app.route('/company/register', methods=['GET', 'POST'])
def company_register():
    if request.method == 'POST':
        db = get_db()
        c = db.cursor()
        try:
            c.execute("INSERT INTO users (name, email, password, role, location, phone, about) VALUES (%s,%s,%s)",
                      (request.form['name'], request.form['email'], generate_password_hash(request.form['password']),
                       'company', request.form.get('location',''), request.form.get('phone',''), request.form.get('about','')))
            db.commit()
            flash('Registration successful! Please login', 'success')
            return redirect(url_for('company_login'))
        except psycopg2.IntegrityError:
            db.rollback()
            flash('Email already exists', 'error')
        finally:
            c.close()
    return render_template('company_register.html')

@app.route('/candidate/login', methods=['GET', 'POST'])
def candidate_login():
    if request.method == 'POST':
        db = get_db()
        c = db.cursor()
        c.execute("SELECT * FROM users WHERE email = %s AND role='candidate'", (request.form['email'],))
        user = c.fetchone()
        c.close()
        if user and check_password_hash(user['password'], request.form['password']):
            session['user_id'], session['name'], session['role'] = user['id'], user['name'], user['role']
            return redirect(url_for('column.candidate_dashboard'))
        flash('Invalid credentials', 'error')
    return render_template('candidate_login.html')

@app.route('/company/login', methods=['GET', 'POST'])
def company_login():
    if request.method == 'POST':
        db = get_db()
        c = db.cursor()
        c.execute("SELECT * FROM users WHERE email = %s AND role='company'", (request.form['email'],))
        user = c.fetchone()
        c.close()
        if user and check_password_hash(user['password'], request.form['password']):
            session['user_id'], session['name'], session['role'] = user['id'], user['name'], user['role']
            return redirect(url_for('column.company_dashboard'))
        flash('Invalid credentials', 'error')
    return render_template('company_login.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        db = get_db()
        c = db.cursor()
        c.execute("SELECT * FROM users WHERE email = %s AND role='admin'", (request.form['email'],))
        user = c.fetchone()
        c.close()
        if user and check_password_hash(user['password'], request.form['password']):
            session['user_id'], session['name'], session['role'] = user['id'], user['name'], user['role']
            return redirect(url_for('column.admin_dashboard'))
        flash('Invalid credentials', 'error')
    return render_template('admin_login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

@app.route('/admin-rahul-123')
def admin_panel():
    db = get_db()
    c = db.cursor()
    c.execute("SELECT * FROM users WHERE role='company'")
    companies = c.fetchall()
    c.execute("SELECT * FROM users WHERE role='candidate'")
    students = c.fetchall()
    c.execute("SELECT * FROM jobs")
    jobs = c.fetchall()
    c.close()
    
    html = '<h1>Admin Panel</h1>'
    html += f'<h2>Companies: {len(companies)}</h2>'
    for c in companies:
        html += f'ID: {c["id"]} | {c["name"]} | {c["email"]} | Hash: {c["password"][:20]}...<br>'
    
    html += f'<h2>Students: {len(students)}</h2>{len(students)} registered<br>'
    html += f'<h2>Jobs: {len(jobs)}</h2>{len(jobs)} posted<br>'
    html += '<br><b>Note:</b> Password hash me hai, seedha nahi dikhega. Reset karna padega.'
    return html

if __name__ == '__main__':
    app.run(debug=True)
