from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import sqlite3

job_bp = Blueprint('job_bp', __name__)

@job_bp.route('/edit_job/<int:job_id>', methods=['GET', 'POST'])
def edit_job(job_id):
    if 'user_id' not in session or session['role'] != 'company':
        flash('Please login as company', 'error')
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row  # Teri HTML me job['title'] hai isliye
    c = conn.cursor()

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        location = request.form['location']
        salary = request.form['salary']
        job_type = request.form['job_type']
        experience = request.form['experience']
        requirements = request.form['requirements']

        c.execute('''UPDATE jobs SET title=?, description=?, location=?, salary=?, 
                     job_type=?, experience=?, requirements=?
                     WHERE id=? AND company_id=?''',
                  (title, description, location, salary, job_type, experience, 
                   requirements, job_id, session['user_id']))
        conn.commit()
        conn.close()
        flash('Job updated successfully!', 'success')
        return redirect(url_for('company_dashboard'))

    c.execute("SELECT * FROM jobs WHERE id=? AND company_id=?", (job_id, session['user_id']))
    job = c.fetchone()
    conn.close()

    if not job:
        flash('Job not found or you are not authorized', 'error')
        return redirect(url_for('company_dashboard'))

    return render_template('edit_job.html', job=job)

@job_bp.route('/delete_job/<int:job_id>')
def delete_job(job_id):
    if 'user_id' not in session or session['role'] != 'company':
        flash('Please login as company', 'error')
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Pehle check karo job usi company ki hai ya nahi
    c.execute("SELECT id FROM jobs WHERE id=? AND company_id=?", (job_id, session['user_id']))
    job = c.fetchone()
    
    if not job:
        flash('Job not found or you are not authorized', 'error')
        conn.close()
        return redirect(url_for('company_dashboard'))
    
    # Job delete karo
    c.execute("DELETE FROM jobs WHERE id=?", (job_id,))
    # Uski applications bhi delete karo
    c.execute("DELETE FROM applications WHERE job_id=?", (job_id,))
    conn.commit()
    conn.close()

    flash('Job deleted successfully!', 'success')
    return redirect(url_for('company_dashboard'))
