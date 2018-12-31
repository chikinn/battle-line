"""A simple tactics player.

Tactful Player plays tactics whenever possible.  Otherwise, plays like Kenny.
"""

from bl_classes import *

class TactfulPlayer(Player):
    @classmethod
    def get_name(cls):
        return 'tactful'

    def play(self, r):
        me = r.whoseTurn
        mySlots = [i for i, f in enumerate(r.flags) if f.slots_left(me) > 0]

        if len(mySlots) == 0:
            return None, None, None # Pass.

        cards = r.h[me].cards
        tactics = [c for c in cards if c in TACTICS]

        if tactics != [] and r.tacticsAdvantage != 1-me: # Play tactics!
            random.shuffle(tactics)
            for card in tactics:
                if is_playable(r, card):
                    target = self.play_tactics(r, card, mySlots, me)
                    return card, target, r.prefer_deck('tactics')

        # Play troop.
        if len(tactics) == HAND_SIZE:
            return None, None, None # Pass if no troops in hand.
        card = random.choice(cards)
        while card in TACTICS:
            card = random.choice(cards)
        target = random.choice(mySlots)
        return card, target, r.prefer_deck('tactics')

    def scout_discards(self, r):
        cards = r.h[r.whoseTurn].cards
        troops = [c for c in cards if c not in TACTICS]
        discardPool = troops
        if troops == []:
            discardPool = cards

        return random.sample(discardPool, 2)

    def play_tactics(self, r, card, mySlots, me):
        myCards   = [i for i, f in enumerate(r.flags) if f.has_card(me)]
        yourCards = [i for i, f in enumerate(r.flags) if f.has_card(1-me)]

        if card in ('Fo', 'Mu'):
            return random.choice([i for i, f in enumerate(r.flags)
                                  if f.winner == None])

        if card == 'De':
            f = random.choice(yourCards)
            c = random.choice(r.flags[f].played[1-me])
            return c,

        if card == 'Tr':
            c = random.choice(
                    [card for flag in yourCards
                          for card in r.flags[flag].played[1-me]
                           if card not in TACTICS])
            f2 = random.choice(mySlots)
            return c, f2

        if card == 'Re':
            f1 = random.choice(myCards)
            c  = random.choice(r.flags[f1].played[me])
            f2 = random.choice(mySlots + [None])
            return c, f2

        if card in ('Al', 'Da', 'Co', 'Sh'):
            return random.choice(mySlots)

        if card == 'Sc':
            return 'tactics', 'tactics', 'tactics'
