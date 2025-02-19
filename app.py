from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Mock user class - In production, this would be a database model
class User(UserMixin):
    def __init__(self, id, username, email, password_hash):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash

# Mock user database - In production, this would be a real database
users = {}

@login_manager.user_loader
def load_user(user_id):
    return users.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/features')
def features():
    return render_template('features.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if username in [user.username for user in users.values()]:
            flash('Username already exists')
            return redirect(url_for('register'))
        
        user_id = len(users) + 1
        users[user_id] = User(user_id, username, email, generate_password_hash(password))
        
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = next((u for u in users.values() if u.username == username), None)
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('play'))
        
        flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/marketplace')
@login_required
def marketplace():
    return render_template('marketplace.html')

@app.route('/leaderboard')
def leaderboard():
    return render_template('leaderboard.html')

@app.route('/play')
@login_required
def play():
    return render_template('play.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error_code=404, error_message="Page not found"), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', error_code=500, error_message="Internal server error"), 500

# Create error template
@app.route('/error')
def error():
    return render_template('error.html', 
                         error_code=request.args.get('code', 404),
                         error_message=request.args.get('message', 'Page not found'))

if __name__ == '__main__':
    # Create a test admin user
    admin_id = len(users) + 1
    users[admin_id] = User(
        admin_id,
        'admin',
        'admin@terminusa.online',
        generate_password_hash('admin123')
    )
    
    app.run(debug=True)
