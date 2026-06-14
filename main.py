from flask import Flask, render_template
from db import init_app
from job_routes import job_bp
import os

app = Flask(__name__)
init_app(app)
app.register_blueprint(job_bp)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/db-test')
def db_test():
    from db import get_db
    try:
        db = get_db()
        cur = db.cursor()
        cur.execute('SELECT version();')
        version = cur.fetchone()
        cur.close()
        return f"DB Connected: {version['version']}"
    except Exception as e:
        return f"DB Error: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)
