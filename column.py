from flask import Blueprint, render_template, request, redirect, url_for, session, flash, g
import sqlite3
from functools import wraps

column_bp = Blueprint('column', __name__)
DATABASE = 'surejob.db'

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first', 'error')
            return redirect(url_for('candidate_login'))
        return f(*args, **kwargs)
    return decorated_function

def company_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role')!= 'company':
            flash('Access denied', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role')!= 'admin':
            flash('Admin access only', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@column_bp.route('/candidate/dashboard')
@login_required
def candidate_dashboard():
    if session['role']!= 'candidate': return redirect(url_for('index'))
    db = get_db()
    apps = db.execute('''SELECT a.*, j.title, j.location, u.name as company_name
                         FROM applications a JOIN jobs j ON a.job_id = j.id
                         JOIN users u ON j.company_id = u.id
                         WHERE a.candidate_id =? ORDER BY a.applied_at DESC''', (session['user_id'],)).fetchall()
    saved = db.execute('''SELECT s.*, j.title, j.location, u.name as company_name FROM saved_jobs s
                          JOIN jobs j ON s.job_id = j.id JOIN users u ON j.company_id = u.id
                          WHERE s.candidate_id =?''', (session['user_id'],)).fetchall()
    return render_template('candidate_dashboard.html', applications=apps, saved_jobs=saved)

@column_bp.route('/company/dashboard')
@login_required
@company_required
def company_dashboard():
    db = get_db()
    jobs = db.execute("SELECT * FROM jobs WHERE company_id =? ORDER BY created_at DESC", (session['user_id'],)).fetchall()
    total_apps = db.execute("SELECT COUNT(*) FROM applications a JOIN jobs j ON a.job_id = j.id WHERE j.company_id =?", (session['user_id'],)).fetchone()[0]
    return render_template('company_dashboard.html', jobs=jobs, total_applications=total_apps)

@column_bp.route('/company/applications/<int:job_id>')
@login_required
@company_required
def job_applications(job_id):
    db = get_db()
    job = db.execute("SELECT * FROM jobs WHERE id =? AND company_id =?", (job_id, session['user_id'])).fetchone()
    if not job:
        flash('Job not found', 'error')
        return redirect(url_for('column.company_dashboard'))
    apps = db.execute('''SELECT a.*, u.name, u.email, u.skills, u.experience, u.location, u.phone, u.education FROM applications a
                         JOIN users u ON a.candidate_id = u.id WHERE a.job_id =? ORDER BY a.applied_at DESC''', (job_id,)).fetchall()
    return render_template('job_applications.html', job=job, applications=apps)

@column_bp.route('/company/update-application/<int:app_id>', methods=['POST'])
@login_required
@company_required
def update_application_status(app_id):
    status = request.form['status']
    interview_date = request.form.get('interview_date', '')
    db = get_db()
    db.execute("UPDATE applications SET status =?, interview_date =? WHERE id =?", (status, interview_date, app_id))
    db.commit()
    flash('Application updated', 'success')
    return redirect(request.referrer)

@column_bp.route('/company/search-candidates')
@login_required
@company_required
def search_candidates():
    keyword = request.args.get('keyword', '')
    location = request.args.get('location', '')
    experience = request.args.get('experience', '')
    skills = request.args.get('skills', '')
    education = request.args.get('education', '')

    query = "SELECT * FROM users WHERE role = 'candidate'"
    params = []

    if keyword:
        query += " AND (name LIKE? OR skills LIKE? OR experience LIKE? OR about LIKE?)"
        params.extend([f'%{keyword}%']*4)
    if location: query += " AND location LIKE?"; params.append(f'%{location}%')
    if experience: query += " AND experience LIKE?"; params.append(f'%{experience}%')
    if education: query += " AND education LIKE?"; params.append(f'%{education}%')
    if skills:
        for skill in [s.strip() for s in skills.split(',')]:
            query += " AND skills LIKE?"; params.append(f'%{skill}%')

    query += " ORDER BY created_at DESC"
    db = get_db()
    candidates = db.execute(query, params).fetchall()
    return render_template('search_candidates.html', candidates=candidates)

@column_bp.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    db = get_db()
    stats = {
        'total_users': db.execute("SELECT COUNT(*) FROM users WHERE role!= 'admin'").fetchone()[0],
        'total_companies': db.execute("SELECT COUNT(*) FROM users WHERE role = 'company'").fetchone()[0],
        'total_candidates': db.execute("SELECT COUNT(*) FROM users WHERE role = 'candidate'").fetchone()[0],
        'total_jobs': db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0],
        'total_applications': db.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
    }
    jobs = db.execute("SELECT j.*, u.name as company_name FROM jobs j JOIN users u ON j.company_id = u.id ORDER BY j.created_at DESC").fetchall()
    users = db.execute("SELECT * FROM users WHERE role!= 'admin' ORDER BY created_at DESC LIMIT 20").fetchall()
    return render_template('admin.html', stats=stats, jobs=jobs, users=users)

@column_bp.route('/admin/delete-job/<int:job_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_job(job_id):
    db = get_db()
    db.execute("DELETE FROM jobs WHERE id =?", (job_id,))
    db.commit()
    flash('Job deleted by admin', 'success')
    return redirect(url_for('column.admin_dashboard'))

@column_bp.route('/admin/delete-user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_user(user_id):
    db = get_db()
    db.execute("DELETE FROM users WHERE id =?", (user_id,))
    db.commit()
    flash('User deleted by admin', 'success')
    return redirect(url_for('column.admin_dashboard'))

@column_bp.route('/candidate/create-resume', methods=['GET', 'POST'])
@login_required
def create_resume():
    if session['role']!= 'candidate': return redirect(url_for('index'))
    db = get_db()
    if request.method == 'POST':
        db.execute('''UPDATE users SET skills=?, experience=?, education=?, about=?, location=?, phone=?
                      WHERE id=?''',
                  (request.form['skills'], request.form['experience'], request.form['education'],
                   request.form['about'], request.form['location'], request.form['phone'], session['user_id']))
        db.commit()
        flash('Resume updated successfully!', 'success')
        return redirect(url_for('column.candidate_dashboard'))
    user = db.execute("SELECT * FROM users WHERE id=?", (session['user_id'],)).fetchone()
    return render_template('create_resume.html', user=user)

@column_bp.route('/company/profile', methods=['GET', 'POST'])
@login_required
@company_required
def company_profile():
    db = get_db()
    if request.method == 'POST':
        db.execute('''UPDATE users SET name=?, location=?, phone=?, about=?
                      WHERE id=?''',
                  (request.form['name'], request.form['location'], request.form['phone'],
                   request.form['about'], session['user_id']))
        db.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('column.company_dashboard'))
    user = db.execute("SELECT * FROM users WHERE id=?", (session['user_id'],)).fetchone()
    return render_template('company_profile.html', user=user)
