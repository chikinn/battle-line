# Battle Line
#### Robert B. Kaspar, rbkaspar@gmail.com

Computer players for a poker-inspired two-player card game

Intended to run in Python 3 (change the shebang in `bl_wrapper.py`)

## Example usage
    $ ./bl_wrapper.py greedy greedy 

## Snippet of example output
    ---------------------------------------------------------------------------
    Greedy1: Al 3y 3b 6o 5b 3o 7b
             Plays 3o at 7
             Draws troop
    
                             *                                                 
                                                                               
                            7g            5y     6r            4r     3o       
                     4p     5r            0g     1g            1b     1r     1o
      Greedy1        5o     6y     7r     4y     8r     2o     2y     0r     2r
                     
                     0*Mu   1      2*     3*     4*   Fo5      6      7      8*
                     
      Greedy2        2g     6g     5p     9p            8g     Sh     9y     Co
                     8p     1y     6p     0o            4o     0b     3p     8o
                     1p            0y                   8b     8y     2b     3g
                     7y                                                        
                                                         *      *      *       
    ---------------------------------------------------------------------------
    Winner: Greedy2

## Available players
* **Random** (`random`) by RK<br>
  Plays at random, never draws tactics
* **Greedy** (`greedy`) by RK<br>
  Like Random Player but insists on drawing and playing tactics

TODO: make better ones!
