"""Board layouts and pure Morabaraba rule helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, TypeAlias

from morabaraba.players import EMPTY, Player, opponent

Coordinate: TypeAlias = tuple[int, int]
Move: TypeAlias = tuple[int | None, int]
BoardState: TypeAlias = list[int]

OUTER_RING: tuple[Coordinate, ...] = (
    (0, 0),
    (3, 0),
    (6, 0),
    (6, 3),
    (6, 6),
    (3, 6),
    (0, 6),
    (0, 3),
)
MIDDLE_RING: tuple[Coordinate, ...] = (
    (1, 1),
    (3, 1),
    (5, 1),
    (5, 3),
    (5, 5),
    (3, 5),
    (1, 5),
    (1, 3),
)
INNER_RING: tuple[Coordinate, ...] = (
    (2, 2),
    (3, 2),
    (4, 2),
    (4, 3),
    (4, 4),
    (3, 4),
    (2, 4),
    (2, 3),
)
CENTER: Coordinate = (3, 3)


@dataclass(frozen=True)
class BoardLayout:
    name: str
    subtitle: str
    description: str
    points: tuple[Coordinate, ...]
    edges: tuple[tuple[int, int], ...]
    mills: tuple[tuple[int, int, int], ...]
    adjacency: tuple[frozenset[int], ...]
    margin: float
    protect_mills: bool
    force_blocks: bool
    center_enabled: bool

    @property
    def point_count(self) -> int:
        return len(self.points)


def count_pieces(board: BoardState, player: Player) -> int:
    return sum(piece == player for piece in board)


def phase_name(board: BoardState, hand: Mapping[Player, int], player: Player) -> str:
    if hand.get(player, 0) > 0:
        return "Placement"
    return "Flying" if count_pieces(board, player) == 3 else "Movement"


def in_mill(layout: BoardLayout, board: BoardState, position: int, player: Player) -> bool:
    return any(
        position in mill and all(board[index] == player for index in mill)
        for mill in layout.mills
    )


def formed_mills(
    layout: BoardLayout,
    before: BoardState,
    after: BoardState,
    destination: int,
    player: Player,
) -> tuple[tuple[int, int, int], ...]:
    previous = {
        mill
        for mill in layout.mills
        if destination in mill and all(before[index] == player for index in mill)
    }
    current = {
        mill
        for mill in layout.mills
        if destination in mill and all(after[index] == player for index in mill)
    }
    return tuple(sorted(current - previous))


def capture_options(
    layout: BoardLayout,
    board: BoardState,
    victim: Player,
) -> tuple[int, ...]:
    pieces = tuple(index for index, piece in enumerate(board) if piece == victim)
    if not layout.protect_mills:
        return pieces

    exposed = tuple(index for index in pieces if not in_mill(layout, board, index, victim))
    return exposed or pieces


def threats(layout: BoardLayout, board: BoardState, player: Player) -> set[int]:
    targets: set[int] = set()
    for mill in layout.mills:
        values = [board[index] for index in mill]
        if values.count(player) == 2 and values.count(EMPTY) == 1:
            targets.add(mill[values.index(EMPTY)])
    return targets


def base_legal_moves(
    layout: BoardLayout,
    board: BoardState,
    hand: Mapping[Player, int],
    player: Player,
) -> tuple[Move, ...]:
    empty_points = tuple(index for index, piece in enumerate(board) if piece == EMPTY)
    if hand.get(player, 0) > 0:
        return tuple((None, destination) for destination in empty_points)

    own_points = tuple(index for index, piece in enumerate(board) if piece == player)
    if len(own_points) == 3:
        return tuple(
            (source, destination)
            for source in own_points
            for destination in empty_points
        )

    return tuple(
        (source, destination)
        for source in own_points
        for destination in layout.adjacency[source]
        if board[destination] == EMPTY
    )


def legal_moves(
    layout: BoardLayout,
    board: BoardState,
    hand: Mapping[Player, int],
    player: Player,
) -> tuple[Move, ...]:
    moves = base_legal_moves(layout, board, hand, player)
    if not layout.force_blocks:
        return moves

    block_targets = threats(layout, board, opponent(player))
    if not block_targets:
        return moves

    blocking_moves = tuple(move for move in moves if move[1] in block_targets)
    return blocking_moves or moves


def has_legal_move(
    layout: BoardLayout,
    board: BoardState,
    hand: Mapping[Player, int],
    player: Player,
) -> bool:
    return bool(legal_moves(layout, board, hand, player))


def _ring_edges(ring: tuple[Coordinate, ...]) -> list[tuple[Coordinate, Coordinate]]:
    return [(ring[index], ring[(index + 1) % len(ring)]) for index in range(len(ring))]


def _unique_edges(
    coord_edges: list[tuple[Coordinate, Coordinate]],
    point_index: dict[Coordinate, int],
) -> tuple[tuple[int, int], ...]:
    seen: set[tuple[int, int]] = set()
    edges: list[tuple[int, int]] = []
    for start, end in coord_edges:
        pair = (point_index[start], point_index[end])
        key = tuple(sorted(pair))
        if key in seen:
            continue
        seen.add(key)
        edges.append(pair)
    return tuple(edges)


def _build_layout(
    *,
    center_enabled: bool,
    margin: float,
    protect_mills: bool,
    force_blocks: bool,
    name: str,
    subtitle: str,
    description: str,
) -> BoardLayout:
    points = OUTER_RING + MIDDLE_RING + INNER_RING + ((CENTER,) if center_enabled else ())
    point_index = {point: index for index, point in enumerate(points)}

    coord_edges: list[tuple[Coordinate, Coordinate]] = []
    coord_edges.extend(_ring_edges(OUTER_RING))
    coord_edges.extend(_ring_edges(MIDDLE_RING))
    coord_edges.extend(_ring_edges(INNER_RING))
    coord_edges.extend(
        [
            ((3, 0), (3, 1)),
            ((3, 1), (3, 2)),
            ((6, 3), (5, 3)),
            ((5, 3), (4, 3)),
            ((3, 6), (3, 5)),
            ((3, 5), (3, 4)),
            ((0, 3), (1, 3)),
            ((1, 3), (2, 3)),
            ((0, 0), (1, 1)),
            ((6, 0), (5, 1)),
            ((6, 6), (5, 5)),
            ((0, 6), (1, 5)),
        ]
    )
    if center_enabled:
        coord_edges.extend(
            [
                ((3, 2), CENTER),
                (CENTER, (3, 4)),
                ((2, 3), CENTER),
                (CENTER, (4, 3)),
            ]
        )

    coord_mills: list[tuple[Coordinate, Coordinate, Coordinate]] = [
        ((0, 0), (3, 0), (6, 0)),
        ((6, 0), (6, 3), (6, 6)),
        ((0, 6), (3, 6), (6, 6)),
        ((0, 0), (0, 3), (0, 6)),
        ((1, 1), (3, 1), (5, 1)),
        ((5, 1), (5, 3), (5, 5)),
        ((1, 5), (3, 5), (5, 5)),
        ((1, 1), (1, 3), (1, 5)),
        ((2, 2), (3, 2), (4, 2)),
        ((4, 2), (4, 3), (4, 4)),
        ((2, 4), (3, 4), (4, 4)),
        ((2, 2), (2, 3), (2, 4)),
        ((3, 0), (3, 1), (3, 2)),
        ((6, 3), (5, 3), (4, 3)),
        ((3, 6), (3, 5), (3, 4)),
        ((0, 3), (1, 3), (2, 3)),
    ]
    if center_enabled:
        coord_mills.extend(
            [
                ((3, 2), CENTER, (3, 4)),
                ((2, 3), CENTER, (4, 3)),
            ]
        )

    edges = _unique_edges(coord_edges, point_index)
    mills = tuple(tuple(point_index[point] for point in mill) for mill in coord_mills)

    adjacency: list[set[int]] = [set() for _ in points]
    for start, end in edges:
        adjacency[start].add(end)
        adjacency[end].add(start)

    return BoardLayout(
        name=name,
        subtitle=subtitle,
        description=description,
        points=points,
        edges=edges,
        mills=mills,
        adjacency=tuple(frozenset(points) for points in adjacency),
        margin=margin,
        protect_mills=protect_mills,
        force_blocks=force_blocks,
        center_enabled=center_enabled,
    )


BOARDS: tuple[BoardLayout, ...] = (
    _build_layout(
        center_enabled=True,
        margin=0.035,
        protect_mills=False,
        force_blocks=True,
        name="Koti 25",
        subtitle="Lesotho Koti - 25 points",
        description="Centre point is active; immediate mills must be blocked; any cow may be captured.",
    ),
    _build_layout(
        center_enabled=False,
        margin=0.075,
        protect_mills=True,
        force_blocks=False,
        name="Traditional 24",
        subtitle="Traditional Morabaraba - 24 points",
        description="Open centre board; cows in mills are protected unless all opponent cows are in mills.",
    ),
    _build_layout(
        center_enabled=True,
        margin=0.075,
        protect_mills=False,
        force_blocks=True,
        name="Koti Compact",
        subtitle="Compact Koti - 25 points",
        description="Compact 25-point Koti board with the same capture and blocking rules.",
    ),
)
