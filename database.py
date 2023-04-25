from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class Player(UserMixin, db.Model):
    """
    The user object.

    Attributes:
     - id -- internal database unique identifier
     - username -- unique identifier used to log in
     - password -- encrypted and salted, used to log in

    Methods:
     - get_id() -- return id
    """

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)

    def get_id(self):
        return str(self.id)
    

def getUser(id: int) -> Player:
    """
    Retrieves a Player by ID

    Arguments:
     - id -- id of Player object
    """

    return db.session.execute(db.select(Player).where(Player.id == id)).scalar()

def login(username: str, password: str) -> Player:
    """
    Retrieves a Player by username and password, if any; if none, returns None.

    Arguments:
     - username -- username of Player
     - password -- password of Player
    """

    return db.session.execute(db.select(Player).where(Player.username == username, Player.password == password)).scalar()

def register(username: str, password: str) -> Player:
    """
    Tries to create a new user account.
    If successful, returns created account.
    If user with same username already exists, then returns None

    Arguments:
     - username -- username of new Player
     - password -- password of new Player
    """
    
    # Create new user
    try:
        newUser = db.session.execute(db.insert(Player).values(username = username, password = password).returning(Player)).scalar()
        db.session.commit()
    except db.exc.IntegrityError:
        # If username already taken
        return None
    
    return newUser
    
def reset() -> None:
    """
    Deletes and recreates the database.
    """
    
    db.drop_all()
    db.create_all()

def init(app: Flask) -> None:
    """
    Attaches the database to the current session. Call in main script before running the Flask application.

    Arguments:
     - app -- the Flask app
    """

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"
    db.init_app(app)