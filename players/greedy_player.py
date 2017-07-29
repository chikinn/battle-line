"""A simple tactics player.

Greedy Player plays as many tactics cards as possible.  Otherwise, plays like
Random Player.
"""

from bl_classes import *

class GreedyPlayer(Player):

    @classmethod
    def get_name(cls):
        return 'greedy'

    def __init__(self, *args):
        """Can be overridden to perform initialization, but must call super."""
        super(GreedyPlayer, self).__init__(*args)

    def play(self, r):
        me = r.whoseTurn
        mySlots   = [i for i, f in enumerate(r.flags) if f.has_slot(me)]
        myCards   = [i for i, f in enumerate(r.flags) if f.has_card(me)]
        yourCards = [i for i, f in enumerate(r.flags) if f.has_card(1 - me)]

        if len(mySlots) == 0:
            return None, None, None

        cards = r.h[me].cards
        tactics = [c for c in cards if c != 'Sc']
        playTroop = False

        if tactics != [] and r.tacticsAdvantage != 1 - me: # Play tactics!
            random.shuffle(tactics)

            for card in tactics:
                if is_playable(r, card):
                    break
            else:
                playTroop = True;

            if not playTroop:
                if card in ('Fo', 'Mu'):
                    target = random.choice([i for i, f in enumerate(r.flags)
                                            if f.winner == None])
    
                elif card == 'De':
                    f = random.choice(yourCards)
                    c = random.choice(r.flags[f].played[1 - me])
                    target = c,
    
                elif card == 'Tr':
                    c = random.choice(
                            [card
                                for flag in yourCards
                                    for card in r.flags[flag].played[1 - me]
                                        if card not in TACTICS])
                    f2 = random.choice(mySlots)
                    target = c, f2
    
                elif card == 'Re':
                    f1 = random.choice(myCards)
                    c = random.choice(r.flags[f1].played[me])
                    f2 = random.choice(mySlots + [None])
                    target = c, f2

                elif card in ('Al', 'Da', 'Co', 'Sh'):
                    target = random.choice(mySlots)
        else:
            playTroop = True

        if playTroop:
            if len([c for c in cards if c in TACTICS]) == HAND_SIZE:
                return None, None, None
            card = random.choice(cards)
            while card in TACTICS:
                card = random.choice(cards)
            target = random.choice(mySlots)

        return card, target, r.prefer_deck('tactics')
