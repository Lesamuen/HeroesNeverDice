from database import Base
from flask_login import UserMixin
from sqlalchemy import ForeignKey, select, insert, update, delete
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session
from sqlalchemy.exc import IntegrityError
from typing import List

class Player(UserMixin, Base):
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

    __tablename__ = "player"

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

    # Items
    vault: Mapped[List["ItemVault"]] = relationship(back_populates = "owner")
    inventory: Mapped[List["ItemInv"]] = relationship(back_populates = "owner")
    listings: Mapped[List["ItemMarket"]] = relationship(back_populates = "owner")

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
    def fuse_dice(self, typeFrom: int, amount: int) -> int:
        """
        Combines two dice of lower denomination into one die of denomination above.

        types: 0 -- d4, 1 -- d6, ... 5 -- d20

        Arguments:
         - typeFrom: lower denomination of dice to fuse
         - amount: amount of higher denomination to try to create

        Returns:
         - 0 -- success
         - 1 -- not enough dice
         - 2 -- non-valid type
        """

        return 0


class Item(Base):
    """
    Base class for all items; item database sharded into
     - ones in player vaults (can't be lost)
     - ones in player inventories (lost on death)
     - ones on the market (can't be used until taken off market)

    Attributes:
     - id -- unique identifier for this item
     - itemType -- type of item; 0: weapon, 1: shield, 2: armor
     - name -- name of the item
     - iLvl -- the 'level' of the item that was used to generate its attributes

    Methods:
     - gen -- generate a random item
     - copy -- return self as args
    """

    __tablename__ = 'item'
    __mapper_args__ = {'polymorphic_on': 'itemType'}

    id: Mapped[int] = mapped_column(primary_key=True)

    # Type of item
    itemType: Mapped[int]
    name: Mapped[str]
    iLvl: Mapped[int]


    ###TODO
    @staticmethod
    def gen(iLvl: int) -> dict[str, int]:
        """
        Generates a random item, given an item level, and passes a dictionary to be used as arguments for constructor.

        Arguments:
         - iLvl -- the item level

        Returns:
         - Dictionary of arguments for derived Item constructor
         - None if invalid item level
        """

        return dict()
    
    ###TODO
    def copy() -> dict[str, int]:
        """
        Converts this item into dictionary of constructor arguments; used to move between inventories, for example.

        Returns:
         - Dictionary of arguments for derived Item constructor
        """

        return dict()


class ItemWeapon(Item):
    """
    Weapons are used to Attack. Either one-handed or two-handed.

    Attributes:
     - attack -- base attack value for weapon
     - d4
     - ... -- max dice spent for attack
     - d20
     - twoh -- whether weapon is two-handed or one-handed
    """

    __mapper_args__ = {'polymorphic_identity': 0}

    attack: Mapped[int] = mapped_column(nullable = True)

    d4: Mapped[int] = mapped_column(nullable = True, use_existing_column = True)
    d6: Mapped[int] = mapped_column(nullable = True, use_existing_column = True)
    d8: Mapped[int] = mapped_column(nullable = True, use_existing_column = True)
    d10: Mapped[int] = mapped_column(nullable = True, use_existing_column = True)
    d12: Mapped[int] = mapped_column(nullable = True, use_existing_column = True)
    d20: Mapped[int] = mapped_column(nullable = True, use_existing_column = True)

    twoh: Mapped[bool] = mapped_column(nullable = True)
    

class ItemShield(Item):
    """
    Shields are used to Defend. Always one-handed.

    Attributes:
     - d4
     - ... -- max dice spent for defense
     - d20
    """

    __mapper_args__ = {'polymorphic_identity': 1}

    d4: Mapped[int] = mapped_column(nullable = True, use_existing_column = True)
    d6: Mapped[int] = mapped_column(nullable = True, use_existing_column = True)
    d8: Mapped[int] = mapped_column(nullable = True, use_existing_column = True)
    d10: Mapped[int] = mapped_column(nullable = True, use_existing_column = True)
    d12: Mapped[int] = mapped_column(nullable = True, use_existing_column = True)
    d20: Mapped[int] = mapped_column(nullable = True, use_existing_column = True)
    

class ItemArmor(Item):
    """
    Armor is what provides all base defensive stats.

    Attributes:
     - health -- max hp increase for armor
     - defense -- base defense value for armor
     - speed -- initiative/turn speed for armor
    """

    __mapper_args__ = {'polymorphic_identity': 2}

    health: Mapped[int] = mapped_column(nullable = True)
    defense: Mapped[int] = mapped_column(nullable = True)
    speed: Mapped[int] = mapped_column(nullable = True)


class ItemVault(Base):
    """
    Represents an Item in a Player's vault; cannot be lost unless sold or deliberately deleted.

    Arguments:
     - item_id -- id of the Item
     - item -- reference to the Item
     - owner_id -- id of the Item's owner
     - owner -- reference to Player that owns this Item
    """

    __tablename__ = "vault"

    item_id: Mapped[int] = mapped_column(ForeignKey("item.id"), primary_key = True)
    item: Mapped["Item"] = relationship()

    owner_id: Mapped[int] = mapped_column(ForeignKey("player.id"), primary_key = True)
    owner: Mapped["Player"] = relationship(back_populates = "vault")
    

class ItemInv(Base):
    """
    Represents an Item in a Player's inventory; lost upon death, and moved to vault when leaving dungeon

    Arguments:
     - item_id -- id of the Item
     - item -- reference to the Item
     - owner_id -- id of the Item's owner
     - owner -- reference to Player that owns this Item
     - equipped -- whether owner is actively using this Item
    """

    __tablename__ = "inventory"

    item_id: Mapped[int] = mapped_column(ForeignKey("item.id"), primary_key = True)
    item: Mapped["Item"] = relationship()

    owner_id: Mapped[int] = mapped_column(ForeignKey("player.id"), primary_key = True)
    owner: Mapped["Player"] = relationship(back_populates = "inventory")
    
    equipped: Mapped[bool] = mapped_column(default = False)


class ItemMarket(Base):
    """
    Represents an Item listed by a Player on the Market; stays until taken off or another Player buys it.

    Arguments:
     - item_id -- id of the Item
     - item -- reference to the Item
     - owner_id -- id of the Item's owner
     - owner -- reference to Player that owns this Item
     - price -- amount of d4s (matching fusing exchange rates) the owner has put the Item up for sale
    """
    
    __tablename__ = "market"

    item_id: Mapped[int] = mapped_column(ForeignKey("item.id"), primary_key = True)
    item: Mapped["Item"] = relationship()

    owner_id: Mapped[int] = mapped_column(ForeignKey("player.id"), primary_key = True)
    owner: Mapped["Player"] = relationship(back_populates = "listings")

    price: Mapped[int]



def getUser(session: Session, id: int) -> Player:
    """
    Retrieves a Player by ID

    Arguments:
     - session -- request context
     - id -- id of Player object

    Returns:
     - Player object with matching id
     - None if no matching id
    """

    return session.execute(select(Player).where(Player.id == id)).scalar()


def login(session: Session, username: str, password: str) -> Player:
    """
    Retrieves a Player by username and password, if any; if none, returns None.

    Arguments:
     - session -- request context
     - username -- username of Player
     - password -- password of Player

    Returns:
     - Player object with matching username/password combo
     - None if no matching username or incorrect password
    """

    return session.execute(select(Player).where(Player.username == username, Player.password == password)).scalar()


def register(session: Session, username: str, password: str) -> Player:
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
        newUser = session.execute(insert(Player).values(username = username, password = password).returning(Player)).scalar()
        session.commit()
    except IntegrityError:
        # If username already taken
        return None
    
    return newUser
