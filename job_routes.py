from flask import Blueprint, render_template, request, redirect, url_for, session, flash, g
import sqlite3
from functools import wraps

job_bp = Blueprint('job', __name__)
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

@job_bp.route('/jobs')
def jobs():
    keyword = request.args.get('keyword', '')
    location = request.args.get('location', '')
    job_type = request.args.get('job_type', '')
    experience = request.args.get('experience', '')
    salary = request.args.get('salary', '')

    query = "SELECT j.*, u.name as company_name FROM jobs j JOIN users u ON j.company_id = u.id WHERE 1=1"
    params = []

    if keyword:
        query += " AND (j.title LIKE? OR j.description LIKE? OR j.skills_required LIKE?)"
        params.extend([f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'])
    if location: query += " AND j.location LIKE?"; params.append(f'%{location}%')
    if job_type: query += " AND j.job_type =?"; params.append(job_type)
    if experience: query += " AND j.experience_required LIKE?"; params.append(f'%{experience}%')
    if salary: query += " AND j.salary LIKE?"; params.append(f'%{salary}%')

    query += " ORDER BY j.created_at DESC"
    db = get_db()
    all_jobs = db.execute(query, params).fetchall()

    saved_job_ids = []
    if 'user_id' in session and session['role'] == 'candidate':
        saved = db.execute("SELECT job_id FROM saved_jobs WHERE candidate_id =?", (session['user_id'],)).fetchall()
        saved_job_ids = [s['job_id'] for s in saved]

    return render_template('jobs.html', jobs=all_jobs, saved_job_ids=saved_job_ids)

@job_bp.route('/job/<int:job_id>')
def job_detail(job_id):
    db = get_db()
    job = db.execute("SELECT j.*, u.name as company_name, u.email as company_email FROM jobs j JOIN users u ON j.company_id = u.id WHERE j.id =?", (job_id,)).fetchone()
    if not job:
        flash('Job not found', 'error')
        return redirect(url_for('job.jobs'))

    applied, saved = False, False
    if 'user_id' in session and session['role'] == 'candidate':
        applied = db.execute("SELECT id FROM applications WHERE job_id =? AND candidate_id =?", (job_id, session['user_id'])).fetchone() is not None
        saved = db.execute("SELECT id FROM saved_jobs WHERE job_id =? AND candidate_id =?", (job_id, session['user_id'])).fetchone() is not None

    return render_template('job_detail.html', job=job, applied=applied, saved=saved)

@job_bp.route('/apply/<int:job_id>', methods=['POST'])
@login_required
def apply_job(job_id):
    if session['role']!= 'candidate':
        flash('Only candidates can apply', 'error')
        return redirect(url_for('job.job_detail', job_id=job_id))
    db = get_db()
    try:
        db.execute("INSERT INTO applications (job_id, candidate_id) VALUES (?,?)", (job_id, session['user_id']))
        db.commit()
        flash('Applied successfully!', 'success')
    except sqlite3.IntegrityError:
        flash('Already applied to this job', 'error')
    return redirect(url_for('job.job_detail', job_id=job_id))

@job_bp.route('/save-job/<int:job_id>', methods=['POST'])
@login_required
def save_job(job_id):
    if session['role']!= 'candidate': return redirect(url_for('index'))
    db = get_db()
    try:
        db.execute("INSERT INTO saved_jobs (candidate_id, job_id) VALUES (?,?)", (session['user_id'], job_id))
        db.commit()
        flash('Job saved!', 'success')
    except sqlite3.IntegrityError:
        db.execute("DELETE FROM saved_jobs WHERE candidate_id =? AND job_id =?", (session['user_id'], job_id))
        db.commit()
        flash('Job unsaved', 'info')
    return redirect(request.referrer or url_for('job.jobs'))

@job_bp.route('/company/post-job', methods=['GET', 'POST'])
@login_required
@company_required
def post_job():
    if request.method == 'POST':
        db = get_db()
        db.execute("INSERT INTO jobs (company_id, title, description, location, salary, job_type, skills_required, experience_required) VALUES (?,?,?,?,?,?,?,?)",
                  (session['user_id'], request.form['title'], request.form['description'], request.form['location'],
                   request.form['salary'], request.form['job_type'], request.form.get('skills_required', ''), request.form.get('experience_required', '')))
        db.commit()
        flash('Job posted successfully!', 'success')
        return redirect(url_for('column.company_dashboard'))
    return render_template('post_job.html')

@job_bp.route('/company/edit-job/<int:job_id>', methods=['GET', 'POST'])
@login_required
@company_required
def edit_job(job_id):
    db = get_db()
    job = db.execute("SELECT * FROM jobs WHERE id =? AND company_id =?", (job_id, session['user_id'])).fetchone()
    if not job:
        flash('Job not found', 'error')
        return redirect(url_for('column.company_dashboard'))
    if request.method == 'POST':
        db.execute('''UPDATE jobs SET title=?, description=?, location=?, salary=?, job_type=?, skills_required=?, experience_required=?
                      WHERE id=? AND company_id=?''',
                  (request.form['title'], request.form['description'], request.form['location'], request.form['salary'],
                   request.form['job_type'], request.form.get('skills_required', ''), request.form.get('experience_required', ''), job_id, session['user_id']))
        db.commit()
        flash('Job updated successfully!', 'success')
        return redirect(url_for('column.company_dashboard'))
    return render_template('edit_job.html', job=job)

@job_bp.route('/company/delete-job/<int:job_id>', methods=['POST'])
@login_required
@company_required
def delete_job(job_id):
    db = get_db()
    db.execute("DELETE FROM jobs WHERE id =? AND company_id =?", (job_id, session['user_id']))
    db.commit()
    flash('Job deleted successfully!', 'success')
    return redirect(url_for('column.company_dashboard'))

@job_bp.route('/company/manage-jobs')
@login_required
@company_required
def manage_jobs():
    db = get_db()
    jobs = db.execute("SELECT * FROM jobs WHERE company_id =? ORDER BY created_at DESC", (session['user_id'],)).fetchall()
    return render_template('manage_jobs.html', jobs=jobs)
