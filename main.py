import os
from flask import Flask, redirect, url_for, render_template
from db import init_app

from job_routes import jobs_bp
from auth_routes import auth_bp  
from admin_routes import admin_bp

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'surejob-secret-2026')

init_app(app)

app.register_blueprint(jobs_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)

@app.route('/')
def home():
    return redirect(url_for('jobs.job_list'))

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)
