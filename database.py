from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from typing import List, Optional

db = SQLAlchemy()

class Player(UserMixin, db.Model):
    """
    The user object.

    Attributes:
     - id -- internal database unique identifier
     - username -- unique identifier used to log in
     - password -- encrypted and salted, used to log in
     - d20
     - ... -- the dice currency of the Player
     - d4
     - split_conv -- index to find splitting conversion rates

    Methods:
     - get_id -- return id
     - split_dice -- split currency into lower currency
     - fuse_dice -- join currency into higher currency
    """

    id: Mapped[int] = mapped_column(primary_key = True)
    username: Mapped[str] = mapped_column(unique = True)
    password: Mapped[str]
    
    # Currency
    d4: Mapped[int] = mapped_column(default = 0)
    d6: Mapped[int] = mapped_column(default = 0)
    d8: Mapped[int] = mapped_column(default = 0)
    d10: Mapped[int] = mapped_column(default = 0)
    d12: Mapped[int] = mapped_column(default = 0)
    d20: Mapped[int] = mapped_column(default = 0)
    split_conv = ((), (1,), (2, 1), (2, 1, 1), (3, 2, 1, 1), (5, 3, 2, 2, 1))

    def get_id(self):
        return str(self.id)
    
    # Currency methods
    ###TODO
    def split_dice(self, typeFrom: int, typeTo: int, amount: int) -> int:
        """
        Splits a higher denomination of dice into an equivalent amount of lower denominations, rounded down

        types: 0 -- d4, 1 -- d6, ... 5 -- d20

        Arguments:
         - typeFrom -- the higher denomination of dice
         - typeTo -- the lower denomination of dice
         - amount -- the amount of dice to convert

        Returns:
         - 0 -- success
         - 1 -- not enough dice
         - 2 -- first argument not of higher denomination
         - 3 -- non-valid type
        """

        return 0

    ###TODO
    def fuse_dice(self, type: int, amount: int) -> int:
        """
        Combines two dice of lower denomination into one die of denomination above.

        types: 0 -- d4, 1 -- d6, ... 5 -- d20

        Arguments:
         - type: lower denomination of dice to fuse
         - amount: amount of higher denomination to try to create

        Returns:
         - 0 -- success
         - 1 -- not enough dice
         - 2 -- non-valid type
        """

        return 0

def getUser(id: int) -> Player:
    """
    Retrieves a Player by ID

    Arguments:
     - id -- id of Player object

    Returns:
     - Player object with matching id
     - None if no matching id
    """

    return db.session.execute(db.select(Player).where(Player.id == id)).scalar()

def login(username: str, password: str) -> Player:
    """
    Retrieves a Player by username and password, if any; if none, returns None.

    Arguments:
     - username -- username of Player
     - password -- password of Player

    Returns:
     - Player object with matching username/password combo
     - None if no matching username or incorrect password
    """

    return db.session.execute(db.select(Player).where(Player.username == username, Player.password == password)).scalar()

def register(username: str, password: str) -> Player:
    """
    Tries to create a new user account.

    Arguments:
     - username -- username of new Player
     - password -- password of new Player

    Returns:
     - Player object of newly created account
     - None if username is taken
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