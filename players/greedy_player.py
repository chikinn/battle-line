"""A simple tactics player.

Greedy Player plays as many tactics cards as possible.  Otherwise, plays like
Random Player.
"""

from bl_classes import *
import random

class GreedyPlayer(Player):

    @classmethod
    def get_name(cls):
        return 'greedy'

    def __init__(self, *args):
        """Can be overridden to perform initialization, but must call super."""
        super(GreedyPlayer, self).__init__(*args)

    def play(self, r):
        me = r.whoseTurn

        myEmpty = [i for i, f in enumerate(r.flags) \
                   if f.winner == None and len(f.played[me]) < 3]

        if len(myEmpty) == 0:
            return None, None, None

        cards = r.h[me].cards
        tactics = [card for card in cards if card in ['De', 'Tr', 'Re']]

        if len(tactics) > 0 and r.tacticsAdvantage != 1 - me: # Play tactics!
            card = random.choice(tactics)

            myFull   = [i for i, f in enumerate(r.flags) \
                        if f.winner == None and len(f.played[me]) > 0]
            yourFull = [i for i, f in enumerate(r.flags) \
                        if f.winner == None and len(f.played[1 - me]) > 0]

            if card == 'De':
                f = random.choice(yourFull)
                c = random.choice(r.flags[f].played[1 - me])
                target = c,

            elif card == 'Tr':
                f1 = random.choice(yourFull)
                c  = random.choice(r.flags[f1].played[1 - me])
                f2 = random.choice(myEmpty)
                target = c, f2

            elif card == 'Re':
                f1 = random.choice(myFull)
                c = random.choice(r.flags[f1].played[me])
                f2 = random.choice(myEmpty + [None])
                target = c, f2

        else: # Play troop.
            if sum([1 for c in cards if c in TACTICS]) == HAND_SIZE:
                return None, None, None
            card = random.choice(cards)
            while card in TACTICS:
                card = random.choice(cards)
            target = random.choice(myEmpty)

        return card, target, 'tactics'
