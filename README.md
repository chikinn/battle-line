# Battle Line
#### Robert B. Kaspar, rbkaspar@gmail.com

Computer players for a poker-inspired two-player card game
Intended to run in Python 3 (change the shebang in bl_wrapper.py)

## Example usage
    $ ./bl_wrapper.py random random

## Snippet of example output
    Random1: 3y 3b 2g 0o 0r 1p 1y
             Plays 0r at 4
             Draws troop
    
                                                           *           *    
                                        0y    0r          6g    9p    9b    
                      6p          5y    9g    3r    1b    8y    7p    6b    
      Random1         2o    4b    4r    0g    2b    8g    4y    7r    3o    
                      
                      0     1*    2     3     4     5*    6     7*    8     
                      
      Random2         3g    0b    6r    7o    8b    6y    5p          4g    
                      1o    4o    8p    5o    5g          2r          1r    
                      2p    6o    7b    3p    9y                      8o    
                       *           *     *     *                            
    
    Winner: Random2

TODO: debug tactics, update proofs for tactics, add non-random players
