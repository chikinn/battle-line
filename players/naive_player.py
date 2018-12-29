"""An incurable optimist.

Naive Player plays and draws only troops.  He considers playing each card from
his hand at each flag and chooses the pairing that might lead to the strongest
formation later, if only he draws that final card -- which, of course, he will.

Ceteris paribus, he prefers to play in the center of the board.
"""

from bl_classes import *

class NaivePlayer(Player):
    @classmethod
    def get_name(cls):
        return 'naive'

    def play(self, r):
        me = r.whoseTurn
        playableFlags = [i for i,f in enumerate(r.flags)
                         if f.slots_left(me) > 0]
        if len(playableFlags) == 0:
            return None, None, None # Pass.

        bestFlagStrength = -1
        bestPlays = []
        for c in r.h[me].cards:
            if c in TACTICS:
                continue
            for iFlag in playableFlags:
                f = r.flags[iFlag]
                candidate = [c] + f.played[me]
                s = r.best_case_no_wilds(candidate, f.special)['strength']

                if s > bestFlagStrength:
                    bestFlagStrength = s
                    bestPlays = [{'card':c, 'flag':iFlag}]
                elif s == bestFlagStrength:
                    bestPlays.append({'card':c, 'flag':iFlag})

        iBestFlag = self.most_central_flag([p['flag'] for p in bestPlays])
        for p in bestPlays:
            if p['flag'] == iBestFlag:
                return p['card'], p['flag'], r.prefer_deck('troop')

    def most_central_flag(self, candidateFlags):
        bestFlag = -1
        bestDistance = N_FLAGS # Arbitrary large number
        for f in candidateFlags:
            d = abs(f - N_FLAGS // 2)
            if d < bestDistance:
                bestDistance = d
                bestFlag = f
        return bestFlag
