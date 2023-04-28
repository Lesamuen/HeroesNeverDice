from database import Base
from flask_login import UserMixin
from sqlalchemy import ForeignKey, select, insert, update, delete
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional, Tuple

class Player(UserMixin, Base):
    """
    The user object.

    Attributes:
     - id: internal database unique identifier
     - username: unique identifier used to log in
     - password: encrypted and salted, used to log in
     - dice: the dice currency of the Player
     - split_conv: index to find splitting conversion rates
     - vault: reference to list of all items in vault
     - inventory: reference to list of all items in inventory
     - listings: reference to list of all items put up on market
     - dungeon: reference to currently generated dungeon

    Methods:
     - get_id: return id
     - split_dice: split currency into lower currency
     - fuse_dice: join currency into higher currency
    """

    __tablename__ = "player"

    id: Mapped[int] = mapped_column(primary_key = True)
    username: Mapped[str] = mapped_column(unique = True)
    password: Mapped[str]
    
    # Currency
    dice: Mapped[bytes] = mapped_column(default = bytes([0, 0, 0, 0, 0, 0]))
    split_conv = ((), (1,), (2, 1), (2, 1, 1), (3, 2, 1, 1), (5, 3, 2, 2, 1))

    # Items
    vault: Mapped[List["ItemVault"]] = relationship(back_populates = "owner")
    inventory: Mapped[List["ItemInv"]] = relationship(back_populates = "owner")
    listings: Mapped[List["ItemMarket"]] = relationship(back_populates = "owner")

    dungeon: Mapped[Optional["Dungeon"]] = relationship(back_populates = "player")

    def get_id(self):
        return str(self.id)
    
    # Currency methods
    def get_dice(self) -> Tuple[int]:
        """
        Returns currency as list of integers from d4 to d20
        """
        
        currency = []
        for i in range(6):
            currency.append(int.from_bytes(self.dice[(i * 4) : (i * 4 + 4)]))

        return tuple(currency)


    def split_dice(self, session: Session, typeFrom: int, typeTo: int, amount: int) -> int:
        """
        Splits a higher denomination of dice into an equivalent amount of lower denominations, rounded down

        types: 0: d4, 1: d6, ... 5: d20

        Arguments:
         - session: request context
         - typeFrom: the higher denomination of dice
         - typeTo: the lower denomination of dice
         - amount: the amount of dice to convert

        Returns:
         - 0: success
         - 1: not enough dice
         - 2: first argument not of higher denomination
         - 3: non-valid type
        """

        # Checks for invalidation
        if not typeFrom > typeTo:
            return 2
        if typeFrom < 0 or typeTo < 0 or typeFrom > 5 or typeTo > 5:
            return 3
        diceFrom = int.from_bytes(self.dice[(typeFrom * 4) : (typeFrom * 4 + 4)])
        if diceFrom < amount:
            return 1
        
        diceTo = int.from_bytes(self.dice[(typeTo * 4) : (typeTo * 4 + 4)])

        diceFrom -= amount
        diceTo += amount * Player.split_conv[typeFrom][typeTo]
        bytesFrom = diceFrom.to_bytes(4)
        bytesTo = diceTo.to_bytes(4)

        newCurrency = bytearray(self.dice)
        newCurrency[typeFrom * 4] = bytesFrom[0]
        newCurrency[typeFrom * 4 + 1] = bytesFrom[1]
        newCurrency[typeFrom * 4 + 2] = bytesFrom[2]
        newCurrency[typeFrom * 4 + 3] = bytesFrom[3]
        newCurrency[typeTo * 4] = bytesTo[0]
        newCurrency[typeTo * 4 + 1] = bytesTo[1]
        newCurrency[typeTo * 4 + 2] = bytesTo[2]
        newCurrency[typeTo * 4 + 3] = bytesTo[3]

        self.dice = bytes(newCurrency)
        session.commit()
        return 0


    def fuse_dice(self, session: Session, typeFrom: int, amount: int) -> int:
        """
        Combines two dice of lower denomination into one die of denomination above.

        types: 0: d4, 1: d6, ... 5: d20

        Arguments:
         - session: request context
         - typeFrom: lower denomination of dice to fuse
         - amount: amount of higher denomination to try to create

        Returns:
         - 0: success
         - 1: not enough dice
         - 2: non-valid type
        """

        # Checks for invalidation
        if typeFrom < 0 or typeFrom > 4:
            return 2
        diceFrom = int.from_bytes(self.dice[(typeFrom * 4) : (typeFrom * 4 + 4)])
        if diceFrom < amount * 2:
            return 1
        
        diceTo = int.from_bytes(self.dice[(typeFrom * 4 + 4) : (typeFrom * 4 + 8)])

        diceFrom -= amount * 2
        diceTo += amount
        bytesFrom = diceFrom.to_bytes(4)
        bytesTo = diceTo.to_bytes(4)

        newCurrency = bytearray(self.dice)
        newCurrency[typeFrom * 4] = bytesFrom[0]
        newCurrency[typeFrom * 4 + 1] = bytesFrom[1]
        newCurrency[typeFrom * 4 + 2] = bytesFrom[2]
        newCurrency[typeFrom * 4 + 3] = bytesFrom[3]
        newCurrency[(typeFrom + 1) * 4] = bytesTo[0]
        newCurrency[(typeFrom + 1) * 4 + 1] = bytesTo[1]
        newCurrency[(typeFrom + 1) * 4 + 2] = bytesTo[2]
        newCurrency[(typeFrom + 1) * 4 + 3] = bytesTo[3]

        self.dice = bytes(newCurrency)
        session.commit()
        return 0


class Item(Base):
    """
    Base class for all items; item database sharded into
     - ones in player vaults (can't be lost)
     - ones in player inventories (lost on death)
     - ones on the market (can't be used until taken off market)

    Attributes:
     - id: unique identifier for this item
     - itemType: type of item; 0: weapon, 1: shield, 2: armor
     - name: name of the item
     - iLvl: the 'level' of the item that was used to generate its attributes

    Methods:
     - gen: generate a random item
     - copy: return self as args
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
         - iLvl: the item level

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
     - attack: base attack value for weapon
     - dice_budget: max dice spent for attack
     - twoh: whether weapon is two-handed or one-handed
    """

    __mapper_args__ = {'polymorphic_identity': 0}

    attack: Mapped[int] = mapped_column(nullable = True)

    dice_budget: Mapped[bytes] = mapped_column(nullable = True, use_existing_column = True)

    twoh: Mapped[bool] = mapped_column(nullable = True)
    

class ItemShield(Item):
    """
    Shields are used to Defend. Always one-handed.

    Attributes:
     - dice_budget: max dice spent for defense
    """

    __mapper_args__ = {'polymorphic_identity': 1}

    dice_budget: Mapped[bytes] = mapped_column(nullable = True, use_existing_column = True)
    

class ItemArmor(Item):
    """
    Armor is what provides all base defensive stats.

    Attributes:
     - health: max hp increase for armor
     - defense: base defense value for armor
     - speed: initiative/turn speed for armor
    """

    __mapper_args__ = {'polymorphic_identity': 2}

    health: Mapped[int] = mapped_column(nullable = True)
    defense: Mapped[int] = mapped_column(nullable = True)
    speed: Mapped[int] = mapped_column(nullable = True)


class ItemVault(Base):
    """
    Represents an Item in a Player's vault; cannot be lost unless sold or deliberately deleted.

    Arguments:
     - item_id: id of the Item
     - item: reference to the Item
     - owner_id: id of the Item's owner
     - owner: reference to Player that owns this Item
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
     - item_id: id of the Item
     - item: reference to the Item
     - owner_id: id of the Item's owner
     - owner: reference to Player that owns this Item
     - equipped: whether owner is actively using this Item
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
     - item_id: id of the Item
     - item: reference to the Item
     - owner_id: id of the Item's owner
     - owner: reference to Player that owns this Item
     - price: amount of d4s (matching fusing exchange rates) the owner has put the Item up for sale
    """
    
    __tablename__ = "market"

    item_id: Mapped[int] = mapped_column(ForeignKey("item.id"), primary_key = True)
    item: Mapped["Item"] = relationship()

    owner_id: Mapped[int] = mapped_column(ForeignKey("player.id"), primary_key = True)
    owner: Mapped["Player"] = relationship(back_populates = "listings")

    price: Mapped[int]


class Dungeon(Base):
    """
    Represents a Player's generated Dungeon floor. Incrementing in floor just means a new 'Dungeon' is generated.

    iLvl = floor * 10.
    Every room exists on a 10x10 grid; i.e. 100 rooms per floor.
    50% empty, 20% items, 30% monsters. 1 guaranteed entrance (return to home) and exit (go to next floor). 1 guaranteed boss (monster of 2 floors up), drops item of 1 floor up.

    Attributes:
     - player_id: id of Player this Dungeon belongs to; primary key because one-to-one relationship
     - player: reference to related Player
     - floor: floor level
     - floor_data: byte data for all rooms
     - position: x and y positions in 4 bits each of player
     - battle: if active battle, then reference to battle
    """

    __tablename__ = "dungeon"

    player_id: Mapped[int] = mapped_column(ForeignKey("player.id"), primary_key = True)
    player: Mapped["Player"] = relationship(back_populates = "dungeon")

    floor: Mapped[int]
    floor_data: Mapped[bytes]
    """
    Each room 1 byte. Therefore, 100 bytes total per floor.
     - 6 bits - room type
       - 0: empty
       - 1: item
       - 2: monster
       - 3: boss
       - 4: entrance
       - 5: exit
     - 1 bit - explored or not (shown on map, empty while passing through)
     - 1 bit - blocked or not (if fleed from enemy, cannot return to same room)
     - Stuff like items and monsters aren't generated until arriving at room.
    """

    position: Mapped[int]

    battle: Mapped[Optional["Battle"]] = relationship(back_populates = "dungeon")
    """If null, then not in battle."""


class Battle(Base):
    """
    Describes an active battle. Used for entered monster rooms. Includes data for active monster and stats.
    Because room disabled upon fleeing, only need one-to-one relationship.

    Attributes:
     - dungeon_id: id of Dungeon this battle belongs to
     - dungeon: reference to related Dungeon
     - player_hp: CURRENT hp of player
     - player_init: current turn tick for player
     - enemy_hp: CURRENT hp of enemy
     - enemy_init: current turn tick for enemy
     - enemy_speed: speed stat of enemy
     - enemy_defense: defense stat of enemy
     - enemy_value: starting dice pool, determines how much dice given to player upon defeat
     - enemy_pool: how much dice enemy has left; will try to flee when out
     - enemy_spend: how much dice the enemy tries to spend on attacking/defending every turn
    """

    __tablename__ = "battle"

    dungeon_id: Mapped[int] = mapped_column(ForeignKey("dungeon.player_id"), primary_key = True)
    dungeon: Mapped["Dungeon"] = relationship(back_populates = "battle")

    player_hp: Mapped[int]
    player_init: Mapped[Optional[int]]
    """
    Counts down from 1 billion, for minimal error. Whenever it hits 0, resets to 1 billion and Player's turn is taken.
    Works in same way for enemy. Increment of ticking down depends on speed stat.
    """

    enemy_hp: Mapped[int]
    enemy_init: Mapped[Optional[int]]
    enemy_speed: Mapped[int]
    enemy_defense: Mapped[int]
    enemy_value: Mapped[bytes]
    enemy_pool: Mapped[Optional[bytes]]
    enemy_spend: Mapped[bytes]



def getUser(session: Session, id: int) -> Player:
    """
    Retrieves a Player by ID

    Arguments:
     - session: request context
     - id: id of Player object

    Returns:
     - Player object with matching id
     - None if no matching id
    """

    return session.execute(select(Player).where(Player.id == id)).scalar()


def login(session: Session, username: str, password: str) -> Player:
    """
    Retrieves a Player by username and password, if any; if none, returns None.

    Arguments:
     - session: request context
     - username: username of Player
     - password: password of Player

    Returns:
     - Player object with matching username/password combo
     - None if no matching username or incorrect password
    """

    return session.execute(select(Player).where(Player.username == username, Player.password == password)).scalar()


def register(session: Session, username: str, password: str) -> Player:
    """
    Tries to create a new user account.

    Arguments:
     - username: username of new Player
     - password: password of new Player

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