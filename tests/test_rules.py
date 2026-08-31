from unittest import TestCase

from morabaraba.players import EMPTY, STARTING_COWS, Player
from morabaraba.rules import (
    BOARDS,
    base_legal_moves,
    capture_options,
    legal_moves,
    threats,
)


class BoardRuleTests(TestCase):
    def test_board_topologies_match_the_supported_variants(self) -> None:
        koti, traditional, compact = BOARDS

        self.assertEqual(koti.point_count, 25)
        self.assertTrue(koti.center_enabled)
        self.assertEqual(traditional.point_count, 24)
        self.assertFalse(traditional.center_enabled)
        self.assertEqual(compact.point_count, 25)
        self.assertTrue(compact.center_enabled)

    def test_traditional_capture_protects_mill_cows(self) -> None:
        traditional = BOARDS[1]
        board = [EMPTY] * traditional.point_count
        board[0] = board[1] = board[2] = Player.BLUE
        board[3] = Player.BLUE

        self.assertEqual(capture_options(traditional, board, Player.BLUE), (3,))

    def test_traditional_allows_mill_capture_when_all_cows_are_in_mills(self) -> None:
        traditional = BOARDS[1]
        board = [EMPTY] * traditional.point_count
        board[0] = board[1] = board[2] = Player.BLUE

        self.assertEqual(capture_options(traditional, board, Player.BLUE), (0, 1, 2))

    def test_koti_capture_can_take_any_opponent_cow(self) -> None:
        koti = BOARDS[0]
        board = [EMPTY] * koti.point_count
        board[0] = board[1] = board[2] = Player.BLUE
        board[3] = Player.BLUE

        self.assertEqual(capture_options(koti, board, Player.BLUE), (0, 1, 2, 3))

    def test_koti_forces_available_blocks(self) -> None:
        koti = BOARDS[0]
        board = [EMPTY] * koti.point_count
        board[0] = board[1] = Player.RED
        hand = {Player.RED: STARTING_COWS - 2, Player.BLUE: STARTING_COWS}

        self.assertEqual(threats(koti, board, Player.RED), {2})
        self.assertIn((None, 2), base_legal_moves(koti, board, hand, Player.BLUE))
        self.assertEqual(legal_moves(koti, board, hand, Player.BLUE), ((None, 2),))
