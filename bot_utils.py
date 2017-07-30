"""Library of generic functions to make writing AI players easier.

Feel free to add to this file.  If a function is so specific that only one bot
will use it, however, then it doesn't belong here."""

from bl_classes import * # Need to import?  Do it in bl_classes.py.

def possible_straights(cards, formationSize=FORMATION_SIZE):
    """Return a seq of conceivable straight continuations."""
    minVal, maxVal = int(TROOP_CONTENTS[0]), int(TROOP_CONTENTS[-1])
    allStraights = [range(i, i + formationSize)
                    for i in range(minVal, maxVal - formationSize + 2)]

    cardValues = [int(card[0]) for card in cards]

    out = []
    for straight in allStraights:
        for value in cardValues:
            if value not in straight:
                break
        else:
            possibleStraight = list(straight)
            for value in set(cardValues): # Skip already played cards.
                possibleStraight.remove(value)
            out.append(list(map(str, possibleStraight)))

    return list(reversed(out)) # Strongest first

def check_formation_components(cards, formationSize=FORMATION_SIZE):
    """Return whether the cards are on track for a straight/triple/flush."""
    straight, triple, flush = False, False, False

    l = len(cards)
    if l > 1:
        values, suits = [c[0] for c in cards], [c[1] for c in cards]
        values.sort()

        spacing = [int(values[i+1]) - int(values[i]) for i in range(l-1)]
        if spacing.count(0) == l-1:
            triple = True
        elif 0 not in spacing and sum(spacing) <= formationSize - 1:
            straight = True

        if suits.count(suits[0]) == l:
            flush = True

        return straight, triple, flush

    else: # With 0 or 1 cards played, all formations are still conceivable.
        return True, True, True

def card_options(card):
    """Specify which values a wild tactics card can assume."""
    if card == 'Al' or card == 'Da':
        numbers = TROOP_CONTENTS
    elif card == 'Sh':
        numbers = [0, 1, 2]
    elif card == 'Co':
        numbers = [7]
    else:
        return [card] # Not a wild tactics card
    return [str(number) + suit for number in numbers for suit in TROOP_SUITS]

def detect_formation(cards):
    """Return the strongest formation a complete set of cards achieves.
    
    A formation is stored in a dict keyed as follows.
      'cards' (list): Cards that make up the formation
      'type' (str): 'straight flush', 'triple', 'flush', 'straight', or 'sum'
      'strength' (float): Normally an int (simply the sum of the cards' values)
                          but can be adjusted by EPSILON to break a tie.
    """
    l = len(cards)
    assert FORMATION_SIZE <= l <= FORMATION_SIZE + 1 # Allow for Mud.

    cardOptions = list(itertools.product(*[card_options(c) for c in cards]))
    if len(cardOptions) == 1:
        return detect_formation_no_wilds(cards)
    else:
        formations = list(map(detect_formation_no_wilds, cardOptions))
        bestFormation = formations[0]
        for formation in formations[1:]:
            if compare_formations([formation, bestFormation], 0) == 0:
                bestFormation = formation
        return bestFormation

def detect_formation_no_wilds(cards):
    """Same as detect_formation, but assumes no wild tactics present."""
    straight, triple, flush = check_formation_components(cards, len(cards))

    if straight and flush:
        fType = 'straight flush'
    elif triple:
        fType = 'triple'
    elif flush:
        fType = 'flush'
    elif straight:
        fType = 'straight'
    else:
        fType = 'sum'

    return {'cards':cards,
            'type':fType,
            'strength':sum([int(c[0]) for c in cards])}

def compare_formations(formations, whoseTurn):
    """Return the player whose formation is stronger.  Account for ties."""
    ranks = [POKER_HIERARCHY.index(f['type']) for f in formations]
    if ranks[0] != ranks[1]:
        return ranks.index(min(ranks))
    else: # Same formation type
        strengths = [f['strength'] for f in formations]
        if strengths[0] != strengths[1]:
            return strengths.index(max(strengths))
        else: # Identical formations, but current player finished 2nd
            return 1 - whoseTurn

def is_playable(r, tacticsCard):
    """Return whether the current player can play this tactics card.

	Does not consider tactics advantage.
    """
    if tacticsCard in ('Fo', 'Mu'):
        return True

    if tacticsCard == 'Sc':
        return len(r.decks['troop']) + len(r.decks['tactics']) >= 3

    if tacticsCard in ('Al', 'Da'):
        if r.playedLeader == r.whoseTurn:
            return False

    me = r.whoseTurn
    myEmpty = [i for i, f in enumerate(r.flags)
               if f.winner == None and len(f.played[me]) < 3]

    if tacticsCard in ('Al', 'Da', 'Sh', 'Co'):
        return myEmpty != []

    yourFull = [i for i, f in enumerate(r.flags)
                if f.winner == None and len(f.played[1 - me]) > 0]
    yourTroops = [card for flag in yourFull
                     for card in r.flags[flag].played[1 - me]
                         if card not in TACTICS]

    if tacticsCard == 'De':
        return yourFull != []

    if tacticsCard == 'Tr':
        return yourTroops != [] and myEmpty != []

    myFull = [i for i, f in enumerate(r.flags)
              if f.winner == None and len(f.played[me]) > 0]

    if tacticsCard == 'Re':
        return myFull != []
