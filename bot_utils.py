"""Library of generic functions to make writing players easier.

Feel free to add to this file.  If a function is so specific that only one bot
will use it, however, then it doesn't belong here."""

from bl_classes import * # Need a package?  Import it in bl_classes.py.

@functools.lru_cache(maxsize=None)
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

@functools.lru_cache(maxsize=None)
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
    if card in ('Al', 'Da'):
        numbers = TROOP_CONTENTS
    elif card == 'Sh':
        numbers = [0, 1, 2]
    elif card == 'Co':
        numbers = [7]
    else:
        return [card] # Not a wild tactics card
    return [str(n) + suit for n in numbers for suit in TROOP_SUITS]

@functools.lru_cache(maxsize=None)
def detect_formation(cards, special=()):
    """Return the strongest formation a complete set of cards achieves.
    
    A formation is stored in a dict keyed as follows.
      'cards' (list): Cards that make up the formation
      'type' (str): 'straight flush', 'triple', 'flush', 'straight', or 'sum'
      'strength' (float): Three-digit int, where hundreds place indicates type
                          and remaining digits indicate sum of card values;
                          can be adjusted by EPSILON (float) to break a tie.
    """
    l = len(cards)
    assert FORMATION_SIZE <= l <= FORMATION_SIZE + 1 # Allow for Mud.

    cardOptions = list(itertools.product(*[card_options(c) for c in cards]))
    if len(cardOptions) == 1:
        return detect_formation_no_wilds(tuple(cards), tuple(special))
    else:
        formations = [detect_formation_no_wilds(tuple(c), tuple(special))
                      for c in cardOptions]
        bestFormation = formations[0]
        for formation in formations[1:]:
            if compare_formations([formation, bestFormation], 0) == 0:
                bestFormation = formation
        return bestFormation

@functools.lru_cache(maxsize=None)
def detect_formation_no_wilds(cards, special=()):
    """Same as detect_formation, but assumes no wild tactics present."""
    straight, triple, flush = check_formation_components(cards, len(cards))

    if 'fog' in special:
        fType = 'sum'
    elif straight and flush:
        fType = 'straight flush'
    elif triple:
        fType = 'triple'
    elif flush:
        fType = 'flush'
    elif straight:
        fType = 'straight'
    else:
        fType = 'sum'

    formationTypeStrength = 100 * POKER_HIERARCHY[::-1].index(fType)
    sumOfCardValues = sum([int(c[0]) for c in cards]) 

    return {'cards':cards,
            'type':fType,
            'strength':formationTypeStrength + sumOfCardValues}

def compare_formations(formations, whoseTurn):
    """Return the player whose formation is stronger.  Account for ties."""
    ranks = [POKER_HIERARCHY.index(f['type']) for f in formations]
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
    myEmpty = [i for i, f in enumerate(r.flags) if f.slots_left(me) > 0]
    if tacticsCard in ('Al', 'Da', 'Sh', 'Co'):
        return myEmpty != []

    yourFull = [i for i, f in enumerate(r.flags) if f.has_card(1-me)]
    if tacticsCard == 'De':
        return yourFull != []

    yourFullNonTactics = [i for i, f in enumerate(r.flags)
                          if f.has_card(1-me) and
                             False in [c in TACTICS for c in f.played[1-me]]]
    if tacticsCard == 'Tr':
        return yourFullNonTactics != [] and myEmpty != []

    myFull = [i for i, f in enumerate(r.flags) if f.has_card(me)]
    if tacticsCard == 'Re':
        return myFull != []

def find_play_to_win_flag(r, card, iFlag, p): # TODO: troop cards
    """Check whether this card can win this flag for the current player.  If
    not, returns None.  If so, returns the card's target (usually, this flag).

    Does not consider tactics advantage.
    """
    f = r.flags[iFlag]
    special = f.special
    if f.winner is not None:
        return None
    
    def check_scenario(adjustments):
        hands = [f.played[i].copy() for i in range(N_PLAYERS)]
        for a in adjustments:
            if a['type'] == 'add':
                hands[a['who']].append(a['card'])
            elif a['type'] == 'drop':
                hands[a['who']].remove(a['card'])
        formations = [r.best_case(hand, special) for hand in hands]
        return compare_formations(formations, p) == p
    
    if card in ('Al', 'Da', 'Sh', 'Co'):
        if f.slots_left(p) != 1:
            return None
        if check_scenario([{'type':'add', 'who':p, 'card':card}]):
            return iFlag
    
    if card == 'Re':
        # Removing a card can't win.  Adding a card from another flag can.
        if f.slots_left(p) != 1:
            return None
        for otherF in r.flags:
            if otherF == f or otherF.winner is not None:
                continue # Can't redeploy from this flag to itself.
            for myCard in otherF.played[p]:
                if check_scenario([{'type':'add', 'who':p, 'card':myCard}]):
                    return myCard, iFlag

    # Reuse this logic later for Traitor.
    def deserter_hurts_you(canTargetTactics=True):
        # My formation isn't ready yet, or flag is already won.
        if f.slots_left(p) != 0 or f.winner is not None:
            return None
        for yourCard in f.played[1-p]:
            if yourCard in TACTICS and not canTargetTactics:
                continue
            if check_scenario([{'type':'drop', 'who':1-p, 'card':yourCard}]):
                return yourCard,
        return None
    if card == 'De':
        return deserter_hurts_you()
    
    if card == 'Tr':
        def traitor_hurts_you():
            """Target a card "you" need.  Like Deserter but can't hit Tactics.
            """
            deserterHurtsYou = deserter_hurts_you(canTargetTactics=False)
            if deserterHurtsYou is not None:
                yourCard = deserterHurtsYou[0]
                # Find a slot at any flag for the card I'll steal from you.
                for i, fl in enumerate(r.flags):
                    if fl.slots_left(p) > 0:
                        return yourCard, i
            return None
        
        def traitor_helps_me():
            """Target a card "I" need.  A bit like Redeploy but can't hit
            Tactics.

            Also covers the case where stealing both hurts you and help me.
            """
            if f.slots_left(p) != 1: # I have no room for your card here.
                return None
            for otherF in r.flags:
                if otherF.winner is not None:
                    continue
                for yourCard in otherF.played[1-p]:
                    if yourCard in TACTICS:
                        continue
                    adjs = [{'type':'add', 'who':p, 'card':yourCard}]
                    if otherF == f:
                        adjs.append({'type':'drop', 'who':1-p, 'card':yourCard})
                    if check_scenario(adjs):
                        return yourCard, iFlag
            return None

        def first_not_none(lst):
            for x in lst:
                if x is not None:
                    return x
            return None
        
        return first_not_none([traitor_hurts_you(), traitor_helps_me()])
    
    if card == 'Fo':
        if f.slots_left(p) != 0 or f.winner is not None:
            return None
        special = tuple(list(special) + ['fog'])
        if check_scenario([]): # No adjustments to formations needed
            return iFlag
    
    return None # Mud and Scout never immediately win a flag.

def flag_wins_game(r, iFlag, p):
    oldWinner = r.flags[iFlag].winner
    r.flags[iFlag].winner = p # Change game to hypothetical state.
    out = r.check_winner() == p
    r.flags[iFlag].winner = oldWinner # Reset game state.
    return out
