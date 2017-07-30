"""Low-level classes for tracking state of a Battle Line round.

Intended to be imported by a higher-level game manager (play_bl).  The meat of
this file is the Round class, which stores all of the game info, along with the
nested Hand and Flag classes.
"""

N_PLAYERS        = 2
N_FLAGS          = 9
STANDARD_WIN     = 5
BREAKTHROUGH_WIN = 3
FORMATION_SIZE   = 3
HAND_SIZE        = 7
EPSILON          = 0.1 # Arbitrary number on (0,1) to break formation ties
POKER_HIERARCHY  = ('straight flush', 'triple', 'flush', 'straight', 'sum')
TROOP_SUITS      = 'roygbp'
TROOP_CONTENTS   = '0123456789' # 0 is lowest.
TACTICS          = {'Al':'Alexander',      'Co':'Companion Cavalry',
                    'Da':'Darius',         'De':'Deserter',
                    'Fo':'Fog',            'Mu':'Mud',
                    'Re':'Redeploy',       'Sc':'Scout',
                    'Sh':'Shield Bearers', 'Tr':'Traitor'}

import random, sys, copy, itertools
from bot_utils import *

class Player():
    """Class to inherit when making a new AI player.
    
    You may wish to use Random Player or Greedy Player as a guide.
    """

    def __init__(self, p):
        super(Player, self).__init__() # OK to override, but still call super.

    @classmethod
    def get_name(cls):
        """Override to tell the framework your player's name."""
        raise Exception('Must override this method')

    def play(self, r):
        """Override to submit a move on your player's turn.
        
        If playing a troop card, return a 3-tuple of the card name, the flag
        number where it should be played, and a deck to draw from.  Playing a
        tactics card is more complicated; see Round.play_tactics."""

        raise Exception('Must override this method')

    def scout_discards(self, r):
        """Override to return a list of two discards after playing Scout."""
        raise Exception('Must override this method')


class Round():
    """Store round info and interact with AI players.

    Methods that interact with AIs: 'get_play', 'get_scout_discards'

    Formation dicts are explained in 'detect_formation' (bot_utils.py).

    best & bestMud (dict): Best formation reachable at an empty flag
    flags (list of 9 Flag): See Flag class
    h (list of 2 Hand): See Hand class
    playedLeader (int or None): Who (player 0 or 1) played Alexander or Darius
    tacticsAdvantage (int or None): Who has played fewer tactics cards
    winner (int or None): Who won the round
    whoseTurn (int): Current player
    verbose (bool): Whether to print play-by-play output (or just state winner)
    cardsLeft (dict): Lists of cards publicly remaining in each deck
    decks (dict): Lists of ordered draw piles for each deck (don't cheat!)
    """

    def __init__(self, players, names, verbose):
        """Instantiate a Round and its Flag and Hand sub-objects."""
        initialBest = detect_formation(
                 [v+TROOP_SUITS[0] for v in TROOP_CONTENTS[-3:]]) # Red 7, 8, 9
        self.best = initialBest
        initialBestMud = detect_formation(
                 [v+TROOP_SUITS[0] for v in TROOP_CONTENTS[-4:]]) # Red 6-9
        self.bestMud = initialBestMud
        self.flags = [self.Flag(initialBest) for i in range(N_FLAGS)]

        self.h = [self.Hand(i, names[i]) for i in range(N_PLAYERS)]

        self.playedLeader = None
        self.tacticsAdvantage = None
        self.winner = None
        self.whoseTurn = 0
        self.verbose = verbose

    def generate_decks_and_deal_hands(self):
        """Construct decks, shuffle, and deal."""
        troopDeck = [n + s for n in TROOP_CONTENTS for s in TROOP_SUITS]
        tacticsDeck = [key for key in TACTICS]

        self.cardsLeft = {'troop':troopDeck[:], 'tactics':tacticsDeck[:]}

        [random.shuffle(d) for d in (troopDeck, tacticsDeck)]
        self.decks = {'troop':troopDeck, 'tactics':tacticsDeck}

        [h.add(self.draw('troop')) for h in self.h for i in range(HAND_SIZE)]

    def draw(self, deckName):
        """Attempt to remove and return the top card of a deck."""
        if deckName and self.decks[deckName] != []:
            return self.decks[deckName].pop()

    def replace_card(self, card, hand, deckName):
        """Discard from hand, then draw (if a deck is specified)."""
        hand.drop(card)
        
        draw = self.draw(deckName)
        if draw != None:
            hand.add(draw)

    def prefer_deck(self, deckName):
        """Return name of the passed deck, or if empty, of the other deck."""
        assert deckName in self.decks.keys()
        if len(self.decks[deckName]) > 0:
            return deckName
        else: # Other deck
            return [key for key in self.decks if key != deckName][0]

    def update_tactics_advantage(self):
        """When a tactics card is played, keep track of who has played more."""
        you = 1 - self.whoseTurn
        assert self.tacticsAdvantage != you # Check legality.
        if self.tacticsAdvantage == None:
            self.tacticsAdvantage = you
        else: # I had the advantage.
            self.tacticsAdvantage = None

    def get_play(self, player):
        """Execute AI's play for current turn.  Return the play."""
        me = self.whoseTurn
        card, target, deckName = player.play(self)

        if card == None: # Player passed; do nothing (TODO: check legality).
            return

        if card in TACTICS:
            self.cardsLeft['tactics'].remove(card)
            self.play_tactics(card, target)
            self.update_tactics_advantage()
        else: # Troop
            self.cardsLeft['troop'].remove(card)
            self.play_troop(card, target)

        if card == 'Sc':
            deckName = self.get_scout_discards(player) # 2-list
            self.replace_card(card, self.h[me], None)
        else: # Draw a new card as usual.
            self.replace_card(card, self.h[me], deckName)

        return card, target, deckName

    def get_scout_discards(self, player):
        """Process and return AI's discards (after Scout)."""
        discards = player.scout_discards(self)
        assert len(discards) == 2

        for card in discards:
            if card in TACTICS:
                deck = 'tactics'
            else:
                deck = 'troop'
            self.decks[deck].append(card)
            self.h[self.whoseTurn].drop(card)

        return discards

    def play_troop(self, card, target):
        me = self.whoseTurn
        flag = self.flags[target]

        assert flag.has_slot(me) # Legal play
        flag.played[me].append(card)

    def play_tactics(self, card, target):
        me = self.whoseTurn

        if card == 'Sc':
            assert (type(target), len(target)) == (tuple, 3) # Deck names
            for deckName in target:
                self.h[me].add(self.draw(self.prefer_deck(deckName)))

        elif card in ('De', 'Tr', 'Re'):
            if card == 'De':
                assert len(target) == 1
                targetCard, targetDestination = target[0], None
                startSide = 1 - me
            else: # Tr, Re
                assert (type(target), len(target)) == (tuple, 2)
                targetCard, targetDestination = target

                if card == 'Tr':
                    startSide, endSide = 1 - me, me
                else: # Re
                    startSide, endSide = me, me

            for f in self.flags:
                if targetCard in f.played[startSide]:
                    f.played[startSide].remove(targetCard)
                    self.update_flag(f, None, True)
                    break
            else:
                raise Exception('Target not found')

            if targetDestination != None:
                f = self.flags[targetDestination]
                self.update_flag(f, None, True)
                f.played[endSide].append(targetCard)

        elif card == 'Fo':
            self.flags[target].fog = True
            self.update_flag(self.flags[target], None, True)

        elif card == 'Mu':
            self.flags[target].mud = True
            self.update_flag(self.flags[target], None, True)

        else: # Al, Da, Co, or Sh
            if card in ('Al', 'Da'):
                assert self.playedLeader != me # Legal play
                self.playedLeader = me
            self.play_troop(card, target) # Play like a troop.

    def best_case(self, cards, special=[]):
        """Return the best formation attainable for a group of cards."""
        cardOptions = [list(tup) for tup in
            itertools.product(*[card_options(card) for card in cards])
        ]
        if len(cardOptions) == 1:
            return self.best_case_no_wilds(cards, special)
        else:
            formations = list(
                map(
                    lambda cards: self.best_case_no_wilds(cards, special),
                    cardOptions
                )
            )
            bestFormation = formations[0]
            for formation in formations[1:]:
                if compare_formations([formation, bestFormation], 0) == 0:
                    bestFormation = formation
            return bestFormation

    def best_case_no_wilds(self, cards, special=[]):
        """Same as best_case, but assumes no wild tactics present."""
        formationSize = FORMATION_SIZE
        if 'mud' in special:
            formationSize += 1
        if 'fog' in special:
            return self.best_fog(cards, formationSize)

        if len(cards) == formationSize:
            return detect_formation(cards)

        if cards == []:
            if 'mud' in special:
                return self.bestMud
            else:
                return self.best

        firstValue, firstSuit = cards[0]
        straight, triple, flush = check_formation_components(cards, formationSize)

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

        if triple:
            formation = copy.copy(cards)
            for card in self.cardsLeft['troop']:
                if card[0] == firstValue:
                    formation += [card]
                    if len(formation) == formationSize:
                        return detect_formation(formation)

        if flush:
            formation = copy.copy(cards)
            for value in TROOP_CONTENTS[::-1]:
                if value + firstSuit in self.cardsLeft['troop']:
                    formation.append(value + firstSuit)
                    if len(formation) == formationSize:
                        return detect_formation(formation)

        if straight:
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

        return self.best_fog(cards, formationSize) # Sum

    def best_fog(self, cards, formationSize):
        """Same as best_case_no_wilds, but ignores formations."""
        cardsLeft = sorted(self.cardsLeft['troop'], reverse=True) # Desc.
        nEmptySlots = formationSize - len(cards)
        return detect_formation(cards + cardsLeft[:nEmptySlots])

    def best_empty(self, mud=False): ### TODO: Loop through best_case instead?
        """Find best formation (self.best) still playable at an empty flag."""
        special = []
        oldBest = self.best # Exclude better formations from search.
        formationSize = FORMATION_SIZE
        if mud:
            special += ['mud']
            oldBest = self.bestMud
            formationSize += 1

        cardsLeft = sorted(self.cardsLeft['troop'], reverse=True) # Desc.
        for fType in POKER_HIERARCHY[POKER_HIERARCHY.index(oldBest['type']):]:
            if fType == 'sum':
                return self.best_case(cardsLeft[:formationSize], special)
            
            if fType == 'flush':
                bestSoFar = {'strength':0}
                for card in cardsLeft:                         #     
                    self.cardsLeft['troop'].remove(card)       # Card can't be
                    bestCase = self.best_case([card], special) # played twice.
                    self.cardsLeft['troop'].append(card)       #
                    if bestCase['type'] == fType:
                        if bestCase['strength'] > bestSoFar['strength']:
                            bestSoFar = bestCase
                if bestSoFar['strength'] > 0:
                    return bestSoFar

            ### TODO: Don't double-check same-valued triples, straights.
            for card in cardsLeft:
                bestCase = self.best_case([card], special)
                if bestCase['type'] == fType:
                    return bestCase

    def update_flag(self, flag, justPlayed, forceUpdate=False):
        """Find the new best continuation at the flag, if necessary."""
        special = []
        formationSize = FORMATION_SIZE
        if flag.mud:
            special = ['mud']
            formationSize += 1
        if flag.fog:
            special += ['fog']

        for p in range(N_PLAYERS):
            if forceUpdate or (justPlayed in flag.best[p]['cards']) !=\
                              (justPlayed in flag.played[p]):
                flag.best[p] = self.best_case(flag.played[p], special)

    def check_winner(self):
        """Check for a majority or breakthrough victory.  Return any winner."""
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

    def show_flags(self):
        """Jankily print the board state."""
        formationSize = FORMATION_SIZE + 1 # Allow for Mud.

        padLength = 18
        lines = [' ' * padLength] * 13

        lines[4] = '  ' + self.h[0].name + ' ' * (18 - 2 - len(self.h[0].name))
        lines[8] = '  ' + self.h[1].name + ' ' * (18 - 2 - len(self.h[1].name))

        for i, flag in enumerate(self.flags):
            center = '{}*     '.format(i)
            p0, p1 = '       ', '       '
            if flag.winner == 0:
                center = '{}      '.format(i)
                p0     = ' *     '
            elif flag.winner == 1:
                center = '{}      '.format(i)
                p1     = ' *     '
            lines[0]  += p0
            if flag.mud:
                center = center[:2] + 'Mu' + '   '
            if flag.fog:
                lines[6] = lines[6][:-2] + 'Fo'
            lines[6]  += center
            lines[12] += p1

            for p in range(N_PLAYERS):
                for j in range(formationSize):
                    if p == 0:
                        iLine = 4 - j
                    else:
                        iLine = 8 + j

                    if j < len(flag.played[p]):
                        lines[iLine] += flag.played[p][j] + ' ' * 5
                    else:
                        lines[iLine] += ' ' * 7

        for f in self.flags:
            if f.mud:
                break
        else: # Remove extra display lines if Mud not in play.
            del lines[1]
            del lines[11]

        [print(line[:79]) for line in lines]
        print('-'*79)


    class Flag():
        """Track all cards played at one flag.

        played (list of 2 list): Troop-like cards played on each side
        best (list of 2 dict): Best formation still achievable on each side
        fog, mud (bool): Whether said card is in play here
        winner (int or None): Who won the flag
        """

        def __init__(self, initialBest):
            self.played = [[], []]
            self.best = [initialBest, initialBest]
            self.fog = False
            self.mud = False
            self.winner = None

        def has_card(self, p):
            """Check whether the player has played here."""
            return self.winner == None and self.played[p] != []

        def has_slot(self, p):
            """Check whether the player can play here."""
            nSlots = FORMATION_SIZE
            if self.mud:
                nSlots += 1
            return self.winner == None and len(self.played[p]) < nSlots

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
                            formations[1 - p] = self.best[1 - p]
                            if compare_formations(formations, whoseTurn) == 1 - p:
                                self.winner = 1 - p # Attacker wins.


    class Hand():
        """Manage one player's hand of cards.

        cards (list of str): One str per card (e.g., '2r' is a red two)
        seat (int): Player ID number (starting player is 0, other player is 1)
        name (str): Player name to show in output
        """

        def __init__(self, seat, name):
            self.cards = []
            self.seat = seat
            self.name = name

        def show(self):
            """Print cards (verbose output only)."""
            print(self.name + ': ' + ' '.join(self.cards))
            return len(self.name + ': ')

        def add(self, newCard):
            self.cards.append(newCard)

        def drop(self, card):
            self.cards.remove(card)
