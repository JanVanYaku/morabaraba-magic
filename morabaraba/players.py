"""Player and piece helpers."""

from enum import IntEnum

EMPTY = 0
STARTING_COWS = 12


class Player(IntEnum):
    RED = 1
    BLUE = 2


PLAYER_NAMES = {
    Player.RED: "Red",
    Player.BLUE: "Blue",
}


def opponent(player: Player) -> Player:
    return Player.BLUE if player == Player.RED else Player.RED
