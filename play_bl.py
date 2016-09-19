"""High-level instructions for playing a round of Hanabi.

Intended to be imported into a wrapper (hanabi_wrapper) so that more than one
round can be played.  Low-level details, along with thorough documentation, are
in another module (hanabi_classes).
"""

from bl_classes import *

def play_one_round(gameType, players, names, verbosity, lossScore, isPoliced):
    """Play a full round and return the winner (str)."""
    r = Round(players, names, verbosity) # Instance of a single Battle Line round
    r.generate_deck_and_deal_hands()

    while not r.winner:
        r.get_play(players[r.whoseTurn]) # Play one turn.
        r.whoseTurn = 1 - r.whoseTurn

    return r.winner 
