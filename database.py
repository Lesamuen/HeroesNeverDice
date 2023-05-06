from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

databaseEngine = create_engine("sqlite:///instance/db.sqlite")

databaseSession = sessionmaker(databaseEngine, autocommit = False, autoflush = False)

class Base(DeclarativeBase):
    """
    Used to make SQLAlchemy ORM work
    """
    pass

def dbInit() -> None:
    """
    Resets the database. We call this only once per structure change.
    """

    Base.metadata.drop_all(databaseEngine)
    Base.metadata.create_all(databaseEngine)