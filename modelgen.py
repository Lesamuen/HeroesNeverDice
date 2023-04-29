from random import randint
from typing import Dict, Tuple

diceCosts = [2, 3, 4, 5, 6, 10]

def randItem(floor: int) -> Dict[str, int | bytes | str]:
    """
    Generates a random item.

    Arguments:
     - floor: floor of dungeon this item was found

    Returns:
     - Stats for item construction
    """

    itemStats = {}
    itemStats['iLvl'] = randint(floor * 10 - 5, floor * 10 + 5)
    itemStats['itemType'] = randint(0, 2)

    if itemStats['itemType'] == 0:
        # health average = 1/3 iLvl; base attack 2x cost of attack budget
        itemStats['attack'] = randint(0, itemStats['iLvl'] // 6) + 1
        diceBudget = itemStats['iLvl'] // 3 - itemStats['attack'] * 2
        dice = [1, 0, 0, 0, 0, 0]
        while diceBudget > 0:
            diceType = randint(0, 5)
            diceBudget -= diceCosts[diceType]
            dice[diceType] += 1
        # conv to byteform
        for i in range(6):
            dice[i] = dice[i].to_bytes(4)
        itemStats['dice_budget'] = dice[0] + dice[1] + dice[2] + dice[3] + dice[4] + dice[5]

        # if two-handed, base attack * 2.5
        if randint(0, 1):
            itemStats['twoh'] = True
            itemStats['name'] = "Lvl. " + str(itemStats['iLvl']) + " Greatsword"
            itemStats['attack'] = int(itemStats['attack'] * 2.5)
        else:
            itemStats['twoh'] = False
            itemStats['name'] = "Lvl. " + str(itemStats['iLvl']) + " Shortsword"
        
        return itemStats
    
    elif itemStats['itemType'] == 1:
        itemStats['name'] = "Lvl. " + str(itemStats['iLvl']) + " Shield"

        diceBudget = itemStats['iLvl'] // 5 - 2
        dice = [1, 0, 0, 0, 0, 0]
        while diceBudget > 0:
            diceType = randint(0, 5)
            diceBudget -= diceCosts[diceType]
            dice[diceType] += 1

        # conv to byteform
        for i in range(6):
            dice[i] = dice[i].to_bytes(4)
        itemStats['dice_budget'] = dice[0] + dice[1] + dice[2] + dice[3] + dice[4] + dice[5]

        return itemStats

    elif itemStats['itemType'] == 2:
        itemStats['name'] = "Lvl. " + str(itemStats['iLvl']) + " Armor"

        healthWeight = randint(20, 100)
        defenseWeight = randint(20, 100)
        speedWeight = randint(20, 100)
        totalWeight = healthWeight + defenseWeight + speedWeight
        healthWeight /= totalWeight
        defenseWeight /= totalWeight
        speedWeight /= totalWeight

        statBudget = randint(int(itemStats['iLvl'] * 0.8), int(itemStats['iLvl'] / 1.2)) + 10
        itemStats['health'] = int(statBudget * healthWeight)
        itemStats['defense'] = int(statBudget * defenseWeight)
        itemStats['speed'] = int(statBudget * speedWeight)

        return itemStats
    
def randFloor() -> Tuple[bytes, int]:
    """
    Generates a 10x10 map of floors.

    Returns:
     - bytemap of floor contents
     - initial position of player, packed into first byte
    """

    # decide side of entrance/exit; opposite sides two lines
    side = randint(1, 4)
    if side == 1:
        entrance = (randint(0, 1), randint(0, 9))
        exit = (randint(8, 9), randint(0, 9))
    elif side == 2:
        entrance = (randint(0, 9), randint(8, 9))
        exit = (randint(0, 9), randint(0, 1))
    elif side == 3:
        entrance = (randint(8, 9), randint(0, 9))
        exit = (randint(0, 1), randint(0, 9))
    elif side == 4:
        entrance = (randint(0, 9), randint(0, 1))
        exit = (randint(0, 9), randint(8, 9))

    # boss in center 4x4
    boss = (randint(3, 6), randint(3, 6))

    floor = bytes()
    for i in range(10):
        for j in range(10):
            if i == boss[0] and j == boss[1]:
                floor += bytes(3)
                continue
            if i == entrance[0] and j == entrance[1]:
                floor += bytes(4 + 64) #explored bit
                continue
            if i == exit[0] and j == exit[1]:
                floor += bytes(5)
                continue
            floorResult = randint(1, 100)
            if floorResult <= 50:
                floor += bytes(0)
            elif floorResult > 80:
                floor += bytes(1)
            else:
                floor += bytes(2)

    initpos = entrance[0] + (entrance[1] << 4)
    
    return (floor, initpos)

