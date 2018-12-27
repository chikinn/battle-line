"""A simple player

OCD player tries to sort the cards by number
"""

from bl_classes import *

class OCDPlayer(Player):
    @classmethod
    def get_name(cls):
        return 'ocd'

    def play(self, r):
        me = r.whoseTurn

        cards = r.h[me].cards
        
        for card in cards:

            if card in TACTICS:
                continue

            if  TROOP_CONTENTS.index(card[0])  == 0:
                continue

            number = TROOP_CONTENTS.index(card[0])-1
            if r.flags[number].has_slot(me):
                flag = r.flags[number]
                return card, number, r.prefer_deck('troop')

        playableFlags = [i for i, f in enumerate(r.flags) if f.has_slot(me)]

        if len(playableFlags) == 0:
            return None, None, None # Pass.

        return cards[0], random.choice(playableFlags), r.prefer_deck('troop')

