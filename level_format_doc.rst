Level Format for Frogs
======================

Basics
------
All level files lay in the levels folder. they have to start with "level_" and must have the ending ".txt"
A level file is a simple text file. In every line is an game object defined and you can make a reference to it by an id. The order doesn't matter.
Positions are defined in a table with row,column.
Every id should exist only one time. Some objects exist in every level and they have the following ids and functions:

Predefined objects
------------------
- background: Background image
- start: The start point of the level. The player should sit there
- end: The end point of the level. If the player reaches it, the level is won
- game_scatter: internal
- live1, live1, live2: The 3 live images. You shouldn't need them
- status: A label to diplay status messages like "Won" or "Lost"
- energy_label: Displays the energy of the player

Defining objects
----------------
An object definition has the following, simple structure:
type option=value option1=value1 ...
Multiple values are seperated by a comma

Types
-----
Here are all the types described which you can/must use in your levels

Required types
**************
The options are in the format description, example
level
_____
Basic settings for the current level.
Options:
- size: The number of rows,columns in the level, size=6,7
- energy: The start energy for the player, energy=4
- flys: The number of flys in the level, flys=4
- boats: The number of boats in the level, boats=1

background
__________
The background image
Options:
- source: Path to the background image, source=img/background.png
:WARNING: The path is not allowed to contain commas or the parsing will fail

start
_____
The start point where the player should start
Options:
- pos: described above
- source: Path to an image

end
___
The end point where the level is finished
Options:
- pos: described above
- source: Path to an image

waterlily
_________
A waterlily where the frogs can jump on. It sinks after a short time (4 seconds or so) and sinks if the boat touches it
Options:
- id: Clear id, id=lily
- pos: described above

stonelily
__________
Same as waterlily, but doesn't sink.
Options:
- see waterlily

switchlily
__________
A stonelily with a a bit different look. It makes a other lily appear if a frog is sitting on it and makes the lily sink if the frog leaves it.
Options:
- see stonelily, and:
- controlled: An id which refers to another lily, controlled=lily1

frog
____
A frog which can jump around, eat flys and die
Options:
- id: A clear id, id=frog1
- player: Defines if the frog is the player or not. It should only one time set to True. Possible values: True, False. example: player=True
- sit_img: A path to an image where the frog is sitting. It is displayed while the frog sits, sit_img=img/frog_black_sit.png
- jump_img: Like sit_img, but displayed while the frog is jumping
- place: The place where the frog is sitting on. That must be the id of a lily, start or end, place=lily1

math
____
An exercise in math. Number range and type can be defined by the user in the settings. It consists of a label, which displays the exercise and *count* lilys, which move with *speed* in *orientation* direction and which can't sink. On every lily is a number but not all are right. If the user jumps onto the lily with the right number he can sit on it, else he will fall into the water and loose one live.
Options:
- id: clear id, id=math2
- pos: the position of the first lily
- count: The number of lilys, count=5
- speed: The speed with that the lilys move, speed=1.1
- orientation: The orientation to which the lilys move. Possible values are: vertical, horizontal, orientation=horizontal

interval
________
Same as math, but there is not a interval hearing exercise instead of a math exercise. On touch of a label the user will hear two tones and has to say which interval it is.
Options:
- see math
