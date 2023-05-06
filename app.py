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

@app.route('/dungeon/attack', methods = ['PUT'])
@login_required
def dungeon_attack():
    spent = request.get_json()['spent_dice']
    return current_user.dungeon.battle.attack(app.session, spent)
    

@app.route('/dungeon/defend', methods = ['PUT'])
@login_required
def dungeon_defense():
    spent = request.get_json()['spent_dice']
    return current_user.dungeon.battle.defense(app.session, spent)
    

@app.route('/dungeon/retreat', methods = ['PUT'])
@login_required
def dungeon_retreat():
    return current_user.dungeon.battle.retreat(app.session)

# Home page
@app.route('/home')
@login_required
def home():
    if current_user.dungeon:
        return redirect(url_for('display_dungeon'))
    return render_template('home.html')

# Market Page
@app.route('/market')
@login_required
def market():
    if current_user.dungeon:
        return redirect(url_for('display_dungeon'))
    return render_template('market.html')

# Vault Page
@app.route('/vault')
@login_required
def vault():
    if current_user.dungeon:
        return redirect(url_for('display_dungeon'))
    
    vaultDisplay = []
    for item in current_user.vault:
        vaultDisplay.append((item.item_id, item.item.name, item.item.desc()))
    invDisplay = []
    for item in current_user.get_unequipped():
        invDisplay.append((item.item_id, item.item.name, item.item.desc()))

    hands = current_user.get_hands()
    if hands[0]:
        mainhand = (hands[0].item_id, hands[0].item.name, hands[0].item.desc())
    else:
        mainhand = (-1, "Fists", "You are holding nothing in this hand.")
    if hands[1]:
        offhand = (hands[1].item_id, hands[1].item.name, hands[1].item.desc())
    else:
        offhand = (-1, "Fists", "You are holding nothing in this hand.")
    armor = current_user.get_armor()
    if armor:
        armor = (armor.item_id, armor.item.name, armor.item.desc())
    else:
        armor = (-1, "Nothing", "You are wearing nothing but rags.")

    return render_template('vault.html', vault = vaultDisplay, inv = invDisplay, mainhand = mainhand, offhand = offhand, armor = armor)

# Inventory actions
@app.route('/equip_item', methods = ['PUT'])
@login_required
def equip_item():
    id = request.get_json()
    item: models.ItemInv = current_user.get_inv_item(app.session, id)
    if item:
        item.equip(app.session)
    return "Success", 200

@app.route('/unequip_item', methods = ['PUT'])
@login_required
def unequip_item():
    id = request.get_json()
    item: models.ItemInv = current_user.get_inv_item(app.session, id)
    if item:
        item.unequip(app.session)
    return "Success", 200

# How to Play
@app.route('/howtoplay')
@login_required
def howtoplay():
    if current_user.dungeon:
        return redirect(url_for('display_dungeon'))
    return render_template('howtoplay.html')

# Account Page
@app.route('/account', methods=['GET', 'POST'])
@login_required
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
@login_required
def display_dungeon():
    if current_user.dungeon:
        map_data = current_user.dungeon.parse_map()
        dice_values =['d4, d6, d8, d10, d12, d20']
        health = current_user.get_health(app.session)
        dice = current_user.get_dice()
        totalattack = current_user.get_attack(app.session)
        attack = totalattack[0]
        active_attack= totalattack[1:]
        defense = current_user.get_defense(app.session)
        active_defense = current_user.get_active_defense(app.session)
        speed = current_user.get_speed(app.session)
        ### formatting with dice
        dice_available=[]
        dice_with_attack =[]
        dice_with_defense=[]
        ## max amount of dice - dice type for attack
        for i in range(len(dice_values)):
            if active_attack[i] != 0:
                dice_with_attack.append(f'{active_attack[i]} - {dice_values[i]}')
            else:
                dice_with_attack.append(f'0 - {dice_values[i]}')
        ## dice amount - dice type
        for i in range(len(dice_values)):
            if dice[i] != 0:
                dice_available.append(f'{dice[i]} - {dice_values[i]}')
            else:
                dice_available.append(f'0 - {dice_values[i]}')
        ## max amount of dice - dice type for defense
        for i in range(len(dice_values)):
            if active_defense[i] != 0:
                dice_with_defense.append(f'{active_defense[i]} - {dice_values[i]}')
            else:
                dice_with_defense.append(f'0 - {dice_values[i]}')

        if current_user.dungeon.battle:
            state = 'battle'
        else:
            state = 'explore'

    return render_template('dungeon.html', map_data = map_data, dice_values=dice_values, 
                           health = health, dice_available = dice_available, state=state, attack = attack, defense = defense,
                           dice_with_defense = dice_with_defense, dice_with_attack = dice_with_attack, speed = speed)

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