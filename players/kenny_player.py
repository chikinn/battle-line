"""The simplest possible player.

Kenny plays only troops, at random, and draws troops if available.
"""

from bl_classes import *

class KennyPlayer(Player):

    @classmethod
    def get_name(cls):
        return 'kenny'

    def __init__(self, *args):
        super(RandomPlayer, self).__init__(*args)

    def play(self, r):
        me = r.whoseTurn

        cards = r.h[me].cards
        card = random.choice(cards)
        while card in TACTICS:
            card = random.choice(cards)

        playableFlags = [i for i, f in enumerate(r.flags) if f.has_slot(me)]

        if len(playableFlags) == 0:
            return None, None, None # Pass.

        return card, random.choice(playableFlags), r.prefer_deck('troop')

    def scout_discards(self, r):
        pass # Never play tactics.
