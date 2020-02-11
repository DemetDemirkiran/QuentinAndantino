# QuentinAndantino
Project for KEN4123 ISG 2019 Sept @ DKE @ UM - Andantino

This game is played on a hexagonal 10 by 10 board. 
This game is a two-player board game.
To start the game the first player can drop a stone in any position adjacent to the center of the board. 
Afterwards, all additional moves must be done such that stones are placed adjacent to two other stones. 
The win conditions are when a player can make a line of length~5 with their stones or when a player can 
fully enclose one or more opposing stones with at least 6 of their own moves.
In this project the first player's colour is red and the second player is blue.  

To be able to play as either player 1 or player 2, the person playing the game must change the `types' parameter
in the configs.py file. Currently, the default setting is `` `human', `ai' ". 
Meaning the first player would be us and the second player is the AI. 
To play as the second player the types must be changed to `` `ai', `human' ". 
Alternatively, both players can be human(`` `human', `human' ") or AI (`` `ai', `ai' "). 
Be aware that, due to the time management strategy, the play time would exceed the ten minute limit. 
