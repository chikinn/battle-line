"""High-level instructions for playing a round of Battle Line.

Intended to be imported into a wrapper (bl_wrapper) so that more than one round
can be played.  Low-level details and thorough documentation are in another
module (bl_classes).
"""

from bl_classes import *

def play_one_round(players, names, verbose):
    """Play a full round and return the winner (str)."""
    r = Round(players, names, verbose) # Round master object -- used everywhere
    r.generate_decks_and_deal_hands()

    lastPlayerPassed = False
    while r.winner == None: # Take turns until game ends.
        hand = r.h[r.whoseTurn]
        if verbose:
            padLength = hand.show()

        play = r.get_play(players[r.whoseTurn]) # Do a turn.
        if play == None: # Allow passing.
            if verbose:
                print(padLength * ' ' + 'Passes\n')
            if lastPlayerPassed: # Two consecutive draws
                return 'none (drawn)'
            lastPlayerPassed = True
        else:
            lastPlayerPassed = False
            card, target, deckName = play

            if card in r.best['cards']:
                r.best = r.best_empty()

            if card in r.bestMud['cards']:
                r.bestMud = r.best_empty(True)

            for f in r.flags:
                r.update_flag(f, card) # Track best possible continuation.
                f.try_to_resolve(r.whoseTurn)

            r.winner = r.check_winner()

            if verbose:
                print(padLength * ' ' + 'Plays {} at {}'.format(card, target))
                print(padLength * ' ' + 'Draws {}\n'.format(deckName))
                r.show_flags()

        r.whoseTurn = 1 - r.whoseTurn

    return r.h[r.winner].name
