"""A despicable Hanabi player.

Cheating Idiot never hints.  He peeks at his cards.  When he has a play, he
picks one randomly.  When he doesn't, he discards randomly.
"""

from bl_classes import *
import random

class RandomPlayer(Player):

    @classmethod
    def get_name(cls):
        return 'random'

    def __init__(self, *args):
        """Can be overridden to perform initialization, but must call super"""
        super(RandomPlayer, self).__init__(*args)

    def play(self, r):
        me = r.whoseTurn

        cards = r.h[me].cards
        card = random.choice(cards)

        playableFlags = [f for f in r.flags if f['winner'] == None and \
                                               len(f['played'][me]) < 3]
        target = r.flags.index(random.choice(playableFlags))

        return card, target, 'troop'

    def end_game_logging(self):
        """Can be overridden to perform logging at the end of the game"""
        pass
