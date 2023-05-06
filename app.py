from flask import Flask, render_template, redirect, url_for, request, jsonify
from greenlet import getcurrent
from flask_cors import CORS
import database as db
import models
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from sqlalchemy.orm import scoped_session
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize Flask app
app = Flask(__name__, template_folder = 'templates', static_folder = 'static')
CORS(app)
app.secret_key = '0v5hY7S4Ki'
app.session = scoped_session(db.databaseSession, getcurrent)
@app.teardown_appcontext
def remove_session(exception):
    app.session.remove()
    print("Request closed")

# Login Manager (FlaskLogin)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return models.Player.get_user(app.session, user_id)

def redirect_login():
    return redirect(url_for('login_page'))
login_manager.unauthorized_handler(redirect_login)

@app.route('/')
@login_required
def home_page():
    return render_template('home.html')

@app.route('/login/', methods=['GET'])
@app.route('/login', methods=['GET'])
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home_page'))
    
    username = request.form.get('username')
    password = request.form.get('password')

    player = models.login(app.session, username, password)

    if player:
        login_user(player)
        return redirect(url_for('home'))
    
    return redirect(url_for('login_page'))
    
@app.route('/logout/')
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register/', methods=['GET'])
@app.route('/register', methods=['GET'])
def register_page():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    username = request.form.get('username')
    password = request.form.get('password')

    player = models.register(app.session, username, password)

    if player:
        login_user(player)
        return redirect(url_for('home'))
    return "Username is taken!", 409

# Dungeon routes
@app.route('/dungeon')
@login_required
def get_dungeon():
    if current_user.dungeon:
        ###TODO could use Jinja here
        return current_user.dungeon.parse_map()
    else:
        return "You aren't in a dungeon!", 404

@app.route('/dungeon', methods = ['POST'])
@login_required
def gen_dungeon():
    if not current_user.dungeon:
        models.Dungeon.new(app.session, current_user)
    return "Success", 200

@app.route('/dungeon/move', methods = ['PUT'])
@login_required
def dungeon_move():
    # incoming request: 0 = up, 1 = right, 2 = down, 3 = left, 4 = floors
    direction = request.get_json()
    if not current_user.dungeon:
        return "Not currently in a dungeon!"
    if direction == 4:
        return current_user.dungeon.exit(app.session)[1]
    return current_user.dungeon.move(app.session, direction)[1]


# Home page
@app.route('/home')
def home():
    if current_user.dungeon:
        return redirect(url_for('display_dungeon'))
    return render_template('home.html')

# Market Page
@app.route('/market')
def market():
    if current_user.dungeon:
        return redirect(url_for('display_dungeon'))
    return render_template('market.html')

# Vault Page
@app.route('/vault')
def vault():
    if current_user.dungeon:
        return redirect(url_for('display_dungeon'))
    #tosend = []
    items = [ #testing tuple list
    ('Sword of Fire', 'A blazing sword that burns all in its path.'),
    ('Staff of Ice', 'A staff that can conjure freezing winds and icy shards.'),
    ('Bow of Lightning', 'A bow that shoots bolts of lightning that never miss.'),
    ('Dagger of Poison', 'A small dagger that can deliver lethal doses of poison.'),
    ('Hammer of Thunder', 'A heavy hammer that can create shockwaves that stun foes.'),
    ('Wand of Arcane Missiles', 'A wand that fires bolts of arcane energy.'),
    ]
    #item[0] is the name, item[1] is the description
    tosend = items
    # inv = current_user.get_unequipped()
    # for i in inv:
    #     tosend.append((i.item.name,i.item.desc()))
    return render_template('vault.html', tosend = tosend)

@app.route('/vault')
def inventory():
    if current_user.dungeon:
        return redirect(url_for('display_dungeon'))
    toinv = []
    inv = current_user.get_inventory()
    for i in inv:
        toinv.append((i.item.name,i.item.desc()))
    return render_template('vault.html', inv = toinv)

@app.route('/vault')
def equipped():
    if current_user.dungeon:
        return redirect(url_for('display_dungeon'))
    toequip = []
    hands = current_user.get_hands()
    armor = current_user.get_armor()

    for i in hands:
        toequip.append((i.item.name,i.item.desc()))
    for i in armor:
        toequip.append((i.item.name,i.item.desc()))
    return render_template('vault.html', hands = toequip, armor = toequip)


# How to Play
@app.route('/howtoplay')
def howtoplay():
    if current_user.dungeon:
        return redirect(url_for('display_dungeon'))
    return render_template('howtoplay.html')

# Account Page
@app.route('/account', methods=['GET', 'POST'])
def account():
    if current_user.dungeon:
        return redirect(url_for('display_dungeon'))
    if request.method == 'POST':
        currentPassword = request.form['current-password']
        newPassword = request.form['new-password']
        confirmPassword = request.form['confirm-password']

        if newPassword and newPassword == confirmPassword and current_user.check_password(currentPassword):
            current_user.change_password(app.session, newPassword)
        
        return redirect(url_for('account'))
    return render_template('account.html', user = current_user.username)

#Dungeon display (temp)
@app.route('/display_dungeon')
def display_dungeon():
    if current_user.dungeon:
        map_data = current_user.dungeon.parse_map()
        return render_template('dungeon.html', map_data = map_data)

# Testing pagessssss
@app.route('/test')
@app.route('/test/')
@login_required
def test():
    return render_template('test.html')

@app.route('/testgenitem')
@login_required
def testgen():
    return models.Item.gen(app.session, 10, current_user).item.desc(), 200

if __name__ == '__main__':
    app.run()