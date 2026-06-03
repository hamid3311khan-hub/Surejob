from flask import Flask, render_template, request, redirect, url_for, session, flash, g
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from job_routes import job_bp
from column import column_bp
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'surejob-v3-final')
DATABASE = 'surejob.db'

# Register Blueprints
app.register_blueprint(job_bp)
app.register_blueprint(column_bp)

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
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
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password TEXT NOT NULL, role TEXT NOT NULL,
            location TEXT, skills TEXT, experience TEXT, phone TEXT, education TEXT, about TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER NOT NULL, title TEXT NOT NULL,
            description TEXT NOT NULL, location TEXT NOT NULL, salary TEXT NOT NULL, job_type TEXT NOT NULL,
            skills_required TEXT, experience_required TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES users (id)
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT, job_id INTEGER NOT NULL, candidate_id INTEGER NOT NULL,
            status TEXT DEFAULT 'Applied', interview_date TEXT, applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobs (id), FOREIGN KEY (candidate_id) REFERENCES users (id),
            UNIQUE(job_id, candidate_id)
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS saved_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, candidate_id INTEGER NOT NULL, job_id INTEGER NOT NULL,
            saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (candidate_id) REFERENCES users (id),
            FOREIGN KEY (job_id) REFERENCES jobs (id), UNIQUE(candidate_id, job_id)
        )''')
        try:
            db.execute("INSERT INTO users (name, email, password, role) VALUES (?,?,?,?)",
                      ('Admin', 'admin@surejob.com', generate_password_hash('admin123'), 'admin'))
            db.commit()
        except: pass

@app.route('/')
def index():
    db = get_db()
    jobs = db.execute("SELECT j.*, u.name as company_name FROM jobs j JOIN users u ON j.company_id = u.id ORDER BY j.created_at DESC LIMIT 8").fetchall()
    return render_template('index.html', jobs=jobs)

@app.route('/candidate/register', methods=['GET', 'POST'])
def candidate_register():
    if request.method == 'POST':
        db = get_db()
        try:
            db.execute("INSERT INTO users (name, email, password, role, location, skills, experience, phone, education, about) VALUES (?,?,?,?,?,?,?,?,?,?)",
                      (request.form['name'], request.form['email'], generate_password_hash(request.form['password']),
                       'candidate', request.form.get('location',''), request.form.get('skills',''),
                       request.form.get('experience',''), request.form.get('phone',''), request.form.get('education',''), request.form.get('about','')))
            db.commit()
            flash('Registration successful! Please login', 'success')
            return redirect(url_for('candidate_login'))
        except sqlite3.IntegrityError:
            flash('Email already exists', 'error')
    return render_template('candidate_register.html')

@app.route('/company/register', methods=['GET', 'POST'])
def company_register():
    if request.method == 'POST':
        db = get_db()
        try:
            db.execute("INSERT INTO users (name, email, password, role, location, phone, about) VALUES (?,?,?,?,?,?,?)",
                      (request.form['name'], request.form['email'], generate_password_hash(request.form['password']),
                       'company', request.form.get('location',''), request.form.get('phone',''), request.form.get('about','')))
            db.commit()
            flash('Registration successful! Please login', 'success')
            return redirect(url_for('company_login'))
        except sqlite3.IntegrityError:
            flash('Email already exists', 'error')
    return render_template('company_register.html')

@app.route('/candidate/login', methods=['GET', 'POST'])
def candidate_login():
    if request.method == 'POST':
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email =? AND role='candidate'", (request.form['email'],)).fetchone()
        if user and check_password_hash(user['password'], request.form['password']):
            session['user_id'], session['name'], session['role'] = user['id'], user['name'], user['role']
            return redirect(url_for('column.candidate_dashboard'))
        flash('Invalid credentials', 'error')
    return render_template('candidate_login.html')

@app.route('/company/login', methods=['GET', 'POST'])
def company_login():
    if request.method == 'POST':
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email =? AND role='company'", (request.form['email'],)).fetchone()
        if user and check_password_hash(user['password'], request.form['password']):
            session['user_id'], session['name'], session['role'] = user['id'], user['name'], user['role']
            return redirect(url_for('column.company_dashboard'))
        flash('Invalid credentials', 'error')
    return render_template('company_login.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email =? AND role='admin'", (request.form['email'],)).fetchone()
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

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
