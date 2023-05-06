from flask_login import UserMixin
from sqlalchemy import ForeignKey, select, insert, update, delete
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional, Tuple, Dict
from werkzeug.security import generate_password_hash, check_password_hash

from database import Base
import randomgen


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
     - get_user: gets a Player by their id
     - check_password: checks password
     - change_password: changes password
     - get_id: return id
     - get_dice: return currency as ints
     - split_dice: split currency into lower currency
     - fuse_dice: join currency into higher currency
     - get_health: health stat
     - get_speed: speed stat
     - get_defense: defense stat
     - get_attack: attack stat and attack dice max
     - get_active_defense: defense dice max
     - get_vault_item: get specific item from vault
     - get_inv_item: get specific item from inventory
     - get_listing: get specific listing on market this player owns
     - get_unequipped: get unequipped items in inventory
     - get_hands: get items equipped in hand slots
     - get_armor: get item equipped in armor slot
    """

    __tablename__ = "player"

    id: Mapped[int] = mapped_column(primary_key = True)
    username: Mapped[str] = mapped_column(unique = True)
    password: Mapped[str]
    
    # Currency
    dice: Mapped[bytes] = mapped_column(default = bytes([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]))
    split_conv = ((1,), (1, 1), (2, 1, 1), (2, 1, 1, 1), (3, 2, 1, 1, 1), (5, 3, 2, 2, 1, 1))

    # Items
    vault: Mapped[List["ItemVault"]] = relationship(back_populates = "owner")
    inventory: Mapped[List["ItemInv"]] = relationship(back_populates = "owner")
    listings: Mapped[List["ItemMarket"]] = relationship(back_populates = "owner")

    dungeon: Mapped[Optional["Dungeon"]] = relationship(back_populates = "player")
    """If null, then currently in home/base"""

    @staticmethod
    def get_user(session: Session, id: int) -> 'Player':
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

    def check_password(self, password: str) -> bool:
        """
        Checks the given password against this user.

        Arguments:
         - password: password to check
        
        Returns:
         - whether password is correct
        """

        return check_password_hash(self.password, password)

    def change_password(self, session: Session, newPassword: str) -> None:
        """
        Changes user's password to given one.

        Arguments:
         - session: request context
         - newPassword: new password to change to
        """

        self.password = generate_password_hash(newPassword)
        session.commit()

    def get_id(self):
        return str(self.id)
    
    # Currency methods
    def get_dice(self) -> Tuple[int]:
        """
        Returns currency as list of integers from d4 to d20
        """
        
        return dice_to_int(self.dice)

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

    # Stat queries
    def get_health(self, session: Session) -> int:
        """
        Gets player's health stat

        Arguments:
         - session: request context

        Returns:
         - health stat, base 10
        """

        armor = session.scalars(select(Item).join_from(ItemInv, Item).where(ItemInv.owner_id == self.id, ItemInv.equipped == True, Item.itemType == 2)).first()
        # Base hp: 10
        if armor:
            return 10 + armor.health
        else:
            return 10
        
    def get_speed(self, session: Session) -> int:
        """
        Gets player's speed stat

        Arguments:
         - session: request context

        Returns:
         - speed stat, base 1
        """

        armor = session.scalars(select(Item).join_from(ItemInv, Item).where(ItemInv.owner_id == self.id, ItemInv.equipped == True, Item.itemType == 2)).first()
        # Base speed: 1 (for very low possibility of going first; player goes first on ties)
        if armor:
            return 1 + armor.speed
        else:
            return 1
        
    def get_defense(self, session: Session) -> int:
        """
        Gets player's defense stat

        Arguments:
         - session: request context

        Returns:
         - defense stat, base 0
        """

        armor = session.scalars(select(Item).join_from(ItemInv, Item).where(ItemInv.owner_id == self.id, ItemInv.equipped == True, Item.itemType == 2)).first()
        # Base defense: 0
        if armor:
            return armor.defense
        else:
            return 0
        
    def get_attack(self, session: Session) -> Tuple[int, int, int, int, int, int, int]:
        """
        Gets player's attack capabilities; combines both hands if two one-hands

        Arguments:
         - session: request context

        Returns:
         - base attack, 6 attack dice max; base 0 + 1d4
        """

        weapons = session.scalars(select(Item).join_from(ItemInv, Item).where(ItemInv.owner_id == self.id, ItemInv.equipped == True, Item.itemType == 0)).all()
        if len(weapons) == 0:
            # Fists: 1d4
            return (0, 1, 0, 0, 0, 0, 0)
        
        attack = []
        weapon1 = weapons[0]
        attack.append(weapon1.attack)
        for i in range(6):
            attack.append(int.from_bytes(weapon1.dice_budget[i * 4 : (i + 1) * 4]))

        if len(weapons) == 2:
            weapon2 = weapons[1]
            attack[0] += weapon2.attack
            for i in range(6):
                attack[i + 1] += (int.from_bytes(weapon2.dice_budget[i * 4 : (i + 1) * 4]))

        return tuple(attack)
    
    def get_active_defense(self, session: Session) -> Tuple[int, int, int, int, int, int]:
        """
        Gets player's defense capabilities

        Arguments:
         - session: request context

        Returns:
         - 6 defense dice max; base 0
        """

        shield = session.scalars(select(Item).join_from(ItemInv, Item).where(ItemInv.owner_id == self.id, ItemInv.equipped == True, Item.itemType == 1)).first()

        if not shield:
            return (0, 0, 0, 0, 0, 0)
        else:
            defense = []
            for i in range(6):
                defense.append(int.from_bytes(shield.dice_budget[i * 4 : (i + 1) * 4]))
            return tuple(defense)

    # Inventory queries
    def get_vault_item(self, session: Session, id: int) -> 'ItemVault | None':
        """
        Retrieves a vault item by its id, if owned by player

        Arguments:
         - session: request context
         - id: id of item to retrieve

        Returns:
         - queried item
         - None if it doesn't exist or isn't owned by player
        """

        return session.execute(select(ItemVault).where(ItemVault.owner_id == self.id, ItemVault.item_id == id)).scalar()
    
    def get_inv_item(self, session: Session, id: int) -> 'ItemInv | None':
        """
        Retrieves an inventory item by its id, if owned by player

        Arguments:
         - session: request context
         - id: id of item to retrieve

        Returns:
         - queried item
         - None if it doesn't exist or isn't owned by player
        """

        return session.execute(select(ItemInv).where(ItemInv.owner_id == self.id, ItemInv.item_id == id)).scalar()
    
    def get_listing(self, session: Session, id: int) -> 'ItemMarket | None':
        """
        Retrieves a listing by its id, if owned by player

        Arguments:
         - session: request context
         - id: id of item to retrieve

        Returns:
         - queried item
         - None if it doesn't exist or isn't owned by player
        """

        return session.execute(select(ItemMarket).where(ItemMarket.owner_id == self.id, ItemMarket.item_id == id)).scalar()

    def get_unequipped(self) -> List["ItemInv"]:
        """
        Returns all unequipped items in inventory, sorted by index.
        """

        unequipped = []
        for item in self.inventory:
            if not item.equipped:
                unequipped.append(item)
        return unequipped

    def get_hands(self) -> Tuple["ItemInv | None", "ItemInv | None"]:
        """
        Returns items in hands. First hand always weapon (or none if nothing equipped). Second hand either second weapon, shield, or also first weapon if two-handed.
        """

        weapons = []
        shield = None
        for item in self.inventory:
            if item.equipped:
                if item.item.itemType == 0:
                    weapons.append(item)
                elif item.item.itemType == 1:
                    shield = item

        hands = []
        if len(weapons) > 0:
            hands.append(weapons[0])
        else:
            hands.append(None)
        if len(weapons) == 1 and weapons[0].item.twoh:
            hands.append(weapons[0])
        elif len(weapons) == 2:
            hands.append(weapons[1])
        elif shield:
            hands.append(shield)
        else:
            hands.append(None)

        return hands
    
    def get_armor(self) -> "ItemInv | None":
        """
        Returns armor equipped, or None if none equipped
        """

        for item in self.inventory:
            if item.equipped and item.item.itemType == 2:
                return item
            
        return None


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
     - gen: generate a random item into inventory
     - desc: return name + stats in string
    """

    __tablename__ = 'item'
    __mapper_args__ = {'polymorphic_on': 'itemType'}

    id: Mapped[int] = mapped_column(primary_key = True)

    # Type of item
    itemType: Mapped[int]
    name: Mapped[str]
    iLvl: Mapped[int]


    @staticmethod
    def gen(session: Session, floor: int, player: Player) -> "ItemInv":
        """
        Generates a random item, given an item floor, and player to attach to.

        Arguments:
         - session: request context
         - floor: the floor item was found on
         - player: reference to player to attach item to

        Returns:
         - Reference to created Item, attached to inventory by default
         - None if invalid floor
        """

        if floor < 1:
            return None
        generatedItem = randomgen.randItem(floor)
        if generatedItem['itemType'] == 0:
            generatedItem = session.execute(insert(ItemWeapon).values(**generatedItem).returning(ItemWeapon.id)).scalar()
        elif generatedItem['itemType'] == 1:
            generatedItem = session.execute(insert(ItemShield).values(**generatedItem).returning(ItemShield.id)).scalar()
        elif generatedItem['itemType'] == 2:
            generatedItem = session.execute(insert(ItemArmor).values(**generatedItem).returning(ItemArmor.id)).scalar()

        generatedItem = session.execute(insert(ItemInv).values(item_id = generatedItem, owner_id = player.id).returning(ItemInv)).scalar()
        session.commit()
        return generatedItem

    def desc(self) -> str:
        """
        Returns a human-readable description of the Item
        """
        return self.name + '\n\n'


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


    def desc(self) -> str:
        desc = super().desc()
        if self.twoh:
            desc += 'TWO-HANDED\n'
        else:
            desc += 'ONE-HANDED\n'
        desc += 'ATK: ' + str(self.attack) + ' + '
        desc += str(int.from_bytes(self.dice_budget[0:4])) + 'd4 + '
        desc += str(int.from_bytes(self.dice_budget[4:8])) + 'd6 + '
        desc += str(int.from_bytes(self.dice_budget[8:12])) + 'd8 + '
        desc += str(int.from_bytes(self.dice_budget[12:16])) + 'd10 + '
        desc += str(int.from_bytes(self.dice_budget[16:20])) + 'd12 + '
        desc += str(int.from_bytes(self.dice_budget[20:24])) + 'd20'

        return desc
    

class ItemShield(Item):
    """
    Shields are used to Defend. Always one-handed.

    Attributes:
     - dice_budget: max dice spent for defense
    """

    __mapper_args__ = {'polymorphic_identity': 1}

    dice_budget: Mapped[bytes] = mapped_column(nullable = True, use_existing_column = True)


    def desc(self) -> str:
        desc = super().desc()
        desc += 'DEF: '
        desc += str(int.from_bytes(self.dice_budget[0:4])) + 'd4 + '
        desc += str(int.from_bytes(self.dice_budget[4:8])) + 'd6 + '
        desc += str(int.from_bytes(self.dice_budget[8:12])) + 'd8 + '
        desc += str(int.from_bytes(self.dice_budget[12:16])) + 'd10 + '
        desc += str(int.from_bytes(self.dice_budget[16:20])) + 'd12 + '
        desc += str(int.from_bytes(self.dice_budget[20:24])) + 'd20'

        return desc
    

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


    def desc(self) -> str:
        desc = super().desc()
        desc += 'HP: ' + str(self.health) + '\n'
        desc += 'DEF: ' + str(self.defense) + '\n'
        desc += 'SPD: ' + str(self.speed)

        return desc


class ItemVault(Base):
    """
    Represents an Item in a Player's vault; cannot be lost unless sold or deliberately deleted.

    Arguments:
     - item_id: id of the Item
     - item: reference to the Item
     - owner_id: id of the Item's owner
     - owner: reference to Player that owns this Item

    Methods:
     - move_inv: move item from vault to inventory
     - list: put item from vault on market with price
    """

    __tablename__ = "vault"

    item_id: Mapped[int] = mapped_column(ForeignKey("item.id"), primary_key = True)
    item: Mapped["Item"] = relationship()

    owner_id: Mapped[int] = mapped_column(ForeignKey("player.id"))
    owner: Mapped["Player"] = relationship(back_populates = "vault")


    def move_inv(self, session: Session) -> None:
        """
        Moves this item from vault to player's inv
        
        Arguments:
         - session: request context
        """

        session.execute(insert(ItemInv).values(item_id = self.item_id, owner_id = self.owner_id))
        session.execute(delete(ItemVault).where(ItemVault.item_id == self.item_id))
        session.commit()

    def list(self, session: Session, price: int) -> None:
        """
        Moves this item from vault to player market, and set a price in terms of d4s
        
        Arguments:
         - session: request context
        """

        session.execute(insert(ItemVault).values(item_id = self.item_id, owner_id = self.owner_id, price = price))
        session.execute(delete(ItemMarket).where(ItemMarket.item_id == self.item_id))
        session.commit()
    

class ItemInv(Base):
    """
    Represents an Item in a Player's inventory; lost upon death, and moved to vault when leaving dungeon

    Arguments:
     - item_id: id of the Item
     - item: reference to the Item
     - owner_id: id of the Item's owner
     - owner: reference to Player that owns this Item
     - equipped: whether owner is actively using this Item

    Methods:
     - move_vault: move item from inventory to vault
     - drop: destroy item
     - equip: equip item, replacing others
     - unequip: unequip item if equipped
    """

    __tablename__ = "inventory"

    item_id: Mapped[int] = mapped_column(ForeignKey("item.id"), primary_key = True)
    item: Mapped["Item"] = relationship()

    owner_id: Mapped[int] = mapped_column(ForeignKey("player.id"))
    owner: Mapped["Player"] = relationship(back_populates = "inventory")
    
    equipped: Mapped[bool] = mapped_column(default = False)


    def move_vault(self, session: Session) -> None:
        """
        Moves this item from inventory to player's vault
        
        Arguments:
         - session: request context
        """

        session.execute(insert(ItemVault).values(item_id = self.item_id, owner_id = self.owner_id))
        session.execute(delete(ItemInv).where(ItemInv.item_id == self.item_id))
        session.commit()

    def drop(self, session: Session) -> None:
        """
        Destroys this item from inventory, whether by manual dropping or dropping upon death.
        
        Arguments:
         - session: request context
        """

        itemDropped = self.item_id
        session.execute(delete(ItemInv).where(ItemInv.item_id == itemDropped))
        session.execute(delete(Item).where(Item.id == itemDropped))
        session.commit()

    def equip(self, session: Session) -> None:
        """
        Tries to equip this item.

        If armor, just replaces armor.
        If weapon, tries to replace main hand. If one-handed, then tries off-hand if main hand full.
        If shield, tries to replace off-hand.

        Arguments:
         - session: request context
        """

        if self.equipped:
            return
        
        # unequip
        if self.item.itemType == 0:
            # weapons
            equipped = self.owner.get_hands()
            if self.item.twoh:
                if equipped[0]:
                    equipped[0].equipped = False
                if equipped[1]:
                    equipped[1].equipped = False
            else:
                if equipped[0] and equipped[1]:
                    equipped[1].equipped = False
        elif self.item.itemType == 1:
            # shield
            equipped = self.owner.get_hands()
            if equipped[1]:
                equipped[1].equipped = False
        elif self.item.itemType == 2:
            equipped = self.owner.get_armor()
            if equipped:
                equipped.equipped = False
                
        self.equipped = True
        session.commit()

        
    def unequip(self, session: Session) -> None:
        """
        Tries to unequip this item.

        Arguments:
         - session: request context
        """
        if not self.equipped:
            return
        
        self.equipped = False
        session.commit()


class ItemMarket(Base):
    """
    Represents an Item listed by a Player on the Market; stays until taken off or another Player buys it.

    Arguments:
     - id: id of the listing
     - item_id: id of the Item
     - item: reference to the Item
     - owner_id: id of the Item's owner
     - owner: reference to Player that owns this Item
     - price: amount of d4s (matching fusing exchange rates) the owner has put the Item up for sale

    Methods:
     - get_listing: get a listing directly by its item id
     - unlist: take item off of market back into vault
     - buy: purchase an item
    """
    
    __tablename__ = "market"

    item_id: Mapped[int] = mapped_column(ForeignKey("item.id"))
    item: Mapped["Item"] = relationship()

    owner_id: Mapped[int] = mapped_column(ForeignKey("player.id"))
    owner: Mapped["Player"] = relationship(back_populates = "listings")

    price: Mapped[int]
    

    @staticmethod
    def get_listing(session: Session, id: int) -> 'ItemMarket | None':
        """
        Gets an ItemMarket by its id.

        Arguments:
         - session: request context
         - id: id of the item

        Returns:
         - the queried listing
         - None if doesn't exist
        """

        return session.execute(select(ItemMarket).where(ItemMarket.item_id == id)).scalar()

    def unlist(self, session: Session) -> None:
        """
        Moves this item from market to player's vault
        
        Arguments:
         - session: request context
        """

        session.execute(insert(ItemVault).values(item_id = self.item_id, owner_id = self.owner_id))
        session.execute(delete(ItemMarket).where(ItemMarket.item_id == self.item_id))
        session.commit()

    def buy(self, session: Session, customer: Player, paying: Tuple[int, int, int, int, int, int]) -> bool:
        """
        Given player attempts to buy an item using given currency.

        Arguments:
         - session: request context
         - customer: the player buying the item
         - paying: currency list of dice the customer wants to use to pay

        Returns:
         - true if successful transaction
         - false if customer and owner are the same
         - false if not enough currency
         - false if currency not enough to pay price
        """

        # owner check
        if customer is self.owner:
            return False

        # test if player even has enough currency
        customerCurrency = customer.get_dice()
        for i in range(6):
            if paying[i] > customerCurrency[i]:
                return False
        
        # test if currency is enough
        payingConv = 0
        for i in range(6):
            payingConv += paying[i] * Player.split_conv[i][0]
        if payingConv < self.price:
            return False
        
        # if overpaying, do nothing special because customer didn't do math lol
        # transfer dice from customer to owner, then transfer item from owner to customer's vault
        ownerCurrency = self.owner.get_dice()
        for i in range(6):
            customerCurrency[i] -= paying[i]
            ownerCurrency[i] += paying[i]
        customer.dice = ints_to_dice(customerCurrency)
        self.owner.dice = ints_to_dice(ownerCurrency)

        session.execute(insert(ItemVault).values(item_id = self.item_id, owner_id = customer.id))
        session.execute(delete(ItemMarket).where(ItemMarket.item_id == self.item_id))
        session.commit()

        return True


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
     - boss_defeated: whether boss is defeated and exit is unlocked
     - battle: if active battle, then reference to battle

    Methods:
     - new: initializes dungeon object at floor 1 for player
     - next: generates next floor
     - move: moves player in 4 cardinal directions
     - exit: moves player through entrance/exit
     - parse_map: returns player view as ints
    """

    __tablename__ = "dungeon"

    player_id: Mapped[int] = mapped_column(ForeignKey("player.id"), primary_key = True)
    player: Mapped["Player"] = relationship(back_populates = "dungeon")

    floor: Mapped[int] = mapped_column(default = 1)
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

    boss_defeated: Mapped[bool] = mapped_column(default = False)

    battle: Mapped[Optional["Battle"]] = relationship(back_populates = "dungeon")
    """If null, then not in battle."""


    @staticmethod
    def new(session: Session, player: Player) -> "Dungeon":
        """
        Generate a new dungeon (move into Dungeon from base)
        Aborts if dungeon already exists

        Arguments:
         - session: request context
         - player: player for which the dungeon is made

        Returns:
         - Current dungeon if already exists
         - New dungeon at floor 1
        """

        if player.dungeon:
            return player.dungeon

        floor = randomgen.randFloor()
        floor = session.execute(insert(Dungeon).values(player_id = player.id, floor_data = floor[0], position = floor[1]).returning(Dungeon)).scalar()
        session.commit()
        return floor
    
    def next(self, session: Session) -> None:
        """
        Goes to next floor of dungeon; generates new floor of higher level

        Arguments:
         - session: request context
        """

        floor = randomgen.randFloor()
        self.floor_data = floor[0]
        self.position = floor[1]
        self.floor += 1
        session.commit()

    def move(self, session: Session, direction: int) -> Tuple[int, str]:
        """
        Attempts to move the player in a direction, exploring tiles

        Arguments:
         - session: request context
         - direction: 0 up, 1 right, 2 down, 3 left

        Returns:
         - Success code, message
         - On success: 0, <exploration message>
         - On blocked movement: 1, <reason>
         - On invalid direction: 2, <reason>
        """

        if self.battle:
            return (1, "You cannot move; currently in a battle!")

        row = self.position & 15 #????xxxx
        col = self.position >> 4 #xxxx????

        if direction == 0:
            if row <= 0:
                return (1, "You cannot move there; out of bounds!")
            row -= 1
        elif direction == 1:
            if col >= 9:
                return (1, "You cannot move there; out of bounds!")
            col += 1
        elif direction == 2:
            if row >= 9:
                return (1, "You cannot move there; out of bounds!")
            row += 1
        elif direction == 3:
            if col <= 0:
                return (1, "You cannot move there; out of bounds!")
            col -= 1
        else:
            return (2, "Invalid direction!")

        newRoom = self.floor_data[row * 10 + col]
        # Test blocking tile
        if (newRoom & 128): #10000000
            return (1, "You cannot move there; the doors to that room have sealed themselves!")
        
        # If already explored, nothing happens
        if (newRoom & 64): #01000000
            self.position = row + (col << 4)
            session.commit()
            return (0, "You moved successfully.")
        
        newRoomType = newRoom & 63 #00111111
        if newRoomType == 0:
            # Empty
            self.position = row + (col << 4)
            editableFloor = bytearray(self.floor_data)
            editableFloor[row * 10 + col] = newRoom | 64 #01000000 set explored bit
            self.floor_data = editableFloor
            session.commit()
            return (0, "You found an empty room.")
        elif newRoomType == 1:
            # Item
            self.position = row + (col << 4)
            editableFloor = bytearray(self.floor_data)
            editableFloor[row * 10 + col] = newRoom | 64 #01000000 set explored bit
            self.floor_data = editableFloor
            session.commit()

            foundItem = Item.gen(session, self.floor, self.player)

            return (0, 'You found a ' + foundItem.item.name + '!')
        elif newRoomType == 2 or newRoomType == 3:
            # Monster/Boss
            if newRoomType == 2:
                log = "You have encountered a monster!"
                battle = Battle.start(session, self, False)
            else:
                log = "You have encountered the boss!"
                battle = Battle.start(session, self, True)

            log += "\nIt's a " + battle.enemy_name + "!"
            
            self.position = row + (col << 4)
            editableFloor = bytearray(self.floor_data)
            editableFloor[row * 10 + col] = newRoom | 64 #01000000 set explored bit
            self.floor_data = editableFloor
            session.commit()

            # Roll initiative
            if not randomgen.initiative(self.player.get_speed(session), battle.enemy_speed):
                log += "\n" + battle.tick_until_player()

            return (0, log)
        elif newRoomType == 5:
            # Exit
            self.position = row + (col << 4)
            editableFloor = bytearray(self.floor_data)
            editableFloor[row * 10 + col] = newRoom | 64 #01000000 set explored bit
            self.floor_data = editableFloor
            session.commit()
            return (0, "You have found the exit!")
        
    def exit(self, session: Session) -> Tuple[int, str]:
        """
        Attempts to go through an entrance or exit.

        Arguments:
         - session: request context

        Returns:
         - Success code, message
         - On success exit: 0, "You have safely returned to town!"
         - On success next floor: 1, "You have entered floor <floor>..."
         - Not on entrance/exit: 2, "You can't leave the floor out this way!"
         - Boss not defeated on exit: 3, "The exit seems to be sealed by a powerful force!"
        """

        row = self.position & 15 #????xxxx
        col = self.position >> 4 #xxxx????
        
        currRoom = self.floor_data[row * 10 + col]
        currRoomType = currRoom & 63 #00111111
        if currRoomType == 4:
            # exit dungeon
            session.execute(delete(Dungeon).where(Dungeon.player_id == self.player_id))
            session.commit()

            for item in session.scalars(select(ItemInv).where(ItemInv.owner_id == self.player_id, ItemInv.equipped == True)):
                item.move_vault()

            return (0, "You have safely returned to town!")
        elif currRoomType == 5:
            # next floor
            if self.boss_defeated:
                self.next()
                return (1, "You have entered floor " + str(self.floor) + "...")
            else:
                return (3, "The exit seems to be sealed by a powerful force!")
        else:
            return (2, "You can't leave the floor out this way!")

    def parse_map(self) -> List[List[int]]:
        """
        Returns dungeon data as player can view

        Returns:
         - list of rows of rooms; 0 = unexplored (fog of war), 1 = explored, 2 = blocked, 3 = entrance, 4 = exit, 5 = player
        """

        playeri = self.position & 15 #????xxxx
        playerj = self.position >> 4 #xxxx????

        parsed = []
        for i in range(10):
            parsed.append([])
            for j in range(10):
                if i == playeri and j == playerj:
                    parsed[i].append(5)
                    continue
                currRoom = self.floor_data[i * 10 + j]
                currRoomType = currRoom & 63 #00111111

                # room states
                if currRoom & 128: #10000000
                    parsed[i].append(2)
                    continue
                elif currRoom & 64: #01000000
                    # test entrance/exit
                    if currRoomType == 4:
                        parsed[i].append(3)
                        continue
                    elif currRoomType == 5:
                        parsed[i].append(4)
                        continue
                    else:
                        parsed[i].append(1)
                        continue
                else:
                    parsed[i].append(0)
                    continue

        return parsed


class Battle(Base):
    """
    Describes an active battle. Used for entered monster rooms. Includes data for active monster and stats.
    Because room disabled upon fleeing, only need one-to-one relationship.

    Attributes:
     - dungeon_id: id of Dungeon this battle belongs to
     - dungeon: reference to related Dungeon
     - player_hp: CURRENT hp of player
     - player_init: current turn tick for player
     - player_temp_defense: temporary defense points from Defend action
     - prev_pos: previous position of player, to move to if successful retreat
     - enemy_name: Name of enemy
     - enemy_hp: CURRENT hp of enemy
     - enemy_max_hp: MAX hp of enemy
     - enemy_init: current turn tick for enemy
     - enemy_speed: speed stat of enemy
     - enemy_defense: defense stat of enemy
     - enemy_temp_defense: temporary defense points from enemy's Defend action
     - enemy_value: starting dice pool, determines how much dice given to player upon defeat
     - enemy_pool: how much dice enemy has left; will try to flee when out
     - enemy_spend: how much dice the enemy tries to spend on attacking/defending every turn

    Methods:
     - start: initializes a battle object for a dungeon
     - tick_until_player: simulate battle until player turn
     - enemy_turn: simulate enemy taking a turn
    """

    __tablename__ = "battle"

    dungeon_id: Mapped[int] = mapped_column(ForeignKey("dungeon.player_id"), primary_key = True)
    dungeon: Mapped["Dungeon"] = relationship(back_populates = "battle")

    player_hp: Mapped[int]
    player_init: Mapped[int] = mapped_column(default = 1000000000)
    """
    Counts down from 1 billion, for minimal error. Whenever it hits 0, resets to 1 billion and Player's turn is taken.
    Works in same way for enemy. Increment of ticking down depends on speed stat.
    """
    player_temp_defense: Mapped[int] = mapped_column(default = 0)
    prev_pos: Mapped[int]

    boss: Mapped[bool]
    enemy_name: Mapped[str]
    enemy_hp: Mapped[int]
    enemy_max_hp: Mapped[int]
    enemy_init: Mapped[int] = mapped_column(default = 1000000000)
    enemy_speed: Mapped[int]
    enemy_defense: Mapped[int]
    enemy_temp_defense: Mapped[int] = mapped_column(default = 0)
    enemy_value: Mapped[bytes]
    enemy_pool: Mapped[Optional[bytes]]
    enemy_spend: Mapped[bytes]


    @staticmethod
    def start(session: Session, dungeon: Dungeon, boss: bool) -> "Battle":
        """
        Generates a battle object with enemy

        Arguments:
         - session: request context
         - dungeon: dungeon the battle is for
         - boss: whether or not the enemy is a boss

        Returns:
         - reference to generated Battle
        """

        generatedEnemy = randomgen.randEnemy(int(dungeon.floor * 1.2) + 1 if boss else dungeon.floor)
        generatedBattle = session.execute(insert(Battle).values(boss = boss, dungeon_id = dungeon.player_id, prev_pos = dungeon.position, player_hp = dungeon.player.get_health(session), **generatedEnemy).returning(Battle)).scalar()
        
        session.commit()
        return generatedBattle

    def tick_until_player(self, session: Session) -> str:
        """
        Simulates enemies until next player turn (player_init is 0)

        If death occurs, then death() called.

        Arguments:
         - session: request context
        
        Returns:
         - combat log
        """

        log = ""
        playerSpeed = self.dungeon.player.get_speed(session)
        while self.player_init > 0:
            if self.enemy_init <= 0:
                log += "\n" + self.enemy_name + "'s turn.\n" + self.enemy_turn(session)
                if self.player_hp <= 0 or self.enemy_init == 2000000000: #using impossible number to mark escape
                    break
                self.enemy_init += 1000000000

            playerTicks = self.player_init // playerSpeed + 1
            enemyTicks = self.enemy_init // self.enemy_speed + 1
            ticks = playerTicks if playerTicks > enemyTicks else enemyTicks
            self.player_init -= ticks * playerSpeed
            self.enemy_init -= ticks * self.enemy_speed

            if playerTicks == enemyTicks and self.enemy_init < self.player_init:
                # both go at same tick, but enemy go first
                log += "\n" + self.enemy_name + "'s turn.\n" + self.enemy_turn(session)
                if self.enemy_init == 2000000000: #using impossible number to mark escape
                    break
                self.enemy_init += 1000000000

        if self.player_hp <= 0:
            self.death()
            log += "\nYou have died! Your body and soul is whisked away, leaving your items behind..."
        elif self.enemy_init == 2000000000: #using impossible number to mark escape
            # just delete battle, no reward
            # boss escaping still unseals door
            if self.boss:
                self.dungeon.boss_defeated = True
                log += "The boss skulks away, and you can no longer feel their oppressive presence in the air..."
            else:
                log += "The enemy escapes out of sight, to recuperate and return another day."
            session.execute(delete(Battle).where(Battle.dungeon_id == self.dungeon_id))
        else:
            log += "\nPlayer's turn."
            # reset player temp defense upon start of next turn
            self.player_temp_defense = 0
        
        session.commit()

        return log

    def attack(self, session: Session, spend: Tuple[int, int, int, int, int, int]) -> str:
        """
        Player attack action. Instead of erroring, if amount spent is more than is possible from weapons, then it is simply limited by weapon amount.
        player_init reset to max.

        If enemy is dead, then battle ends and they drop their dice. If boss, then item dropped too and exit is unlocked.

        Arguments:
         - session: request context
         - spend: how much the player is trying to spend

        Returns:
         - combat log
        """

        log = "You strike at the " + self.enemy_name + "!"

        actualSpent = []
        playerAttack = self.dungeon.player.get_attack()
        for i in range(6):
            actualSpent.append(spend[i] if spend[i] <= playerAttack[i + 1] else playerAttack[i + 1])
        
        result = randomgen.spendDice(self.dungeon.player.get_dice())
        self.dungeon.player.dice = ints_to_dice(result[2])
        log += '\n' + result[1]

        # deal damage, mitigated by defense
        if result[0] <= self.enemy_temp_defense:
            log += '\nThe ' + self.enemy_name + ' fends off your blow!'
            self.enemy_temp_defense -= result[0]
        elif result[0] <= self.enemy_temp_defense + self.enemy_defense:
            log += '\nYour attack fails to penetrate the ' + self.enemy_name + "'s blow!"
            self.enemy_temp_defense = 0
        else:
            result[0] -= self.enemy_temp_defense + self.enemy_defense
            self.enemy_temp_defense = 0
            self.enemy_hp -= result[0]
            log += '\nYou deal ' + str(result[0]) + ' damage.'

        if self.enemy_hp <= 0:
            # enemy defeated
            if self.boss:
                self.dungeon.boss_defeated = True
                log += '\nYou have defeated the boss, a ' + self.enemy_name + '!'

                # currency
                currencyDrop = dice_to_int(self.enemy_value)
                currentCurrency = self.dungeon.player.get_dice()
                for i in range(6):
                    currentCurrency[i] += currencyDrop[i]
                self.dungeon.player.dice = ints_to_dice(currentCurrency)
                log += '\nIt dropped ' + str(currencyDrop[0]) + 'd4, ' + str(currencyDrop[1]) + 'd6, ' + str(currencyDrop[2]) + 'd8, ' + str(currencyDrop[3]) + 'd10, ' + str(currencyDrop[4]) + 'd12, and ' + str(currencyDrop[5]) + 'd20.'
                
                # item from 2 floors up
                itemDrop = Item.gen(session, self.dungeon.floor + 2, self.dungeon.player)
                log += '\nIt dropped a ' + itemDrop.item.name + '!'

                log += "\nThe floor's exit has been unlocked..."
            else:
                log += '\nYou have defeated a ' + self.enemy_name + '!'

                # currency
                currencyDrop = dice_to_int(self.enemy_value)
                currentCurrency = self.dungeon.player.get_dice()
                for i in range(6):
                    currentCurrency[i] += currencyDrop[i]
                self.dungeon.player.dice = ints_to_dice(currentCurrency)
                log += '\nIt dropped ' + str(currencyDrop[0]) + 'd4, ' + str(currencyDrop[1]) + 'd6, ' + str(currencyDrop[2]) + 'd8, ' + str(currencyDrop[3]) + 'd10, ' + str(currencyDrop[4]) + 'd12, and ' + str(currencyDrop[5]) + 'd20.'

            session.execute(delete(Battle).where(Battle.dungeon_id == self.dungeon_id))
            session.commit()
        else:
            # Simulate enemy turns until next player turn
            self.player_init = 1000000000
            log += '\n' + self.tick_until_player(session)

        return log

    def defense(self, session: Session, spend: Tuple[int, int, int, int, int, int]) -> str:
        """
        Player defense action. Instead of erroring, if amount spent is more than is possible from shield, then it is simply limited by shield amount.
        player_init reset to max.

        Arguments:
         - session: request context
         - spend: how much the player is trying to spend

        Returns:
         - combat log
        """

        log = "You raise your guard!"

        actualSpent = []
        playerDefense = self.dungeon.player.get_active_defense()
        for i in range(6):
            actualSpent.append(spend[i] if spend[i] <= playerDefense[i] else playerDefense[i])
        
        result = randomgen.spendDice(self.dungeon.player.get_dice())
        self.dungeon.player.dice = ints_to_dice(result[2])
        log += '\n' + result[1]
        self.player_temp_defense = result[0]

        # Simulate enemy turns until next player turn
        self.player_init = 1000000000
        log += '\n' + self.tick_until_player(session)

        return log

    def retreat(self, session: Session) -> str:
        """
        Player retreat action.
        If successful, battle ends, but player moved to previous room and room is blocked off.
        If failed, player_init reset to max

        Arguments:
         - session: request context

        Returns:
         - combat log
        """

        log = "You attempt to run away!"

        result = randomgen.runAway(self.dungeon.player.get_speed(), self.enemy_speed)
        log += '\n' + result[1]
        
        if result[0]:
            log += '\nSuccess! You retreat back the way you came...'

            # set blocked on this room
            row = self.dungeon.position & 15 #????xxxx
            col = self.dungeon.position >> 4 #xxxx????
            editableFloor = bytearray(self.dungeon.floor_data)
            editableFloor[row * 10 + col] = editableFloor[row * 10 + col] | 128 #10000000 set blocked bit
            self.dungeon.floor_data = editableFloor

            # return to prev pos
            self.dungeon.position = self.prev_pos
            
            session.execute(delete(Battle).where(Battle.dungeon_id == self.dungeon_id))
            session.commit()
        else:
            self.player_init = 1000000000
            log += "\nFailure!\n" + self.tick_until_player()

        return log

    def enemy_turn(self, session: Session) -> str:
        """
        Simulates enemy taking their turn.
        
        Arguments:
         - session: request context

        Returns:
         - combat log
        """

        log = ""

        # Reset enemy temp defense
        self.enemy_temp_defense = 0

        # Retrieve enemy dice pool
        currPool = dice_to_int(self.enemy_pool)

        # if fully empty, try to run away
        empty = True
        for i in currPool:
            if i > 0:
                empty = False
                break
        if empty:
            log += "Exhausted, the " + self.enemy_name + " is trying to get away...\n"
            result = randomgen.runAway(self.enemy_speed, self.dungeon.player.get_speed(session))
            log += result[1]
            if result[0]:
                log += "\n...and succeeded!"
                self.enemy_init = 2000000000
            else:
                log += "\n...but failed!"
            session.commit()
            return log
        
        # if below half health, 50% chance to defend instead of attack
        if self.enemy_hp <= self.enemy_max_hp // 2 and randomgen.enemyDefense():
            defense = randomgen.spendDice(currPool, dice_to_int(self.enemy_spend))
            if defense[0]:
                log += "Weary, the " + self.enemy_name + " tries to defend itself!\n" + defense[1]
                self.enemy_temp_defense = defense[0]
                self.enemy_pool = ints_to_dice(defense[2])
                session.commit()
                return log
            
        # otherwise, attack by default
        attack = randomgen.spendDice(currPool, dice_to_int(self.enemy_spend))
        log += "The " + self.enemy_name + " strikes you!\n" + attack[1]

        if self.player_temp_defense >= attack[0]:
            # player's defend action fully blocked attack
            self.player_temp_defense -= attack[0]
            log += "\nThe attack glances off your impeccable defense!"
        else:
            # mitigate with player defense
            mitigatedDamage = attack[0] - self.player_temp_defense - self.dungeon.player.get_defense()
            self.player_temp_defense = 0
            if mitigatedDamage <= 0:
                log += "\nThe attack fails to penetrate your armor!"
            else:
                log += "\nYou take " + str(mitigatedDamage) + " damage."
                self.player_hp -= mitigatedDamage

        self.enemy_pool = ints_to_dice(attack[2])
        session.commit()
        return log

    def death(self, session: Session) -> None:
        """
        Called upon player death.
        Battle and dungeon deleted. All items in inventory dropped.

        Arguments:
         - session: request context
        """

        # Drop all items
        for item in session.scalars(select(ItemInv).where(ItemInv.owner_id == self.id)).all():
            item.drop()

        # Delete dungeon
        session.execute(delete(Dungeon).where(Dungeon.player_id == self.dungeon_id))
        session.execute(delete(Battle).where(Battle.dungeon_id == self.dungeon_id))

        session.commit()



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

    user = session.execute(select(Player).where(Player.username == username)).scalar()
    if user and user.check_password(password):
        return user
    return None

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
        newUser = session.execute(insert(Player).values(username = username, password = generate_password_hash(password)).returning(Player)).scalar()
        session.commit()
    except IntegrityError:
        # If username already taken
        return None
    
    return newUser


def dice_to_int(dice: bytes) -> Tuple[int, int, int, int, int, int]:
    """
    Converts dice in byte array form into parsed integer form.

    Arguments:
     - dice: the dice in byte form to convert

    Returns:
     - tuple of all amounts of dice in integer form, from d4 to d20
    """

    dice_ints = []
    for i in range(6):
        dice_ints.append(int.from_bytes(dice[i * 4 : (i + 1) * 4]))

    return tuple(dice_ints)

def ints_to_dice(dice: Tuple[int, int, int, int, int, int]) -> bytes:
    """
    Converts dice in parsed integer form back to byte form for storage.

    Arguments:
     - dice: the dice in integer form to convert

    Returns:
     - byte data containing dice
    """

    return dice[0].to_bytes(4) + dice[1].to_bytes(4) + dice[2].to_bytes(4) + dice[3].to_bytes(4) + dice[4].to_bytes(4) + dice[5].to_bytes(4)
