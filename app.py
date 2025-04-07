import subprocess
import re
from flask import Flask, render_template, redirect, url_for, request, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'Ps6 and pcg'

# PostgreSQL connection
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Ps6 and pcg@localhost/mariochat_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    avatar = db.Column(db.String(200), default='avatars/default.png')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
@login_required
def index():
    return render_template('index.html', username=current_user.username, avatar=current_user.avatar)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('index'))
        return 'Invalid credentials'
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if the username already exists in the database
        if User.query.filter_by(username=username).first():
            return 'Username already exists!'

        # Create a new user
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()

        # Redirect to login page after successful signup
        return redirect(url_for('login'))

    return render_template('signup.html')


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        # Update the username and password
        new_username = request.form.get('username')
        new_password = request.form.get('password')

        if new_username:
            current_user.username = new_username
        if new_password:
            current_user.password = new_password

        db.session.commit()  # Commit changes to the database

        return redirect(url_for('profile'))  # Redirect to the profile page to see changes

    return render_template('profile.html', username=current_user.username)



@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_message = request.json.get("message", "")

        # Run Ollama and capture output
        process = subprocess.Popen(
            ["ollama", "run", "mario"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        bot_response, error = process.communicate(input=user_message + "\n")

        # Clean the response
        def clean_text(text):
            text = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', text)
            text = text.replace("\r", "").replace("\n", "")
            return text[:200]

        clean_response = clean_text(bot_response).strip()

        return jsonify({'status': 'success', 'message': clean_response})

    except Exception as e:
        print("Exception:", e)
        return jsonify({'status': 'error', 'message': str(e)})

# Create database tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
