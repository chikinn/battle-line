# Battle Line
#### Robert B. Kaspar (rbkaspar@gmail.com) and Ben Zax

Computer players for a poker-inspired two-player card game

Intended to run in Python 3 (change the shebang in `bl_wrapper.py`)

## Example usage
    $ ./bl_wrapper.py sniper naive 

## Snippet of example output
    ...
    ---------------------------------------------------------------------------
    Naive : 9g 0r 1b 9b 5b 0b 1y
            Plays 9g at 1
            Draws troop
    
                                           *      *             *      *       
                     8r                   3o     4y            7o     6p       
                     8y     7b     6g     4o     5y            8o     4p       
      Sniper         8b     6b     8g     5o     6y     6o     9o     5p     3r
                     
                     0*     1*     2*     3      4      5      6      7      8*
                     
      Naive          1o     2g     4b     9y     9r     9p     2r     1p     3g
                     0o     0g     3b     7y     7r     7p     1r            3y
                            9g     2b            4r     8p                     
                                                                               
                                                         *                     
    ---------------------------------------------------------------------------
    Sniper: 1g 0p 3p 5g 2o 2p Fo
            Plays Fo at 0
            Draws tactics
    
                      *                    *      *             *      *       
                     8r                   3o     4y            7o     6p       
                     8y     7b     6g     4o     5y            8o     4p       
      Sniper         8b     6b     8g     5o     6y     6o     9o     5p     3r
                     
                   Fo0      1*     2*     3      4      5      6      7      8*
                     
      Naive          1o     2g     4b     9y     9r     9p     2r     1p     3g
                     0o     0g     3b     7y     7r     7p     1r            3y
                            9g     2b            4r     8p                     
                                                                               
                                                         *                     
    ---------------------------------------------------------------------------
    Winner: Sniper

## Available players
No tactics
* **Kenny** (`kenny`) by RK<br>
  Veteran AI also skilled at skat; plays at random
* **Racist** (`racist`) by Jake Kaspar<br>
  Believes colors should be segregated
* **Naïve** (`naive`) by RK<br>
  Dreams big
* **OCD** (`ocd`) by JK<br>
  Three of a kind soothes the orderly mind

Tactics
* **Tactful** (`tactful`) by RK<br>
  Like Kenny but draws and plays only tactics
* **Sniper** (`sniper`) by RK<br>
  Copies Naïve, plus tactics for the coup de grâce

The strongest player is currently **Sniper**, who beats **Naïve** 54.5 ± 0.2% of the time (n = 10^5).
