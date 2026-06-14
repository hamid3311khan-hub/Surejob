from flask import Flask, g, render_template, request, jsonify
from db import get_db, init_app
import os

app = Flask(__name__)
init_app(app)

@app.route('/')
def home():
    return "SureJob is Live! Server Running ✅"

@app.route('/db-test')
def db_test():
    try:
        db = get_db()
        cur = db.cursor()
        cur.execute('SELECT version();')
        db_version = cur.fetchone()
        cur.close()
        return f"DB Connected: {db_version['version']}"
    except Exception as e:
        return f"DB Error: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)
