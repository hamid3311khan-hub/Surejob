from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register')
def register():
    return "<h1 class='text-3xl font-bold text-center mt-20'>Company Register - Coming Soon 🔥</h1>"

@app.route('/login')
def login():
    return "<h1 class='text-3xl font-bold text-center mt-20'>Employer Login - Coming Soon 🔥</h1>"

@app.route('/jobs')
def jobs():
    return "<h1 class='text-3xl font-bold text-center mt-20'>Jobs Page - Coming Soon 🔥</h1>"

if __name__ == '__main__':
    app.run()
