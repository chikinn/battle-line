"""The simplest possible player.

Random Player plays only troops, at random, and draws troops if available.
"""

from bl_classes import *
import random

class RandomPlayer(Player):

    @classmethod
    def get_name(cls):
        return 'random'

    def __init__(self, *args):
        """Can be overridden to perform initialization, but must call super."""
        super(RandomPlayer, self).__init__(*args)

    def play(self, r):
        me = r.whoseTurn

        cards = r.h[me].cards
        card = random.choice(cards)
        while card in TACTICS:
            card = random.choice(cards)

        playableFlags = []
        for i, flag in enumerate(r.flags):
            if flag.winner == None and len(flag.played[me]) < 3:
                playableFlags.append(i)

        if len(playableFlags) == 0:
            return None, None, None

        return card, random.choice(playableFlags), r.preferTroops()
