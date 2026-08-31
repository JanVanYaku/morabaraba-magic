# Morabaraba Magic

```text
#######################################################################
# Author: Lehlohonolo Adolf Matobakele
# Email: lehlohonolo.matobakele@gov.ls
# Contact: 00266 62320704
#######################################################################
```

Morabaraba Magic is a Python/Pygame desktop implementation of the Southern African strategy board game Morabaraba, including Traditional 24-point play and Lesotho Koti-style 25-point variants.

The rules reference used for this version is the Morabaraba guide at <https://morabaraba-magic.lovable.app/>.

## Features

- Play against a computer opponent or another local player.
- 12 cows per player.
- Placement, movement, and flying phases.
- Mill detection and capture flow.
- Traditional 24-point capture protection.
- Koti 25-point active centre, forced blocking, and open capture rules.
- Win detection when a player is reduced to two cows or has no legal moves.
- Highlighted legal destinations and capture targets during play.
- Three selectable board layouts.
- Unit tests for the core rule engine.

## Installation

Install Python 3.11 or newer, then install the Pygame dependency:

```bash
python -m pip install -r requirements.txt
```

## Run

```bash
python morabaraba_magic.py
```

## Test

```bash
python -m unittest discover -s tests
python -m compileall morabaraba morabaraba_magic.py tests
```

## Controls

- Mouse: choose mode, choose board, place cows, select cows, move cows, and capture.
- Esc: return to the main menu.
- New Game: restart the current board and mode.
- Boards: choose a different board without leaving the app.

## Supported Boards

### Koti 25

![Morabaraba Board 1](assets/board_1.svg)

Lesotho Koti-style board with an active centre point. Immediate mills must be blocked when a block is available, and any opponent cow may be captured after forming a mill.

### Traditional 24

![Morabaraba Board 2](assets/board_2.svg)

Traditional open-centre Morabaraba board. Cows inside mills are protected from capture unless every remaining opponent cow is already inside a mill.

### Koti Compact

![Morabaraba Board 3](assets/board_3.svg)

Compact visual version of the 25-point Koti topology, using the same active-centre and capture behavior as Koti 25.

## Project Structure

```text
morabaraba-magic/
├── assets/
│   ├── board_1.svg
│   ├── board_2.svg
│   └── board_3.svg
├── morabaraba/
│   ├── ai.py
│   ├── engine.py
│   ├── players.py
│   ├── rules.py
│   └── ui.py
├── tests/
│   └── test_rules.py
├── morabaraba_magic.py
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Code Notes

- `morabaraba/rules.py` contains pure board topology and legal move logic.
- `morabaraba/engine.py` owns game state and turn transitions.
- `morabaraba/ai.py` scores legal moves for the computer opponent.
- `morabaraba/ui.py` contains the Pygame screens and rendering.
- `morabaraba_magic.py` is intentionally kept as a tiny launcher.
