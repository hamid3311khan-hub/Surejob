from flask import Flask, request, redirect, session
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'surejob_mobile_2026'

def get_db():
    conn = sqlite3.connect('surejob.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("CREATE TABLE IF NOT EXISTS candidates (id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, phone TEXT, password TEXT, registered_on TEXT)")
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return "SureJob Running ✅ <br><a href='/candidate-register'>Register</a> | <a href='/candidate-login'>Login</a>"

@app.route('/candidate-register', methods=['GET', 'POST'])
def candidate_register():
    if request.method == 'POST':
        name = request.form.get('name', '')
        email = request.form.get('email', '')
        phone = request.form.get('phone', '')
        password = request.form.get('password', '')
        hashed_password = generate_password_hash(password)
        conn = get_db()
        try:
            conn.execute('INSERT INTO candidates (name, email, phone, password, registered_on) VALUES (?,?,?,?,?)', (name, email, phone, hashed_password, datetime.now().strftime('%Y-%m-%d %H:%M')))
            conn.commit()
            conn.close()
            return "Registration ho gaya! <a href='/candidate-login'>Login karo</a>"
        except:
            conn.close()
            return "Email already hai"
    return '<form method="post">Name: <input name="name"><br>Email: <input name="email"><br>Phone: <input name="phone"><br>Password: <input name="password" type="password"><br><button>Register</button></form>'

@app.route('/candidate-login', methods=['GET', 'POST'])
def candidate_login():
    if request.method == 'POST':
        email = request.form.get('email', '')
        password = request.form.get('password', '')
        conn = get_db()
        candidate = conn.execute('SELECT * FROM candidates WHERE email=?', (email,)).fetchone()
        conn.close()
        if candidate and check_password_hash(candidate['password'], password):
            session['candidate_id'] = candidate['id']
            session['candidate_name'] = candidate['name']
            return "Login ho gaya " + candidate['name'] + "! <a href='/'>Home</a>"
        return "Galat password"
    return '<form method="post">Email: <input name="email"><br>Password: <input name="password" type="password"><br><button>Login</button></form>'

if __name__ == '__main__':
    app.run()
