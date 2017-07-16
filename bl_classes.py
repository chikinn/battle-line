"""Low-level classes for tracking state of a Battle Line round.

Intended to be imported by a higher-level game manager (play_bl).  The meat of
this file is the Round class, which stores all of the game info, along with
the nested Hand class, which stores player-specific info.
"""

N_PLAYERS        = 2
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

from bot_utils import *
import random, sys, copy


class Player():
    """Class to inherit when making a new AI player."""
    def __init__(self, p, verbosity):
        super(Player, self).__init__()

    @classmethod
    def get_name(cls):
        """Override to tell the framework your player's name."""
        raise Exception('Must override this method')

    def play(self, r):
        """Override to interact with the framework on your player's turn."""
        raise Exception('Must override this method')

class Round():
    """Store round info and interact with AI players.

    Methods that interact with AIs: 'get_play', 'get_scout_discards'.
    """

    def __init__(self, players, names, verbosity):
        """Instantiate a Round and its Flag and Hand sub-objects."""
        initialBest = detect_formation(
                 [v+TROOP_SUITS[0] for v in TROOP_CONTENTS[-3:]]) # Red 7, 8, 9
        self.best = initialBest # Best formation reachable at an empty flag
        self.flags = [self.Flag(initialBest) for i in range(N_FLAGS)]

        self.h = [self.Hand(i, names[i]) for i in range(N_PLAYERS)]

        self.tacticsAdvantage = None
        self.winner = None
        self.whoseTurn = 0
        self.verbosity = verbosity

    def generate_decks_and_deal_hands(self):
        """Construct decks, shuffle, and deal."""
        troopDeck = [n + s for n in TROOP_CONTENTS for s in TROOP_SUITS]
        tacticsDeck = [key for key in TACTICS]

        # Start tracking unplayed cards.
        self.cardsLeft = {'troop':troopDeck[:], 'tactics':tacticsDeck[:]}

        [random.shuffle(d) for d in (troopDeck, tacticsDeck)]
        self.decks = {'troop':troopDeck, 'tactics':tacticsDeck}

        [h.add(self.draw('troop')) for h in self.h for i in range(HAND_SIZE)]

    def draw(self, deckName):
        """Attempt to remove and return the top card of the deck."""
        if self.decks[deckName] == []: # Empty; draw from other deck.
            otherDeckName = [key for key in self.decks if key != deckName][0]
            return self.decks[otherDeckName].pop()
        return self.decks[deckName].pop()

    def replace_card(self, card, hand, deckName):
        """Discard from hand, then draw."""
        hand.drop(card)
        hand.add(self.draw(deckName))

    def update_tactics_advantage(self):
        p = self.whoseTurn
        assert self.tacticsAdvantage != p
        if self.tacticsAdvantage == None:
            self.tacticsAdvantage = 1 - p
        else:
            self.tacticsAdvantage = None

    def get_play(self, player):
        """Execute AI's play for current turn.  Return the play."""
        card, target, deckName = player.play(self)
        if card == None: # Player passed; do nothing.
            return

        if card in TACTICS:
            assert 'played at most one more than opponent' # Legal play
            self.cardsLeft['tactics'].remove(card)
            self.play_tactics(card, target)

        else: # Troop
            self.cardsLeft['troop'].remove(card)
            self.play_troop(card, target)

        self.replace_card(card, self.h[self.whoseTurn], deckName)
        return card, target, deckName

    def play_troop(self, card, target):
        p = self.whoseTurn
        flag = self.flags[target]

        formationSize = FORMATION_SIZE
        if flag.mud:
            formationSize += 1
        assert len(flag.played[p]) < formationSize # Legal play

        flag.played[p].append(card)

    def play_tactics(self, card, target):
        p = self.whoseTurn

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
                assert len(target) == 1
                targetCard, targetDestination = target[0], None
                startSide = 1 - p
            else: # Tr, Re
                assert (type(target), len(target)) == (tuple, 2)
                targetCard, targetDestination = target

                if card == 'Tr':
                    startSide, endSide = 1 - p, p
                else: # Re
                    startSide, endSide = p, p

            for f in self.flags:
                if targetCard in f.played[startSide]:
                    f.played[startSide].remove(targetCard)
                    break
            else:
                pass # Error -- target not found

            if targetDestination != None:
                f = self.flags[targetDestination]
                f.played[endSide].append(targetCard)

        elif card == 'Fo':
            self.flags[target].fog = True

        elif card == 'Mu':
            self.flags[target].mud = True

        else: # Al, Da, Co, or Sh
            if card in ('Al', 'Da'):
                assert 'not played other already' # Legal play
            self.play_troop(card, target) # Play like a troop.

    def available(self, card):
        """Return whether a card might still be available to draw and play."""
        return card in self.cardsLeft['troop'] + self.cardsLeft['tactics']
    
    def best_case(self, cards, formationSize=FORMATION_SIZE): ### TODO: tactics
        """Return the best possible continuation of a formation."""
        if len(cards) == formationSize:
            return detect_formation(cards)

        if cards == []:
            if formationSize == 3:
                return self.best
            else:
                pass ### TODO: Mud

        firstValue, firstSuit = cards[0]
        straight, triple, flush = check_formation_components(cards)

        if straight:
            possibleStraights = possible_straights(cards, formationSize)

            if flush:
                for s in possibleStraights:
                    for value in s:
                        card = value + firstSuit
                        if card not in self.cardsLeft['troop']:
                            break
                    else:
                        return detect_formation(cards +\
                                 [value + firstSuit for value in s])

        formation = copy.copy(cards)

        if triple:                               ###
            for card in self.cardsLeft['troop']: ### TODO: loop through suits
                if card[0] == firstValue:        ### instead, more efficiently.
                    formation += [card]          ###
                    if len(formation) == formationSize:
                        return detect_formation(formation)

        if flush: ### TODO: too similar to triple block above; consolidate?
            for value in TROOP_CONTENTS[::-1]:
                if value + firstSuit in self.cardsLeft['troop']:
                    formation.append(value + firstSuit)
                    if len(formation) == formationSize:
                        return detect_formation(formation)

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
                    return detect_formation(formation)

        # Sum
        cardsLeft = sorted(self.cardsLeft['troop'], reverse=True) # Desc.
        nEmptySlots = formationSize - len(cards)
        return detect_formation(cards + [cardsLeft[0]])

    def best_empty(self): ### TODO: Loop through best_case instead?
        """Find best formation (self.best) still playable at an empty flag."""
        oldBest = self.best # Exclude better formations from search.

        cardsLeft = sorted(self.cardsLeft['troop'], reverse=True) # Desc.
        for fType in POKER_HIERARCHY[POKER_HIERARCHY.index(oldBest['type']):]:
            if fType == 'sum':
                return self.best_case([cardsLeft[:FORMATION_SIZE]])
            
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

    def update_flag(self, flag, justPlayed):
        """Find the new best continuation at the flag, if necessary."""
        for player in range(N_PLAYERS):
            if (justPlayed in flag.best[player]['cards']) !=\
               (justPlayed in flag.played[player]):
                flag.best[player] = self.best_case(flag.played[player])

    def check_winner(self):
        flagOutcomes = [f.winner for f in self.flags]

        for player in range(N_PLAYERS):
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
            if flag.winner == 0:
                center = '{}     '.format(i)
                p0     = ' *    '
            elif flag.winner == 1:
                center = '{}     '.format(i)
                p1     = ' *    '
            lines[0]  += p0
            lines[5]  += center
            lines[10] += p1

            for p in range(N_PLAYERS):
                for j in range(3):
                    if p == 0:
                        iLine = 3 - j
                    else:
                        iLine = 7 + j

                    if j < len(flag.played[p]):
                        lines[iLine] += flag.played[p][j] + ' ' * 4
                    else:
                        lines[iLine] += ' ' * 6

        [print(line) for line in lines]
        print('-'*79)

    def get_scout_discards(self):
        pass


    class Flag():
        def __init__(self, initialBest):
            """Instantiate a Flag."""
            self.played = [[], []]
            self.best = [initialBest, initialBest]
            self.fog = False
            self.mud = False
            self.winner = None

        def try_to_resolve(self, whoseTurn):
            """Determine whether a flag is won, either normally or by proof."""
            if self.winner == None:
                formationSize = FORMATION_SIZE
                if self.mud:
                    formationSize += 1
    
                formations = copy.copy(self.played)
                finishedPlayers = [p for p in range(N_PLAYERS)
                                   if len(formations[p]) == formationSize]
                
                if len(finishedPlayers) == N_PLAYERS: # Both players ready 
                    self.winner = compare_formations\
                           (list(map(detect_formation, formations)), whoseTurn)
                elif len(finishedPlayers) == 1: # One attacker seeks a proof.
                    for p in range(N_PLAYERS):
                        if p not in finishedPlayers: # Defender
                            formations[p] = copy.copy(self.best[p])
                            # Tie goes to attacker since he finished first.
                            formations[p]['strength'] -= EPSILON
                            formations[1 - p] = detect_formation(formations[1 - p])
                            if compare_formations(formations, whoseTurn) == 1 - p:
                                self.winner = 1 - p # Attacker wins.


    class Hand():
        """Manage one player's hand of cards.

        cards (list of dict): One dict per card.  Keys:
          name (str): card name (e.g., '2r' is a red two)
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
