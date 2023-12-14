# Idea

Command Modes:
- Manual mode: the user directly writes to
the console all the commands the machine 
should execute.
- Automatic mode: The machine figures out the
list of commands to execute on its own.

The key idea would be to unify the set of 
commands we have at our disposal in either
mode. 

List of commands to implement:
- Goto (float distance, float orientation)


Order:
have a representation of the map (as a 2d
array), and do some A* pathfinding on this map.
Then we get a new position to go towards, and
we go there. Rince and repeat.


