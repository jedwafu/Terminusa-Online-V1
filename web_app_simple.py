import os
from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_cors import CORS

# Create and configure the Flask application
app = Flask(__name__, 
            static_url_path='/static',
            static_folder='static')
CORS(app)

# Configure app
app.config.update(
    SEND_FILE_MAX_AGE_DEFAULT=0,  # Disable caching during development
    SECRET_KEY='dev-key-please-change',
)

# Configure logging
import logging
os.makedirs('logs', exist_ok=True)  # Ensure logs directory exists
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Create file handler
file_handler = logging.FileHandler('logs/web.log')
file_handler.setFormatter(formatter)

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

# Add handlers to logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

@app.route('/')
def index():
    """Render homepage"""
    return render_template('index_simple.html')

@app.route('/play')
def play_page():
    """Play page"""
    return redirect('https://play.terminusa.online')

@app.route('/login')
def login_page():
    """Login page"""
    try:
        return render_template('login_simple.html', 
                             title='Login')
    except Exception as e:
        logger.error(f"Error rendering login page: {str(e)}")
        return render_template('error_simple.html', 
                             error_message='An error occurred while loading the page. Please try again later.'), 500

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Not found'}), 404
    return render_template('error_simple.html', 
                         error_message='The page you are looking for could not be found.'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Internal server error'}), 500
    return render_template('error_simple.html', 
                         error_message='An internal server error occurred. Please try again later.'), 500

if __name__ == '__main__':
    # Create simple templates
    os.makedirs('templates', exist_ok=True)
    
    with open('templates/index_simple.html', 'w') as f:
        f.write("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Terminusa Online</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #000;
            color: #0f0;
            text-align: center;
            padding: 50px;
        }
        h1 {
            font-size: 3em;
            margin-bottom: 20px;
        }
        p {
            font-size: 1.2em;
            margin-bottom: 30px;
        }
        .button {
            display: inline-block;
            padding: 10px 20px;
            background-color: #0f0;
            color: #000;
            text-decoration: none;
            border-radius: 5px;
            font-weight: bold;
            margin: 10px;
        }
    </style>
</head>
<body>
    <h1>Welcome to Terminusa Online</h1>
    <p>A Terminal-based MMORPG inspired by Solo Leveling</p>
    <a href="/play" class="button">Play Now</a>
    <a href="/login" class="button">Login</a>
</body>
</html>
        """)
    
    with open('templates/login_simple.html', 'w') as f:
        f.write("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - Terminusa Online</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #000;
            color: #0f0;
            text-align: center;
            padding: 50px;
        }
        h1 {
            font-size: 2em;
            margin-bottom: 20px;
        }
        form {
            max-width: 300px;
            margin: 0 auto;
        }
        input {
            width: 100%;
            padding: 10px;
            margin-bottom: 15px;
            background-color: #111;
            border: 1px solid #0f0;
            color: #0f0;
        }
        button {
            padding: 10px 20px;
            background-color: #0f0;
            color: #000;
            border: none;
            border-radius: 5px;
            font-weight: bold;
            cursor: pointer;
        }
        a {
            color: #0f0;
            text-decoration: none;
            display: block;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <h1>Login to Terminusa Online</h1>
    <form>
        <input type="text" placeholder="Username" required>
        <input type="password" placeholder="Password" required>
        <button type="submit">Login</button>
    </form>
    <a href="/">Back to Home</a>
</body>
</html>
        """)
    
    with open('templates/error_simple.html', 'w') as f:
        f.write("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Error - Terminusa Online</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #000;
            color: #f00;
            text-align: center;
            padding: 50px;
        }
        h1 {
            font-size: 2em;
            margin-bottom: 20px;
        }
        p {
            font-size: 1.2em;
            margin-bottom: 30px;
        }
        a {
            color: #0f0;
            text-decoration: none;
        }
    </style>
</head>
<body>
    <h1>Error</h1>
    <p>{{ error_message }}</p>
    <a href="/">Back to Home</a>
</body>
</html>
        """)
    
    # Get port from environment or use default
    port = int(os.environ.get('WEBAPP_PORT', 3000))
    
    # Run the app
    app.run(host='0.0.0.0', port=port, debug=False)
