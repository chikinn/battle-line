#!/usr/bin/env python
"""Wrapper for playing more than one round of Battle Line."""

import sys, argparse, logging, random
from play_bl import play_one_round
from bl_classes import Player
from players import random_player

availablePlayers = {}
for playerSubClass in Player.__subclasses__():
    availablePlayers[playerSubClass.get_name()] = playerSubClass

# Parse command-line args.
parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('declaredPlayers', metavar='p', type=str, nargs=2,
    help=', '.join(availablePlayers.keys()))
parser.add_argument('-n', '--n_rounds', default=1, metavar='n_rounds',
    type=int, help='positive int')
parser.add_argument('-v', '--verbosity', default='verbose',
    metavar='verbosity', type=str, help='silent, scores, verbose, or log')

args = parser.parse_args()

assert args.n_rounds > 0
assert args.verbosity in ('silent', 'scores', 'verbose', 'log')

def mean(lst):
    return sum(lst) / len(lst)

def std_err(lst):
    m = mean(lst)
    n = len(lst)
    sumSquaredErrs = sum([(x - m)**2 for x in lst])
    var = sumSquaredErrs / (n - 1)
    return sqrt(var / n)

# Load players.
players = []
rawNames = args.declaredPlayers
for i in range(len(rawNames)):
    assert rawNames[i] in availablePlayers
    players.append(availablePlayers[rawNames[i]](i, args.verbosity))
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
    if args.verbosity in ('verbose', 'log'):
        print('\n' + 'ROUND {}:'.format(i))
    winners.append(play_one_round(players, names, args.verbosity))
    if args.verbosity != 'silent':
        print('Winner: ' + str(winners[-1]))

# Print average scores.
if args.verbosity != 'silent':
    print('')
if len(winners) > 1: # Only print stats if there were multiple rounds.
    print('Lots of games?  Lazy!')
elif args.verbosity == 'silent': # Still print score for silent single round
    print('Winner: ' + winners[0])
