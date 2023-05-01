from random import randint
from typing import Dict, Tuple

diceCosts = (2, 3, 4, 5, 6, 10)
diceVals = (4, 6, 8, 10, 12, 20)

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

        statBudget = randint(int(itemStats['iLvl'] * 0.8), int(itemStats['iLvl'] * 1.2)) + 10
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

    floor = bytearray()
    for i in range(10):
        for j in range(10):
            if i == boss[0] and j == boss[1]:
                floor.append(3)
                continue
            if i == entrance[0] and j == entrance[1]:
                floor.append(4 + 64) #explored bit
                continue
            if i == exit[0] and j == exit[1]:
                floor.append(5)
                continue
            floorResult = randint(1, 100)
            if floorResult <= 50:
                floor.append(0)
            elif floorResult > 80:
                floor.append(1)
            else:
                floor.append(2)

    initpos = entrance[0] + (entrance[1] << 4)
    
    return (floor, initpos)

def randEnemy(floor: int) -> Dict[str, int | bytes | str]:
    """
    Generates a random enemy.

    Arguments:
     - floor: floor of dungeon the enemy is from

    Returns:
     - Stats for battle construction
    """

    iLvl = randint(floor * 10 - 9, floor * 10 + 5)

    enemyStats = {}
    enemyStats['enemy_name'] = "Lvl. " + str(iLvl) + " Goon"

    # Decide base stats
    healthWeight = randint(20, 100)
    defenseWeight = randint(0, 50)
    speedWeight = randint(20, 100)
    totalWeight = healthWeight + defenseWeight + speedWeight
    healthWeight /= totalWeight
    defenseWeight /= totalWeight
    speedWeight /= totalWeight

    statBudget = randint(int(iLvl * 0.9), int(iLvl * 1.1)) + 10
    enemyStats['enemy_hp'] = int(statBudget * healthWeight)
    enemyStats['enemy_defense'] = int(statBudget * defenseWeight)
    enemyStats['enemy_speed'] = int(statBudget * speedWeight)
    
    diceBudget = iLvl
    dice = [0, 0, 0, 0, 0, 0]
    while diceBudget > 0:
        diceType = randint(0, 5)
        diceBudget -= diceCosts[diceType]
        dice[diceType] += 1
    # conv to byteform
    for i in range(6):
        dice[i] = dice[i].to_bytes(4)
    enemyStats['enemy_value'] = dice[0] + dice[1] + dice[2] + dice[3] + dice[4] + dice[5]
    enemyStats['enemy_pool'] = enemyStats['enemy_value']
    
    diceBudget = iLvl // 4
    dice = [1, 1, 1, 1, 1, 1]
    while diceBudget > 0:
        diceType = randint(0, 5)
        diceBudget -= diceCosts[diceType]
        dice[diceType] += 1
    # conv to byteform
    for i in range(6):
        dice[i] = dice[i].to_bytes(4)
    enemyStats['enemy_spend'] = dice[0] + dice[1] + dice[2] + dice[3] + dice[4] + dice[5]

    return enemyStats

def initiative(playerSpeed: int, enemySpeed: int) -> bool:
    """
    Rolls initiative for first turn in a battle.

    Arguments:
     - playerSpeed: speed stat of the player
     - enemySpeed: speed stat of the enemy

    Returns:
     - True if player goes first
     - False if enemy goes first
    """

    return (randint(1, playerSpeed) >= randint(1, enemySpeed))

def runAway(escapeSpeed: int, chaseSpeed: int) -> Tuple[bool, str]:
    """
    Attempts a retreat check. Rolls d4 per speed point, and if escape is higher, then successful.

    Arguments:
     - escapeSpeed: speed of the entity running away
     - chaseSpeed: speed of the entity opposing this check
    
    Returns:
     - Bool whether successful
     - Combat log
    """

    escapeCheck = 0
    for i in range(escapeSpeed):
        escapeCheck += randint(1, 4)
        
    chaseCheck = 0
    for i in range(chaseSpeed):
        chaseCheck += randint(1, 4)

    log = str(escapeSpeed) + "d4 (" + str(escapeCheck) + ") vs. " + str(chaseSpeed) + "d4 (" + str(chaseCheck) + ")"
    return (escapeCheck > chaseCheck, log)

def enemyDefense(pool: Tuple[int, int, int, int, int, int], spend: Tuple[int, int, int, int, int, int]) -> Tuple[bool] | Tuple[bool, str, int, Tuple[int, int, int, int, int, int]]:
    """
    Decides whether an enemy defends; 50% chance.
    If so, spends dice to increase temp defense points, which resets on next enemy turn

    Arguments:
     - pool: parsed dice of enemy held
     - spend: parsed dice enemy tries to spend

    Returns:
     - False if doesn't defend
     - True, combat log, defense roll result, and new pool if does defend
    """

    # check if defending
    if randint(0, 1):
        actualSpent = []
        pool = list(pool)
        for i in range(6):
            # spend up to max
            actualSpent.append(pool[i] if pool[i] < spend[i] else spend[i])
            pool[i] -= actualSpent[i]

        log = ""
        total = 0
        for i in range(6):
            if actualSpent[i] == 0:
                continue
            if len(log) > 0:
                log += ' + '
            result = 0
            for j in range(actualSpent[i]):
                result += randint(1, diceVals[i])
            log += str(actualSpent[i]) + 'd' + str(diceVals[i]) + '(' + str(result) + ')'
            total += result
        
        log += ' = ' + str(total)

        return (True, log, total, tuple(pool))
    else:
        return (False,)

def enemyAttack(pool: Tuple[int, int, int, int, int, int], spend: Tuple[int, int, int, int, int, int]) -> Tuple[str, int, Tuple[int, int, int, int, int, int]]:
    """
    Spends dice to do damage.

    Arguments:
     - pool: parsed dice of enemy held
     - spend: parsed dice enemy tries to spend

    Returns:
     - combat log, attack roll result, and new pool
    """

    actualSpent = []
    pool = list(pool)
    for i in range(6):
        # spend up to max
        actualSpent.append(pool[i] if pool[i] < spend[i] else spend[i])
        pool[i] -= actualSpent[i]

    log = ""
    total = 0
    for i in range(6):
        if actualSpent[i] == 0:
            continue
        if len(log) > 0:
            log += ' + '
        result = 0
        for j in range(actualSpent[i]):
            result += randint(1, diceVals[i])
        log += str(actualSpent[i]) + 'd' + str(diceVals[i]) + '(' + str(result) + ')'
        total += result
    
    log += ' = ' + str(total)

    return (log, total, tuple(pool))
