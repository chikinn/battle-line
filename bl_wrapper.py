#!/usr/bin/env python
"""Wrapper for playing more than one round of Battle Line."""

import sys, argparse, logging, random, math
from play_bl import play_one_round
from bl_classes import Player
from players import *

availablePlayers = {}
for playerSubClass in Player.__subclasses__():
    availablePlayers[playerSubClass.get_name()] = playerSubClass
    # Sniper Player inherits Naive Player, not vanilla Player.
    for playerSubSubClass in playerSubClass.__subclasses__():
        availablePlayers[playerSubSubClass.get_name()] = playerSubSubClass

# Parse command-line args.
parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('declaredPlayers', metavar='player', type=str, nargs=2,
    help=', '.join(availablePlayers.keys()))
parser.add_argument('-n', '--n_rounds', default=1, metavar='n_rounds',
    type=int, help='positive int')

args = parser.parse_args()

assert args.n_rounds > 0
verbose = True
if args.n_rounds > 1:
    verbose = False

# Load players.
players = []
rawNames = args.declaredPlayers
for i in range(len(rawNames)):
    assert rawNames[i] in availablePlayers
    players.append(availablePlayers[rawNames[i]](i))
    rawNames[i] = rawNames[i].capitalize()

# Resolve duplicate names by appending '1', '2', etc. as needed.
names = []
counters = {name : 0 for name in rawNames}
for name in rawNames:
    if rawNames.count(name) > 1:
        counters[name] += 1
        names.append(name + str(counters[name]))
    else:
        names.append(name)

# Pad names for better verbose display.
longestName = ''
for name in names:
    if len(name) > len(longestName):
        longestName = name
for i in range(len(names)):
    while len(names[i]) < len(longestName):
        names[i] += ' '

# Play rounds.
winners = []
for i in range(args.n_rounds):
    if verbose:
        print('\nROUND {}:'.format(i))
    winners.append(play_one_round(players, names, verbose))
    if not verbose:
        print('Winner: {}'.format(winners[-1]))

# Print average scores.
if not verbose:
    print('')
if len(winners) > 1: # Print stats only if there were multiple rounds.
    nDraws = args.n_rounds - sum([winners.count(n) for n in names])
    for name in names:
        ratio = (winners.count(name) + 0.5 * nDraws) / args.n_rounds
        stdErr = math.sqrt(ratio * (1 - ratio) / args.n_rounds)
        if ratio >= 0.5:
            print('{0} wins {1:.3f} +/- {2:.3f}'.format(name, ratio, stdErr))
            break
 
elif verbose: # Still print score for silent single round.
    print('Winner: {}'.format(winners[0]))
