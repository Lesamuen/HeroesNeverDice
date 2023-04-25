from flask import Flask, render_template, redirect, url_for, request, abort
import database as db
from flask_login import LoginManager, current_user, login_user, logout_user, login_required

# Initialize Flask app
app = Flask(__name__, template_folder = 'templates', static_folder = 'static')
app.secret_key = '0v5hY7S4Ki'

# Login Manager (FlaskLogin)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return db.getUser(user_id)

def redirect_login():
    return redirect(url_for('login_page'))
login_manager.unauthorized_handler(redirect_login)

# Testing pages
@app.route('/')
@login_required
def home_page():
    return render_template('home.html')

@app.route('/login/', methods=['GET'])
@app.route('/login', methods=['GET'])
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for('home_page'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home_page'))
    
    username = request.form.get('username')
    password = request.form.get('password')

    player = db.login(username, password)

    if player:
        login_user(player)
        return redirect(url_for('home_page'))
    
    return redirect(url_for('login_page'))
    
@app.route('/logout/')
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login_page'))

@app.route('/register/', methods=['GET'])
@app.route('/register', methods=['GET'])
def register_page():
    if current_user.is_authenticated:
        return redirect(url_for('home_page'))
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home_page'))
    
    username = request.form.get('username')
    password = request.form.get('password')

    player = db.register(username, password)

    if player:
        login_user(player)
        return redirect(url_for('home_page'))
    return "Username is taken!", 409

# REMOVE THIS FROM FINAL PRODUCT
@app.route('/reset/')
@app.route('/reset')
def reset():
    db.reset()
    return redirect(url_for('home_page'))

if __name__ == '__main__':
    db.init(app)
    app.run()