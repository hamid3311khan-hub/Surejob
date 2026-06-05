from flask import Blueprint, render_template, request, redirect, url_for, session, flash, g
import psycopg2
from psycopg2.extras import RealDictCursor
from functools import wraps
import os

column_bp = Blueprint('column', __name__)

def get_db():
    if 'db' not in g:
        g.db = psycopg2.connect(os.environ.get('DATABASE_URL'), cursor_factory=RealDictCursor)
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
    c = db.cursor()
    c.execute('''SELECT a.*, j.title, j.location, u.name as company_name
                 FROM applications a JOIN jobs j ON a.job_id = j.id
                 JOIN users u ON j.company_id = u.id
                 WHERE a.candidate_id = %s ORDER BY a.applied_at DESC''', (session['user_id'],))
    apps = c.fetchall()
    c.execute('''SELECT s.*, j.title, j.location, u.name as company_name FROM saved_jobs s
                 JOIN jobs j ON s.job_id = j.id JOIN users u ON j.company_id = u.id
                 WHERE s.candidate_id = %s''', (session['user_id'],))
    saved = c.fetchall()
    c.close()
    return render_template('candidate_dashboard.html', applications=apps, saved_jobs=saved)

@column_bp.route('/company/dashboard')
@login_required
@company_required
def company_dashboard():
    db = get_db()
    c = db.cursor()
    c.execute("SELECT * FROM jobs WHERE company_id = %s ORDER BY created_at DESC", (session['user_id'],))
    jobs = c.fetchall()
    c.execute("SELECT COUNT(*) FROM applications a JOIN jobs j ON a.job_id = j.id WHERE j.company_id = %s", (session['user_id'],))
    total_apps = c.fetchone()['count']
    c.close()
    return render_template('company_dashboard.html', jobs=jobs, total_applications=total_apps)

@column_bp.route('/company/applications/<int:job_id>')
@login_required
@company_required
def job_applications(job_id):
    db = get_db()
    c = db.cursor()
    c.execute("SELECT * FROM jobs WHERE id = %s AND company_id = %s", (job_id, session['user_id']))
    job = c.fetchone()
    if not job:
        c.close()
        flash('Job not found', 'error')
        return redirect(url_for('column.company_dashboard'))
    c.execute('''SELECT a.*, u.name, u.email, u.skills, u.experience, u.location, u.phone, u.education FROM applications a
                 JOIN users u ON a.candidate_id = u.id WHERE a.job_id = %s ORDER BY a.applied_at DESC''', (job_id,))
    apps = c.fetchall()
    c.close()
    return render_template('job_applications.html', job=job, applications=apps)

@column_bp.route('/company/update-application/<int:app_id>', methods=['POST'])
@login_required
@company_required
def update_application_status(app_id):
    status = request.form['status']
    interview_date = request.form.get('interview_date', '')
    db = get_db()
    c = db.cursor()
    c.execute("UPDATE applications SET status = %s, interview_date = %s WHERE id = %s", (status, interview_date, app_id))
    db.commit()
    c.close()
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
        query += " AND (name ILIKE %s OR skills ILIKE %s OR experience ILIKE %s OR about ILIKE %s)"
        params.extend([f'%{keyword}%']*4)
    if location: query += " AND location ILIKE %s"; params.append(f'%{location}%')
    if experience: query += " AND experience ILIKE %s"; params.append(f'%{experience}%')
    if education: query += " AND education ILIKE %s"; params.append(f'%{education}%')
    if skills:
        for skill in [s.strip() for s in skills.split(',')]:
            query += " AND skills ILIKE %s"; params.append(f'%{skill}%')

    query += " ORDER BY created_at DESC"
    db = get_db()
    c = db.cursor()
    c.execute(query, params)
    candidates = c.fetchall()
    c.close()
    return render_template('search_candidates.html', candidates=candidates)

@column_bp.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    db = get_db()
    c = db.cursor()
    c.execute("SELECT COUNT(*) FROM users WHERE role != 'admin'")
    total_users = c.fetchone()['count']
    c.execute("SELECT COUNT(*) FROM users WHERE role = 'company'")
    total_companies = c.fetchone()['count']
    c.execute("SELECT COUNT(*) FROM users WHERE role = 'candidate'")
    total_candidates = c.fetchone()['count']
    c.execute("SELECT COUNT(*) FROM jobs")
    total_jobs = c.fetchone()['count']
    c.execute("SELECT COUNT(*) FROM applications")
    total_applications = c.fetchone()['count']
    
    stats = {
        'total_users': total_users,
        'total_companies': total_companies,
        'total_candidates': total_candidates,
        'total_jobs': total_jobs,
        'total_applications': total_applications
    }
    
    c.execute("SELECT j.*, u.name as company_name FROM jobs j JOIN users u ON j.company_id = u.id ORDER BY j.created_at DESC")
    jobs = c.fetchall()
    c.execute("SELECT * FROM users WHERE role != 'admin' ORDER BY created_at DESC LIMIT 20")
    users = c.fetchall()
    c.close()
    return render_template('admin.html', stats=stats, jobs=jobs, users=users)

@column_bp.route('/admin/delete-job/<int:job_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_job(job_id):
    db = get_db()
    c = db.cursor()
    c.execute("DELETE FROM jobs WHERE id = %s", (job_id,))
    db.commit()
    c.close()
    flash('Job deleted by admin', 'success')
    return redirect(url_for('column.admin_dashboard'))

@column_bp.route('/admin/delete-user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_user(user_id):
    db = get_db()
    c = db.cursor()
    c.execute("DELETE FROM users WHERE id = %s", (user_id,))
    db.commit()
    c.close()
    flash('User deleted by admin', 'success')
    return redirect(url_for('column.admin_dashboard'))

@column_bp.route('/candidate/create-resume', methods=['GET', 'POST'])
@login_required
def create_resume():
    if session['role']!= 'candidate': return redirect(url_for('index'))
    db = get_db()
    c = db.cursor()
    if request.method == 'POST':
        c.execute('''UPDATE users SET skills=%s, experience=%s, education=%s, about=%s, location=%s, phone=%s
                     WHERE id=%s''',
                  (request.form['skills'], request.form['experience'], request.form['education'],
                   request.form['about'], request.form['location'], request.form['phone'], session['user_id']))
        db.commit()
        c.close()
        flash('Resume updated successfully!', 'success')
        return redirect(url_for('column.candidate_dashboard'))
    c.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
    user = c.fetchone()
    c.close()
    return render_template('create_resume.html', user=user)

@column_bp.route('/company/profile', methods=['GET', 'POST'])
@login_required
@company_required
def company_profile():
    db = get_db()
    c = db.cursor()
    if request.method == 'POST':
        c.execute('''UPDATE users SET name=%s, location=%s, phone=%s, about=%s
                     WHERE id=%s''',
                  (request.form['name'], request.form['location'], request.form['phone'],
                   request.form['about'], session['user_id']))
        db.commit()
        c.close()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('column.company_dashboard'))
    c.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
    user = c.fetchone()
    c.close()
    return render_template('company_profile.html', user=user)
