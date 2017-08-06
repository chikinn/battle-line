# Battle Line
#### Robert B. Kaspar (rbkaspar@gmail.com) and Ben Zax

Computer players for a poker-inspired two-player card game

Intended to run in Python 3 (change the shebang in `bl_wrapper.py`)

## Example usage
    $ ./bl_wrapper.py racist naive

## Snippet of example output
    ---------------------------------------------------------------------------
    Racist: 1o 2b 2g 1g 7y 0y 6y
            Passes
    
    Naive : 0r 1p 1y 2y 4y 3r 4r
            Plays 4y at 0
            Draws troop
    
                      *                    *      *                    *      *
                     4y            9r     8b     0g                   4p     4b
                     6g     7o     5r     7b     3g            2o     2p     5b
      Naive          5g     7r     6r     9b     8g     9o     4o     6p     3b
                     
                     0      1*     2      3      4      5      6*     7      8 
                     
      Racist         1r     8o     8y     7g     6b     7p     3p     4g       
                     5p     3o     9y            1b     9p     0p     6o       
                     9g     5o     5y            0b     8p     0o              
                                                                               
                                    *                    *                     
    ---------------------------------------------------------------------------
    Winner: Naive

## Available players
No tactics
* **Kenny** (`kenny`) by RK<br>
  Veteran AI also skilled at Skat, plays at random
* **Racist** (`racist`) by Jake Kaspar<br>
  Believes colors should be segregated
* **Naïve** (`naive`) by RK<br>
  Dreams big
* **OCD** (`ocd`) by JK<br>
  Three of a kind soothes the orderly mind

Tactics
* **Tactful** (`tactful`) by RK<br>
  Like Kenny but draws and plays only tactics
