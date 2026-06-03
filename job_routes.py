from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import sqlite3

job_bp = Blueprint('job_bp', __name__)

@job_bp.route('/edit_job/<int:job_id>', methods=['GET', 'POST'])
def edit_job(job_id):
    if 'user_id' not in session or session['role']!= 'company':
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        location = request.form['location']
        salary = request.form['salary']
        job_type = request.form['job_type']

        c.execute('''UPDATE jobs SET title=?, description=?, location=?, salary=?, job_type=?
                     WHERE id=? AND company_id=?''',
                  (title, description, location, salary, job_type, job_id, session['user_id']))
        conn.commit()
        conn.close()
        flash('Job updated successfully!', 'success')
        return redirect(url_for('company_dashboard'))

    c.execute("SELECT * FROM jobs WHERE id=? AND company_id=?", (job_id, session['user_id']))
    job = c.fetchone()
    conn.close()

    if not job:
        flash('Job not found', 'error')
        return redirect(url_for('company_dashboard'))

    return render_template('edit_job.html', job=job)

@job_bp.route('/delete_job/<int:job_id>')
def delete_job(job_id):
    if 'user_id' not in session or session['role']!= 'company':
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("DELETE FROM jobs WHERE id=? AND company_id=?", (job_id, session['user_id']))
    c.execute("DELETE FROM applications WHERE job_id=?", (job_id,))
    conn.commit()
    conn.close()

    flash('Job deleted successfully!', 'success')
    return redirect(url_for('company_dashboard'))
