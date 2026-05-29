        @app.route('/job/<int:job_id>', methods=['GET', 'POST'])
def job_detail(job_id):
    conn = get_db()
    conn.execute('UPDATE jobs SET views = views + 1 WHERE id=?', (job_id,))
    conn.commit()

    job = conn.execute('''
        SELECT j.*, c.company_name, c.logo, c.email as company_email
        FROM jobs j LEFT JOIN companies c ON j.company_id = c.id
        WHERE j.id=?
    ''', (job_id,)).fetchone()

    if not job:
        conn.close()
        return "Job Not Found", 404

    similar_jobs = conn.execute('''
        SELECT j.id, j.title, j.location, c.company_name
        FROM jobs j LEFT JOIN companies c ON j.company_id = c.id
        WHERE j.category=? AND j.id!=? AND j.status='Active'
        LIMIT 4
    ''', (job['category'], job_id)).fetchall()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()

        if not all([name, email, phone]):
            flash('Name, Email aur Phone required hai!', 'error')
            conn.close()
            return redirect(f'/job/{job_id}')

        resume = request.files.get('resume')
        resume_path = ''
        if resume and resume.filename and allowed_file(resume.filename):
            filename = secure_filename(f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{resume.filename}")
            resume_path = os.path.join(RESUME_FOLDER, filename)
            resume.save(resume_path)

        conn.execute('INSERT INTO applications (job_id, name, email, phone, resume, cover_letter, applied_on) VALUES (?,?,?,?,?,?,?)',
            (job_id, name, email, phone, resume_path, request.form.get('cover_letter',''), datetime.now().strftime('%Y-%m-%d %H:%M')))
        conn.commit()
        flash('Application submitted successfully!', 'success')
        conn.close()
        return redirect(f'/job/{job_id}')

    conn.close()
    return render_template('job_detail.html', job=job, similar_jobs=similar_jobs)

@app.route('/save-job/<int:job_id>', methods=['POST'])
def save_job(job_id):
    email = request.json.get('email', '').strip()
    if not email:
        return jsonify({'success': False, 'msg': 'Email required'})

    conn = get_db()
    try:
        conn.execute('INSERT INTO saved_jobs (email, job_id, saved_on) VALUES (?,?,?)',
            (email, job_id, datetime.now().strftime('%Y-%m-%d')))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'msg': 'Job saved!'})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'success': False, 'msg': 'Already saved'})

@app.route('/company-register', methods=['GET', 'POST'])
def company_register():
    if request.method == 'POST':
        company_name = request.form.get('company_name', '').strip()
        gst_no = request.form.get('gst_no', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '').strip()

        if not all([company_name, email, phone, password]):
            flash('Company Name, Email, Phone aur Password required hai!', 'error')
            return render_template('company_register.html')

        hashed_password = generate_password_hash(password)

        logo = request.files.get('logo')
        logo_path = ''
        if logo and logo.filename and allowed_file(logo.filename):
            filename = secure_filename(f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{logo.filename}")
            logo_path = os.path.join(UPLOAD_FOLDER, filename)
            logo.save(logo_path)

        conn = get_db()
        try:
            conn.execute('INSERT INTO companies (company_name, gst_no, email, phone, password, logo, registered_on, plan_expiry) VALUES (?,?,?,?,?,?,?,?)',
                (company_name, gst_no, email, phone, hashed_password, logo_path,
                 datetime.now().strftime('%Y-%m-%d'),
                 (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')))
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            conn.close()
            return redirect('/company-login')
        except sqlite3.IntegrityError:
            conn.close()
            flash('Ye Email already registered hai!', 'error')
        except Exception as e:
            conn.close()
            flash(f'Error: {str(e)}', 'error')
    return render_template('company_register.html')

@app.route('/company-login', methods=['GET', 'POST'])
def company_login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        if not email or not password:
            flash('Email aur Password dono dalo!', 'error')
            return render_template('company_login.html')

        conn = get_db()
        company = conn.execute('SELECT * FROM companies WHERE email=?', (email,)).fetchone()
        conn.close()

        if company and check_password_hash(company['password'], password):
            session['company_id'] = company['id']
            session['company_name'] = company['company_name']
            return redirect('/company-dashboard')
        flash('Invalid credentials!', 'error')
    return render_template('company_login.html')

@app.route('/company-dashboard')
def company_dashboard():
    if 'company_id' not in session:
        return redirect('/company-login')
    conn = get_db()
    company = conn.execute('SELECT * FROM companies WHERE id=?', (session['company_id'],)).fetchone()

    stats = {
        'total_jobs': conn.execute('SELECT COUNT(*) as c FROM jobs WHERE company_id=? AND status="Active"', (session['company_id'],)).fetchone()['c'],
        'total_apps': conn.execute('SELECT COUNT(*) as c FROM applications a JOIN jobs j ON a.job_id=j.id WHERE j.company_id=?', (session['company_id'],)).fetchone()['c'],
        'total_views': conn.execute('SELECT SUM(views) as c FROM jobs WHERE company_id=?', (session['company_id'],)).fetchone()['c'] or 0
    }

    jobs = conn.execute('''
        SELECT j.*, COUNT(a.id) as app_count
        FROM jobs j
        LEFT JOIN applications a ON j.id = a.job_id
        WHERE j.company_id=?
        GROUP BY j.id
        ORDER BY j.id DESC
    ''', (session['company_id'],)).fetchall()

    conn.close()
    return render_template('company_dashboard.html', jobs=jobs, company=company, stats=stats)

@app.route('/post-job', methods=['GET', 'POST'])
def post_job():
    if 'company_id' not in session:
        return redirect('/company-login')

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        salary = request.form.get('salary', '').strip()
        location = request.form.get('location', '').strip()
        category = request.form.get('category', '').strip()
        experience = request.form.get('experience', '').strip()
        skills = request.form.get('skills', '').strip()
        contact = request.form.get('contact', '').strip()

        if not all([title, salary, location, category]):
            flash('Title, Salary, Location aur Category required hai!', 'error')
            return render_template('post_job.html', categories=JOB_CATEGORIES, locations=LOCATIONS)

        conn = get_db()
        conn.execute('INSERT INTO jobs (company_id, title, location, salary, experience, category, description, skills, contact, posted_on) VALUES (?,?,?,?,?,?,?,?,?,?)',
            (session['company_id'], title, location, salary, experience, category, description, skills, contact, datetime.now().strftime('%Y-%m-%d')))
        conn.commit()
        conn.close()
        flash('Job posted successfully!', 'success')
        return redirect('/company-dashboard')
    return render_template('post_job.html', categories=JOB_CATEGORIES, locations=LOCATIONS)

@app.route('/edit-job/<int:job_id>', methods=['GET', 'POST'])
def edit_job(job_id):
    if 'company_id' not in session:
        return redirect('/company-login')
    conn = get_db()
    job = conn.execute('SELECT * FROM jobs WHERE id=? AND company_id=?', (job_id, session['company_id'])).fetchone()
    if not job:
        conn.close()
        flash('Job not found!', 'error')
        return redirect('/company-dashboard')
    if request.method == 'POST':
        conn.execute('''UPDATE jobs SET title=?, description=?, salary=?, location=?,
                        category=?, experience=?, skills=?, contact=? WHERE id=?''',
                    (request.form['title'], request.form['description'], request.form['salary'],
                     request.form['location'], request.form['category'], request.form.get('experience',''),
                     request.form.get('skills',''), request.form.get('contact',''), job_id))
        conn.commit()
        conn.close()
        flash('Job updated successfully!', 'success')
        return redirect('/company-dashboard')
    conn.close()
    return render_template('edit_job.html', job=job, categories=JOB_CATEGORIES, locations=LOCATIONS)

@app.route('/delete-job/<int:job_id>')
def delete_job(job_id):
    if 'company_id' not in session:
        return redirect('/company-login')
    conn = get_db()
    conn.execute('DELETE FROM jobs WHERE id=? AND company_id=?', (job_id, session['company_id']))
    conn.commit()
    conn.close()
    flash('Job deleted successfully!', 'success')
    return redirect('/company-dashboard')

@app.route('/job-applications/<int:job_id>')
def job_applications(job_id):
    if 'company_id' not in session:
        return redirect('/company-login')
    conn = get_db()
    job = conn.execute('SELECT * FROM jobs WHERE id=? AND company_id=?', (job_id, session['company_id'])).fetchone()
    if not job:
        conn.close()
        flash('Job not found!', 'error')
        return redirect('/company-dashboard')
    applications = conn.execute('SELECT * FROM applications WHERE job_id=? ORDER BY id DESC', (job_id,)).fetchall()
    conn.close()
    return render_template('job_applications.html', job=job, applications=applications)

@app.route('/admin', methods=['GET', 'POST'])

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        if request.form.get('password') == os.environ.get('ADMIN_PASSWORD', 'admin123'):
            session['admin'] = True
        else:
            return render_template('admin_login.html', error='Invalid password')
    
    if not session.get('admin'):
        return render_template('admin_login.html')
    
    conn = get_db()
    companies = conn.execute('SELECT * FROM companies ORDER BY id DESC').fetchall()
    jobs = conn.execute('SELECT jobs.*, companies.company_name FROM jobs JOIN companies ON jobs.company_id = companies.id ORDER BY jobs.id DESC').fetchall()
    
    # YEH LINE ADD KAR 👇
    apps_count = conn.execute('SELECT COUNT(*) as count FROM applications').fetchone()['count']
    
    conn.close()
    
    # YAHAN apps_count ADD KAR 👇
    return render_template('admin.html', companies=companies, jobs=jobs, apps_count=apps_count)
@app.route('/toggle-featured/<int:job_id>')
def toggle_featured(job_id):
    if not session.get('admin'):
        return redirect('/admin')
    conn = get_db()
    job = conn.execute('SELECT featured FROM jobs WHERE id=?', (job_id,)).fetchone()
    new_status = 0 if job['featured'] else 1
    conn.execute('UPDATE jobs SET featured=? WHERE id=?', (new_status, job_id))
    conn.commit()
    conn.close()
    return redirect('/admin')

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('.', filename)

@app.route('/company-logout')
def company_logout():
    session.pop('company_id', None)
    session.pop('company_name', None)
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/check-db')
def check_db():
    conn = get_db()
    job_count = conn.execute('SELECT COUNT(*) as total FROM jobs').fetchone()
    conn.close()
    return f"<h2>Jobs: {job_count['total']}</h2>"

if __name__ == '__main__':
    app.run(debug=True)
