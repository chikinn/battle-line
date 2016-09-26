"""High-level instructions for playing a round of Hanabi.

Intended to be imported into a wrapper (hanabi_wrapper) so that more than one
round can be played.  Low-level details, along with thorough documentation, are
in another module (hanabi_classes).
"""

from bl_classes import *

def play_one_round(players, names, verbosity):
    """Play a full round and return the winner (str)."""
    r = Round(players, names, verbosity) # Instance of one Battle Line round
    r.generate_decks_and_deal_hands()

    while r.winner == None:
        r.get_play(players[r.whoseTurn]) # Play one turn.
        for flag in r.flags:
            r.check_flag(flag)
        r.winner = r.check_winner()

        r.whoseTurn = 1 - r.whoseTurn

    for flag in r.flags:
        print(flag['played'])
        print(flag['winner'])

    return r.winner 
