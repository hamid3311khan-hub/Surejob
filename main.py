from flask import Flask, request, render_template, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'surejob_secret_key_123'

def init_db():
    conn = sqlite3.connect('database.db')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            mobile TEXT,
            full_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            company_name TEXT,
            mobile TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            location TEXT,
            salary TEXT,
            job_type TEXT,
            experience TEXT,
            company_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies (id)
        )
    ''')
    conn.commit()
    conn.close()
    print("Database initialized ✅")

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    try:
        conn = get_db_connection()
        jobs = conn.execute('''
            SELECT jobs.*, companies.company_name 
            FROM jobs 
            JOIN companies ON jobs.company_id = companies.id 
            ORDER BY jobs.id DESC LIMIT 6
        ''').fetchall()
        conn.close()
        return render_template('index.html', jobs=jobs)
    except Exception as e:
        print(f"Error in home route: {e}")
        return render_template('index.html', jobs=[])

@app.route('/jobs')
def jobs():
    conn = get_db_connection()
    all_jobs = conn.execute('''
        SELECT jobs.*, companies.company_name 
        FROM jobs 
        JOIN companies ON jobs.company_id = companies.id 
        ORDER BY jobs.id DESC
    ''').fetchall()
    conn.close()
    return render_template('jobs.html', jobs=all_jobs)

@app.route('/job/<int:job_id>')
def job_detail(job_id):
    conn = get_db_connection()
    job = conn.execute('''
        SELECT jobs.*, companies.company_name 
        FROM jobs 
        JOIN companies ON jobs.company_id = companies.id 
        WHERE jobs.id = ?
    ''', (job_id,)).fetchone()
    conn.close()
    return render_template('job_detail.html', job=job)

@app.route('/candidate/register', methods=['GET', 'POST'])
def candidate_register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        mobile = request.form.get('mobile')
        full_name = request.form.get('full_name')
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO candidates (email, password, mobile, full_name) VALUES (?, ?, ?, ?)',
                         (email, password, mobile, full_name))
            conn.commit()
            return redirect(url_for('candidate_login'))
        except sqlite3.IntegrityError:
            return "Email already exists!"
        finally:
            conn.close()
    return render_template('candidate_register.html')

@app.route('/candidate/login', methods=['GET', 'POST'])
def candidate_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM candidates WHERE email = ? AND password = ?', 
                           (email, password)).fetchone()
        conn.close()
        if user:
            session['user_id'] = user['id']
            session['user_type'] = 'candidate'
            session['name'] = user['full_name']
            return redirect(url_for('candidate_dashboard'))
        else:
            return "Invalid email or password!"
    return render_template('candidate_login.html')

@app.route('/candidate/dashboard')
def candidate_dashboard():
    if 'user_id' not in session or session['user_type'] != 'candidate':
        return redirect(url_for('candidate_login'))
    return render_template('candidate_dashboard.html', name=session['name'])

@app.route('/company/register', methods=['GET', 'POST'])
def company_register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        company_name = request.form.get('company_name')
        mobile = request.form.get('mobile')
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO companies (email, password, company_name, mobile) VALUES (?, ?, ?, ?)',
                         (email, password, company_name, mobile))
            conn.commit()
            return redirect(url_for('company_login'))
        except sqlite3.IntegrityError:
            return "Email already exists!"
        finally:
            conn.close()
    return render_template('company_register.html')

@app.route('/company/login', methods=['GET', 'POST'])
def company_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        conn = get_db_connection()
        company = conn.execute('SELECT * FROM companies WHERE email = ? AND password = ?', 
                              (email, password)).fetchone()
        conn.close()
        if company:
            session['user_id'] = company['id']
            session['user_type'] = 'company'
            session['name'] = company['company_name']
            return redirect(url_for('company_dashboard'))
        else:
            return "Invalid email or password!"
    return render_template('company_login.html')

@app.route('/company/dashboard')
def company_dashboard():
    if 'user_id' not in session or session['user_type'] != 'company':
        return redirect(url_for('company_login'))
    return render_template('company_dashboard.html', name=session['name'])

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

init_db()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
