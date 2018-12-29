"""An opportunist who waits patiently for the kill.

Sniper Player mimics the best no-tactics player (currently Naive).  In
addition, when choosing which deck to draw from, he checks whether there exists
a tactics card that could cause him to win next turn.  If so, draws tactics.
Plays tactics only when it wins immediately.
"""

from bl_classes import *
from players.naive_player import NaivePlayer

class SniperPlayer(NaivePlayer):
    @classmethod
    def get_name(cls):
        return 'sniper'

    def play(self, r):
        p = check_for_winning_tactics_play()
        if p is not None:
            return p

        # Play recommended by parent non-tactics player
        card, flag, deck = super().play(r)

        if exists_winning_tactics_draw(r):
            deck = r.prefer_deck('tactics')

        return card, flag, deck

    def exists_winning_tactics_draw(self, r):
        pass

    def check_for_winning_tactics_play(self, r):
        pass
