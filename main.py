from flask import Flask, request, render_template, redirect, url_for
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    return render_template('candidate_register.html')

@app.route('/register', methods=['POST'])
def register():
    email = request.form.get('email')
    password = request.form.get('password')
    mobile = request.form.get('mobile')
    full_name = request.form.get('full_name')
    
    conn = get_db_connection()
    conn.execute('INSERT INTO candidates (email, password, mobile, full_name) VALUES (?, ?, ?, ?)',
                 (email, password, mobile, full_name))
    conn.commit()
    conn.close()
    
    return "Registration Successful!"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
