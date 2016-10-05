"""Low-level classes for tracking state of a Battle Line round.

Intended to be imported by a higher-level game manager (play_bl).  The meat of
this file is the Round class, which stores all of the game info, along with
the nested Hand class, which stores player-specific info.
"""

import random, sys, copy

N_FLAGS          = 9
STANDARD_WIN     = 5
BREAKTHROUGH_WIN = 3
FORMATION_SIZE   = 3
TROOP_SUITS      = 'roygbp'
TROOP_CONTENTS   = '0123456789' # 0 is lowest.
TACTICS          = {'Al':'Alexander',      'Co':'Companion Cavalry',
                    'Da':'Darius',         'De':'Deserter',
                    'Fo':'Fog',            'Mu':'Mud',
                    'Re':'Redeploy',       'Sc':'Scout',
                    'Sh':'Shield Bearers', 'Tr':'Traitor'}
HAND_SIZE        = 7
POKER_HIERARCHY  = ('straight flush', 'triple', 'flush', 'straight', 'sum')
EPSILON          = 0.1 # Arbitrary number on (0,1) to break formation ties

class Player(object):
    """Class that should be inherited from when making"""
    def __init__(self, me, verbosity):
        super(Player, self).__init__()

    @classmethod
    def get_name(cls):
        """Name to use when presenting this class to the user"""
        raise Exception('Override the function "get_name" in your class')

    def play(self, r):
        """Must be overridden to perform a play"""
        raise Exception("Must override this method")
        pass

class Round(object):
    """Store round info and interact with AI players.

    The only method that interacts with AIs is 'get_play'.

    gameType (str): How to treat rainbows ('rainbow', 'purple', 'vanlla').
    suits (str): Which suits are included for this game type.
    nPlayers (int)
    """

    def __init__(self, players, names, verbosity):
        """Instantiate a Round and its Hand sub-objects."""
        self.nPlayers = len(names)
        self.winner = None
        self.h = [self.Hand(i, names[i]) for i in range(self.nPlayers)]

        initialBest = self.detect_formation(
                [v+TROOP_SUITS[0] for v in TROOP_CONTENTS[-3:]]) # Red 7, 8, 9
        self.best = initialBest # Best formation reachable at an empty flag

        self.flags = [{'played':[[], []], ### TODO: turn flags into objects.
                       'best':[initialBest, initialBest],
                       'fog':False,
                       'mud':False,
                       'winner':None} for _ in range(N_FLAGS)]

        self.whoseTurn = 0

        self.verbosity = verbosity

    def generate_decks_and_deal_hands(self):
        """Construct decks, shuffle, and deal."""
        troopDeck = []
        for suit in TROOP_SUITS:
            for number in TROOP_CONTENTS:
                troopDeck.append(number + suit)
        tacticsDeck = [key for key in TACTICS]

        # Start tracking unplayed cards.
        self.cardsLeft = {'troop':troopDeck[:], 'tactics':tacticsDeck[:]}

        random.shuffle(troopDeck)
        random.shuffle(tacticsDeck)
        self.decks = {'troop':troopDeck, 'tactics':tacticsDeck}

        for hand in self.h:
            for i in range(HAND_SIZE):
                hand.add(self.draw('troop'))

    def draw(self, deckName):
        """Remove and return the top card of the deck."""
        return self.decks[deckName].pop()

    def replace_card(self, card, hand, deckName):
        # Discard card from hand, then attempt to draw a new card.
        """Drop the card and draw a new one."""
        if self.decks[deckName] != []:
            hand.drop(card)
            hand.add(self.draw(deckName))
            return True
        else:
            hand.drop(card)
            hand.add(self.draw('tactics'))
            return False # Deck is empty.

    def get_play(self, p):
        """Execute AI p's play for current turn.  Return the play."""
        card, target, deckName = p.play(self)
        if card == None: # Player passed; do nothing.
            return

        me = self.whoseTurn
        hand = self.h[me]

        if card in TACTICS:
            assert 'played at most one more than opponent' # Legal play
            self.cardsLeft['tactics'].remove(card)

            if card == 'Sc':
                assert (type(target), len(target)) == (tuple, 3) # Deck names
                for deckName in target:
                    hand.add(self.draw(deckName))

                discards = self.get_scout_discards(p)
                for discard in discards:
                    if discard in TACTICS:
                        deck = 'tactics'
                    else:
                        deck = 'troop'
                    self.decks['deck'].append(discard)
                    hand.drop(discard)
                return # Skip regular discard step.

            elif card in ('De', 'Tr', 'Re'):
                if card == 'De':
                    targetCard, targetDestination = target, None
                    startSide = 1 - me
                else: # Tr, Re
                    assert (type(target), len(target)) == (tuple, 2)
                    targetCard, targetDestination = target

                    if card == 'Tr':
                        startSide, endSide = 1 - me, me
                    else: # Re
                        startSide, endSide = me, me

                for f in self.flags:
                    if targetCard in f['played'][startSide]:
                        f['played'][1 - me].remove(targetCard)
                        break
                else:
                    pass # Error -- target not found

                if targetDestination != None:
                    f = self.flags[targetDestination]
                    f['played'].append(targetCard)

            elif card in ('Fo', 'Mu'):
                self.flags[target][TACTICS[card].lower()] = True

            else: # Al, Da, Co, or Sh
                if card in ('Al', 'Da'):
                    assert 'not played other already' # Legal play
                self.play_troop(card, target) # Play like a troop.

        else: # Troop
            self.cardsLeft['troop'].remove(card)
            self.play_troop(card, target)

        self.replace_card(card, hand, deckName)
        return card, target, deckName

    def play_troop(self, card, target):
        me = self.whoseTurn
        hand = self.h[me]
        flag = self.flags[target]

        formationSize = FORMATION_SIZE
        if flag['mud']:
            formationSize += 1

        assert len(flag['played'][me]) < formationSize # Legal play

        flag['played'][me].append(card)

    def check_formation_components(self, cards, formationSize=3):
        straight, triple, flush = False, False, False

        l = len(cards)
        if l > 1:
            values, suits = [c[0] for c in cards], [c[1] for c in cards]
            values.sort()

            spacing = [int(values[i+1]) - int(values[i]) for i in range(l-1)]
            if spacing.count(0) == l-1:
                triple = True
            elif sum(spacing) <= formationSize - 1:
                straight = True

            if suits.count(suits[0]) == l:
                flush = True

            return straight, triple, flush

        else: # All formations are still possible with one or no cards played.
            return True, True, True

    def detect_formation(self, cards): # Assume wilds pre-specified
        l = len(cards)
        assert 3 <= l <= 4 # Allow for Mud.

        straight, triple, flush = self.check_formation_components(cards)

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

    def possible_straights(self, cards, formationSize=3):
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

    def still_available(self, card):
        """Return whether a card might still be available to draw and play."""
        return True
    
    def best_case(self, cards, formationSize=3): ### TODO: tactics
        """Return the best possible continuation of a formation."""
        if len(cards) == formationSize:
            return self.detect_formation(cards)

        if cards == []:
            if formationSize == 3:
                return self.best
            else:
                pass ### TODO: Mud

        firstValue, firstSuit = cards[0]
        straight, triple, flush = self.check_formation_components(cards)

        if straight:
            possibleStraights = self.possible_straights(cards, formationSize)

        if straight and flush:
            for s in possibleStraights:
                for value in s:
                    card = value + firstSuit
                    if card not in self.cardsLeft['troop']:
                        break
                else:
                    return self.detect_formation(cards +\
                             [value + firstSuit for value in s])

        if triple:
            formation = copy.copy(cards)         ###
            for card in self.cardsLeft['troop']: ### TODO: loop through suits
                if card[0] == firstValue:        ### instead, more efficiently.
                    formation += [card]          ###
                    if len(formation) == formationSize:
                        return self.detect_formation(formation)

        if flush: ### TODO: too similar to triple block above; consolidate?
            formation = copy.copy(cards)
            for value in TROOP_CONTENTS[::-1]:
                if value + firstSuit in self.cardsLeft['troop']:
                    formation.append(value + firstSuit)
                    if len(formation) == formationSize:
                        return self.detect_formation(formation)

        if straight: ### TODO: optimize.
            for s in possibleStraights:
                formation = copy.copy(cards)
                for value in s:
                    for card in self.cardsLeft['troop']:
                        if card[0] == value: # Value is available.
                            formation.append(card)
                            break
                    else: # Value is not available.
                        break
                else: # All values are available.
                    return self.detect_formation(formation)

        # Sum
        cardsLeft = sorted(self.cardsLeft['troop'], reverse=True) # Desc.
        nEmptySlots = formationSize - len(cards)
        return self.detect_formation(cards + cardsLeft[:nEmptySlots])

    def best_empty(self):
        """Find best formation still playable at an empty flag (self.best)."""
        oldBest = self.best ### TODO: Exclude better formations from search.

        cardsLeft = sorted(self.cardsLeft['troop'], reverse=True) # Desc.
        for fType in POKER_HIERARCHY:
            if fType == 'sum':
                return self.best_case([cardsLeft[0]])
            
            if fType == 'flush':
                bestSoFar = {'strength':0}
                for card in cardsLeft:
                    self.cardsLeft.remove(card) # Card can't be played twice.
                    bestCase = self.best_case([card])
                    self.cardsLeft.append(card)
                    if bestCase['type'] == fType:
                        if bestCase['strength'] > bestSoFar['strength']:
                            bestSoFar = bestCase
                if bestSoFar['strength'] > 0:
                    return bestSoFar

            ### TODO: Don't double-check same-valued triples, straights.
            for card in cardsLeft:
                bestCase = self.best_case([card])
                if bestCase['type'] == fType:
                    return bestCase

    def compare_formations(self, formations):
        ranks = [POKER_HIERARCHY.index(f['type']) for f in formations]
        if ranks[0] != ranks[1]:
            return ranks.index(min(ranks))
        else: # Same formation type
            strengths = [f['strength'] for f in formations]
            if strengths[0] != strengths[1]:
                return strengths.index(max(strengths))
            else: # Identical formations
                # Tie breaks against current player, who finished later.
                return 1 - self.whoseTurn

    def update_flag(self, flag, justPlayed):
        """Find the new best continuation at the flag, if necessary."""
        for player in (0, 1):
            if (justPlayed in flag['best'][player]['cards']) !=\
               (justPlayed in flag['played'][player]):
                flag['best'][player] = self.best_case(flag['played'][player])

    def try_to_resolve_flag(self, flag):
        """Determine whether a flag is won, either normally or by proof."""
        if flag['winner'] == None:
            formationSize = FORMATION_SIZE
            if flag['mud']:
                formationSize += 1

            formations = copy.copy(flag['played'])
            finishedPlayers = []
            for player in (0, 1):
                if len(formations[player]) == formationSize:
                    finishedPlayers.append(player)
            
            if len(finishedPlayers) == 2: # Both players ready 
                flag['winner'] = self.compare_formations(list(map(self.detect_formation, formations)))
            elif len(finishedPlayers) == 1: # One attacker seeks a proof.
                for player in (0, 1):
                    if player not in finishedPlayers: # Defender
                        formations[player] = copy.copy(flag['best'][player])
                        # Tie goes to attacker since he finished first.
                        formations[player]['strength'] -= EPSILON
                        formations[1 - player] = self.detect_formation(formations[1 - player])
                        if self.compare_formations(formations) == 1 - player:
                            flag['winner'] = 1 - player # Attacker wins.

    def check_winner(self):
        flagOutcomes = [f['winner'] for f in self.flags]

        for player in (0, 1):
            if flagOutcomes.count(player) >= STANDARD_WIN:
                return player

        breakthroughStreak = 0
        streakHolder = None
        for i in range(N_FLAGS):
            if flagOutcomes[i] != None:
                if flagOutcomes[i] == streakHolder:
                    breakthroughStreak += 1
                    if breakthroughStreak == BREAKTHROUGH_WIN:
                        return streakHolder
                else:
                    streakHolder = flagOutcomes[i]
                    breakthroughStreak = 1
            else:
                breakthroughStreak = 0
                streakHolder = None

        return None

    def show_flags(self): ### TODO: account for Mud.
        padLength = 18
        lines = [' ' * padLength] * 11

        lines[3] = '  ' + self.h[0].name + ' ' * (18 - 2 - len(self.h[0].name))
        lines[7] = '  ' + self.h[1].name + ' ' * (18 - 2 - len(self.h[1].name))

        for i, flag in enumerate(self.flags):
            center = '{}*    '.format(i)
            p0, p1 = '      ', '      '
            if flag['winner'] == 0:
                center = '{}     '.format(i)
                p0     = ' *    '
            elif flag['winner'] == 1:
                center = '{}     '.format(i)
                p1     = ' *    '
            lines[0]  += p0
            lines[5]  += center
            lines[10] += p1

            for p in (0, 1):
                for j in range(3):
                    if p == 0:
                        iLine = 3 - j
                    else:
                        iLine = 7 + j

                    if j < len(flag['played'][p]):
                        lines[iLine] += flag['played'][p][j] + ' ' * 4
                    else:
                        lines[iLine] += ' ' * 6

        for line in lines:
            print(line)
        print()

    def get_scout_discards(self):
        pass


    class Hand(object):
        """Manage one player's hand of cards.

        cards (list of dict): One dict per card.  Keys:
          name (str): card name (e.g., '2?' is a rainbow two)
          time (int): turn number in which card was drawn
          direct (list of char): hint info that matches the card; can be either
            a color or a number; chronological; duplicates allowed
          indirect (list of char): same as direct but info does not match card
          known (bool): whether card can be deduced solely from public info
        seat (int): Player ID number (starting player is 0).
        """

        def __init__(self, seat, name):
            """Instantiate a Hand."""
            self.cards = []
            self.seat = seat
            self.name = name

        def show(self):
            """Print cards (verbose output only)."""
            print(self.name + ': ' + ' '.join(self.cards))
            return len(self.name + ': ')

        def add(self, newCard):
            """Add a card to the hand."""
            self.cards.append(newCard)

        def drop(self, card):
            """Discard a card from the hand."""
            self.cards.remove(card)
