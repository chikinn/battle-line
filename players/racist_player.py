"""A color segragator.

Racist attempts to build a rainbow out of the first six flags: red only at flag
1, orange only at flag 2, etc.  The remaining three are a dumping ground.
"""

from bl_classes import *

class RacistPlayer(Player):
    @classmethod
    def get_name(cls):
        return 'racist'

    def play(self, r):
        me = r.whoseTurn

        cards = r.h[me].cards
        
        for card in cards:
            if card in TACTICS:
                continue

            color = TROOP_SUITS.index(card[1])
            if r.flags[color].has_slot(me):
                flag = r.flags[color]
                return card, color, r.prefer_deck('troop')

        playableFlags = [i for i, f in enumerate(r.flags) if f.has_slot(me)]

        if len(playableFlags) == 0:
            return None, None, None # Pass.

        return cards[0], random.choice(playableFlags), r.prefer_deck('troop')
