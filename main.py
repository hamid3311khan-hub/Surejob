from flask import Flask, g, render_template, request, jsonify
from db import get_db, init_app
import os

app = Flask(__name__)

# db ko app se jod de
init_app(app)

# Database use karne ka example
@app.route('/')
def home():
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT version();')
    db_version = cur.fetchone()
    cur.close()
    return f"SureJob is Live! DB Connected: {db_version['version']}"

# Tere purane routes yahan daal de
# Example:
# @app.route('/jobs')
# def get_jobs():
#     db = get_db()
#     cur = db.cursor()
#     cur.execute('SELECT * FROM jobs;')
#     jobs = cur.fetchall()
#     cur.close()
#     return jsonify(jobs)

if __name__ == '__main__':
    app.run(debug=True)
