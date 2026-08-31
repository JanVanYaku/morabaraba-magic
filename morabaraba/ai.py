"""Simple computer opponent for Morabaraba Magic."""

from __future__ import annotations

import random

from morabaraba.players import EMPTY, Player, opponent
from morabaraba.rules import (
    BoardLayout,
    Move,
    capture_options,
    formed_mills,
    in_mill,
    legal_moves,
    threats,
)


def choose_move(
    layout: BoardLayout,
    board: list[int],
    hand: dict[Player, int],
    player: Player,
    rng: random.Random,
) -> Move | None:
    moves = legal_moves(layout, board, hand, player)
    if not moves:
        return None

    ranked = [
        (_score_move(layout, board, hand, player, move, rng), move)
        for move in moves
    ]
    ranked.sort(key=lambda item: item[0], reverse=True)
    return ranked[0][1]


def choose_capture(
    layout: BoardLayout,
    board: list[int],
    victim: Player,
    rng: random.Random,
) -> int | None:
    options = capture_options(layout, board, victim)
    if not options:
        return None

    ranked = [
        (_score_capture(layout, board, victim, position, rng), position)
        for position in options
    ]
    ranked.sort(key=lambda item: item[0], reverse=True)
    return ranked[0][1]


def _score_move(
    layout: BoardLayout,
    board: list[int],
    hand: dict[Player, int],
    player: Player,
    move: Move,
    rng: random.Random,
) -> float:
    source, destination = move
    before = board.copy()
    after = board.copy()
    simulated_hand = dict(hand)

    if source is None:
        after[destination] = player
        simulated_hand[player] -= 1
    else:
        after[source] = EMPTY
        after[destination] = player

    enemy = opponent(player)
    score = rng.random()

    if formed_mills(layout, before, after, destination, player):
        score += 10_000
    if destination in threats(layout, board, enemy):
        score += 2_500

    score += len(threats(layout, after, player)) * 150
    score -= len(threats(layout, after, enemy)) * 130
    score += len(layout.adjacency[destination]) * 12

    if simulated_hand[player] == 0:
        score += len(_empty_neighbours(layout, after, destination)) * 8
    return score


def _score_capture(
    layout: BoardLayout,
    board: list[int],
    victim: Player,
    position: int,
    rng: random.Random,
) -> float:
    after = board.copy()
    after[position] = EMPTY

    score = rng.random()
    if in_mill(layout, board, position, victim):
        score += 500
    score += len(threats(layout, board, victim)) * 60
    score -= len(threats(layout, after, victim)) * 100
    score += len(layout.adjacency[position]) * 5
    return score


def _empty_neighbours(
    layout: BoardLayout,
    board: list[int],
    position: int,
) -> tuple[int, ...]:
    return tuple(
        neighbour
        for neighbour in layout.adjacency[position]
        if board[neighbour] == EMPTY
    )
