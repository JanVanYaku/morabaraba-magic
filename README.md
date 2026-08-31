# Morabaraba Magic

A Python/Pygame implementation of **Morabaraba**, built around three selectable board layouts.

## Features

- Play against the computer
- Local two-player mode
- 12 cows per player
- Placement, movement and flying phases
- Mill detection and captures
- Win detection by reducing an opponent to two cows or blocking all legal moves
- Three selectable boards
- Board-specific capture rules
- No external sound or image packs required beyond the included board previews

## Board choices

### Board 1
25 playable points with an active centre cross. Uses the Koti/Sesotho-style capture rule in this build, so a cow inside a mill is not protected from capture.

![Board 1](board_1.png)

### Board 2
24 playable points with an open centre. Cows inside a mill are protected unless every remaining opponent cow is already in a mill.

![Board 2](board_2.png)

### Board 3
A compact visual version of the same 25-point centre-cross topology used by Board 1.

![Board 3](board_3.png)

## Requirements

- Python 3.8+
- Pygame 2.5+

## Installation

```bash
python -m pip install -r requirements.txt
```

## Run

```bash
python morabaraba_magic.py
```

## Controls

- **Mouse**: place, select, move and capture cows
- **N**: start a new game
- **B**: return to board selection
- **Esc**: go back/menu
- **Mouse wheel / arrow keys**: scroll the rules screen

## Project structure

```text
morabaraba-magic/
├── morabaraba_magic.py
├── board_1.png
├── board_2.png
├── board_3.png
├── requirements.txt
├── .gitignore
└── README.md
```

## Current status

The game currently supports desktop play with a computer opponent or two local players. Online multiplayer is not yet implemented.
