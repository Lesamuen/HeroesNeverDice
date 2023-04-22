from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

def init(app: Flask) -> None:
    """
    Attaches the database to the current session. Call in main script before running the Flask application.

    Arguments:
        app -- the Flask app
    """

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"
    db.init_app(app)