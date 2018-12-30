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
        winningPlay = self.find_winning_tactics_play(r)
        if winningPlay is not None:
            return winningPlay

        # Play recommended by parent non-tactics player
        oldPlay = super().play(r)
        if oldPlay == None: # Pass.
            return oldPlay
        card, flag, deck = oldPlay

        if self.exists_winning_tactics_draw(r):
            deck = r.prefer_deck('tactics')

        return card, flag, deck

    def exists_winning_tactics_draw(self, r):
        # Edge case: returns true if card is already in hand
        p = r.whoseTurn
        for i, f in enumerate(r.flags):
            if flag_wins_game(r, i, p):
                for card in r.cardsLeft['tactics']:
                    if find_play_to_win_flag(r, card, i, p) != None:
                        return True
        return False

    def find_winning_tactics_play(self, r):
        p = r.whoseTurn
        for card in r.h[p].cards:
            if card in TACTICS:
                for i, f in enumerate(r.flags):
                    if flag_wins_game(r, i, p):
                        winsFlag = find_play_to_win_flag(r, card, i, p)
                        if winsFlag != None:
                            target = winsFlag
                            deck = r.prefer_deck('tactics') # Arbitrary
                            return card, target, deck
        return None
