"""Stateful Morabaraba game engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from morabaraba.players import EMPTY, PLAYER_NAMES, STARTING_COWS, Player, opponent
from morabaraba.rules import (
    BOARDS,
    BoardLayout,
    Move,
    base_legal_moves,
    capture_options,
    count_pieces,
    formed_mills,
    has_legal_move,
    legal_moves,
    phase_name,
    threats,
)


class GameMode(StrEnum):
    COMPUTER = "computer"
    LOCAL = "local"


@dataclass
class MorabarabaGame:
    layout: BoardLayout = BOARDS[0]
    mode: GameMode = GameMode.COMPUTER
    board: list[int] = field(init=False)
    hand: dict[Player, int] = field(init=False)
    turn: Player = field(init=False)
    selected: int | None = field(init=False)
    capture_pending: bool = field(init=False)
    winner: Player | None = field(init=False)
    message: str = field(init=False)

    def __post_init__(self) -> None:
        self.reset()

    def start(self, mode: GameMode, layout: BoardLayout) -> None:
        self.mode = mode
        self.layout = layout
        self.reset()

    def reset(self) -> None:
        self.board = [EMPTY] * self.layout.point_count
        self.hand = {Player.RED: STARTING_COWS, Player.BLUE: STARTING_COWS}
        self.turn = Player.RED
        self.selected = None
        self.capture_pending = False
        self.winner = None
        self.message = "Red places the first cow."

    @property
    def placement_active(self) -> bool:
        return self.hand[Player.RED] > 0 or self.hand[Player.BLUE] > 0

    @property
    def is_computer_turn(self) -> bool:
        return self.mode == GameMode.COMPUTER and self.turn == Player.BLUE

    def phase(self, player: Player | None = None) -> str:
        return phase_name(self.board, self.hand, player or self.turn)

    def legal_moves_for_turn(self) -> tuple[Move, ...]:
        return legal_moves(self.layout, self.board, self.hand, self.turn)

    def legal_destinations(self) -> set[int]:
        if self.capture_pending:
            return set(capture_options(self.layout, self.board, opponent(self.turn)))
        if self.hand[self.turn] > 0:
            return {destination for _, destination in self.legal_moves_for_turn()}
        if self.selected is None:
            return set()
        return {
            destination
            for source, destination in self.legal_moves_for_turn()
            if source == self.selected
        }

    def choose_position(self, position: int | None) -> None:
        if position is None or self.winner or self.is_computer_turn:
            return
        if self.capture_pending:
            self.capture(position)
            return
        if self.hand[self.turn] > 0:
            self.place(position)
            return
        self._choose_movement_position(position)

    def place(self, destination: int) -> bool:
        if self.winner or self.capture_pending:
            return False
        if self.hand[self.turn] <= 0:
            self.message = f"{PLAYER_NAMES[self.turn]} has no cows left to place."
            return False
        if self.board[destination] != EMPTY:
            self.message = "Choose an empty point."
            return False
        if (None, destination) not in self.legal_moves_for_turn():
            self.message = self._blocked_mill_message()
            return False

        before = self.board.copy()
        self.board[destination] = self.turn
        self.hand[self.turn] -= 1
        self._finish_action(before, destination)
        return True

    def move(self, source: int, destination: int) -> bool:
        if self.winner or self.capture_pending:
            return False
        if self.board[source] != self.turn:
            self.message = "Select one of your cows first."
            return False
        if self.board[destination] != EMPTY:
            self.message = "Choose an empty destination."
            return False
        if (source, destination) not in self.legal_moves_for_turn():
            self.message = self._blocked_mill_message()
            return False

        before = self.board.copy()
        self.board[source] = EMPTY
        self.board[destination] = self.turn
        self.selected = None
        self._finish_action(before, destination)
        return True

    def capture(self, position: int) -> bool:
        if not self.capture_pending:
            return False

        victim = opponent(self.turn)
        options = capture_options(self.layout, self.board, victim)
        if position not in options:
            self.message = "That cow is protected. Choose a valid capture."
            return False

        self.board[position] = EMPTY
        self.capture_pending = False
        self.selected = None
        self._end_turn()
        return True

    def _choose_movement_position(self, position: int) -> None:
        if self.selected is None:
            if self.board[position] == self.turn:
                self.selected = position
                self.message = "Choose where to move that cow."
            return

        if position == self.selected:
            self.selected = None
            self.message = "Selection cleared."
            return

        if self.board[position] == self.turn:
            self.selected = position
            self.message = "Choose where to move that cow."
            return

        source = self.selected
        self.move(source, position)

    def _finish_action(self, before: list[int], destination: int) -> None:
        if formed_mills(self.layout, before, self.board, destination, self.turn):
            self.capture_pending = True
            self.selected = None
            self.message = f"{PLAYER_NAMES[self.turn]} formed a mill. Capture a cow."
            return
        self._end_turn()

    def _end_turn(self) -> None:
        next_player = opponent(self.turn)
        if not self.placement_active:
            if count_pieces(self.board, next_player) < 3:
                self.winner = self.turn
                self.message = (
                    f"{PLAYER_NAMES[self.turn]} wins by reducing "
                    f"{PLAYER_NAMES[next_player]} to two cows."
                )
                return
            if not has_legal_move(self.layout, self.board, self.hand, next_player):
                self.winner = self.turn
                self.message = f"{PLAYER_NAMES[self.turn]} wins by blocking all legal moves."
                return

        self.turn = next_player
        self.selected = None
        self.message = f"{PLAYER_NAMES[self.turn]}'s turn: {self.phase().lower()}."

    def _blocked_mill_message(self) -> str:
        if self.layout.force_blocks:
            enemy_threats = threats(self.layout, self.board, opponent(self.turn))
            blocking_moves = [
                move
                for move in base_legal_moves(self.layout, self.board, self.hand, self.turn)
                if move[1] in enemy_threats
            ]
            if blocking_moves:
                return "Koti rule: block the open mill first."
        return "That move is not legal on this board."
