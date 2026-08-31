"""Pygame user interface for Morabaraba Magic."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

import pygame

from morabaraba.ai import choose_capture, choose_move
from morabaraba.engine import GameMode, MorabarabaGame
from morabaraba.players import EMPTY, PLAYER_NAMES, STARTING_COWS, Player, opponent
from morabaraba.rules import BOARDS, BoardLayout, capture_options, count_pieces

WIDTH = 1180
HEIGHT = 760
FPS = 60
AI_DELAY_MS = 430

BACKGROUND = (18, 27, 31)
PANEL = (31, 43, 47)
PANEL_LIGHT = (44, 59, 63)
BOARD_FILL = (244, 222, 164)
BOARD_LINE = (55, 39, 24)
TEXT = (245, 242, 233)
MUTED = (180, 187, 185)
GOLD = (236, 176, 66)
RED = (216, 66, 65)
BLUE = (55, 135, 205)
WHITE = (255, 255, 255)


@dataclass(frozen=True)
class Fonts:
    regular: pygame.font.Font
    bold: pygame.font.Font
    title: pygame.font.Font
    small: pygame.font.Font


@dataclass
class Button:
    rect: pygame.Rect
    label: str
    accent: bool = False

    def draw(self, surface: pygame.Surface, fonts: Fonts) -> None:
        mouse = pygame.mouse.get_pos()
        fill = GOLD if self.accent else PANEL_LIGHT
        border = (110, 118, 112) if self.rect.collidepoint(mouse) else (80, 92, 95)
        if self.rect.collidepoint(mouse):
            fill = tuple(min(255, channel + 16) for channel in fill)

        pygame.draw.rect(surface, fill, self.rect, border_radius=10)
        pygame.draw.rect(surface, border, self.rect, 2, border_radius=10)

        color = (18, 18, 18) if self.accent else TEXT
        draw_text(surface, self.label, fonts.bold, color, self.rect.center, center=True)


def draw_text(
    surface: pygame.Surface,
    text: str,
    font: pygame.font.Font,
    color: tuple[int, int, int],
    position: tuple[int, int],
    *,
    center: bool = False,
) -> None:
    rendered = font.render(text, True, color)
    rect = rendered.get_rect(center=position) if center else rendered.get_rect(topleft=position)
    surface.blit(rendered, rect)


def draw_wrapped_text(
    surface: pygame.Surface,
    text: str,
    font: pygame.font.Font,
    color: tuple[int, int, int],
    x: int,
    y: int,
    width: int,
    line_height: int,
) -> int:
    words = text.split()
    line = ""
    for word in words:
        candidate = f"{line} {word}".strip()
        if font.size(candidate)[0] > width and line:
            draw_text(surface, line, font, color, (x, y))
            y += line_height
            line = word
        else:
            line = candidate
    if line:
        draw_text(surface, line, font, color, (x, y))
        y += line_height
    return y


class App:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Morabaraba Magic")

        self.surface = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.fonts = Fonts(
            regular=pygame.font.SysFont("segoeui", 20),
            bold=pygame.font.SysFont("segoeui", 21, bold=True),
            title=pygame.font.SysFont("georgia", 42, bold=True),
            small=pygame.font.SysFont("segoeui", 16),
        )
        self.game = MorabarabaGame()
        self.screen = "menu"
        self.pending_mode = GameMode.COMPUTER
        self.board_choice = 0
        self.ai_wait_started_at: int | None = None
        self.rng = random.Random()
        self.play_board_rect = pygame.Rect(32, 50, 660, 660)

    def run(self) -> None:
        while True:
            self.clock.tick(FPS)
            controls = self._draw_current_screen()
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._quit()
                    return
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.screen = "menu"
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self._handle_click(event.pos, controls)

            if self.screen == "game":
                self._run_ai_turn()

    def _draw_current_screen(self) -> dict[str, object]:
        if self.screen == "menu":
            return self._draw_menu()
        if self.screen == "choose":
            return self._draw_board_choice()
        if self.screen == "rules":
            return self._draw_rules()
        return self._draw_game()

    def _draw_menu(self) -> dict[str, object]:
        self.surface.fill(BACKGROUND)
        draw_text(
            self.surface,
            "MORABARABA MAGIC",
            self.fonts.title,
            GOLD,
            (WIDTH // 2, 105),
            center=True,
        )
        draw_text(
            self.surface,
            "Traditional strategy with Koti and 24-point Morabaraba boards.",
            self.fonts.regular,
            MUTED,
            (WIDTH // 2, 174),
            center=True,
        )

        buttons = [
            Button(pygame.Rect(WIDTH // 2 - 175, 290 + index * 72, 350, 56), label, index == 0)
            for index, label in enumerate(
                ["Play vs Computer", "Two Players", "How to Play", "Quit"]
            )
        ]
        for button in buttons:
            button.draw(self.surface, self.fonts)
        return {"buttons": buttons}

    def _draw_board_choice(self) -> dict[str, object]:
        self.surface.fill(BACKGROUND)
        draw_text(
            self.surface,
            "Choose Your Board",
            self.fonts.title,
            GOLD,
            (WIDTH // 2, 70),
            center=True,
        )

        cards = [pygame.Rect(45 + index * 380, 170, 330, 410) for index in range(3)]
        for index, (layout, rect) in enumerate(zip(BOARDS, cards)):
            pygame.draw.rect(self.surface, PANEL, rect, border_radius=14)
            pygame.draw.rect(
                self.surface,
                GOLD if index == self.board_choice else (75, 85, 88),
                rect,
                4 if index == self.board_choice else 2,
                border_radius=14,
            )
            self._draw_board_preview(layout, pygame.Rect(rect.x + 25, rect.y + 25, 280, 250))
            draw_text(self.surface, layout.name, self.fonts.bold, TEXT, (rect.x + 24, rect.y + 300))
            draw_text(self.surface, layout.subtitle, self.fonts.regular, MUTED, (rect.x + 24, rect.y + 334))
            draw_wrapped_text(
                self.surface,
                layout.description,
                self.fonts.small,
                GOLD,
                rect.x + 24,
                rect.y + 367,
                276,
                20,
            )

        back = Button(pygame.Rect(45, 640, 150, 52), "Back")
        go = Button(pygame.Rect(WIDTH // 2 - 170, 640, 340, 52), "Continue", True)
        back.draw(self.surface, self.fonts)
        go.draw(self.surface, self.fonts)
        return {"cards": cards, "back": back, "continue": go}

    def _draw_rules(self) -> dict[str, object]:
        self.surface.fill(BACKGROUND)
        draw_text(self.surface, "How to Play", self.fonts.title, GOLD, (60, 50))
        lines = [
            "Each player starts with 12 cows. Red always moves first.",
            "Placement: players alternate placing cows on empty points.",
            "Mill: three cows on a valid board line. A new mill earns a capture.",
            "Movement: after all cows are placed, move to adjacent empty points.",
            "Flying: when a player has exactly three cows left, they may move to any empty point.",
            "Traditional 24-point board: cows in mills are protected unless all opponent cows are in mills.",
            "Koti 25-point board: the centre is active, blocking immediate mills is mandatory, and any cow may be captured.",
            "Win by reducing the opponent to two cows or by blocking all legal moves after placement.",
        ]
        y = 138
        for line in lines:
            y = draw_wrapped_text(self.surface, f"- {line}", self.fonts.regular, TEXT, 80, y, 1000, 39)

        back = Button(pygame.Rect(60, 660, 150, 50), "Back", True)
        back.draw(self.surface, self.fonts)
        return {"back": back}

    def _draw_game(self) -> dict[str, object]:
        self.surface.fill(BACKGROUND)
        self._draw_board()
        self._draw_status_panel()

        new_game = Button(pygame.Rect(775, 630, 150, 45), "New Game", True)
        boards = Button(pygame.Rect(945, 630, 150, 45), "Boards")
        new_game.draw(self.surface, self.fonts)
        boards.draw(self.surface, self.fonts)

        if self.game.winner:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 170))
            self.surface.blit(overlay, (0, 0))
            draw_text(
                self.surface,
                f"{PLAYER_NAMES[self.game.winner]} wins!",
                self.fonts.title,
                GOLD,
                (WIDTH // 2, HEIGHT // 2),
                center=True,
            )

        return {"new_game": new_game, "boards": boards}

    def _draw_board(self) -> None:
        pygame.draw.rect(self.surface, BOARD_FILL, self.play_board_rect, border_radius=12)
        pygame.draw.rect(self.surface, (180, 155, 102), self.play_board_rect, 3, border_radius=12)

        legal_destinations = self.game.legal_destinations()
        capture_targets = (
            set(capture_options(self.game.layout, self.game.board, opponent(self.game.turn)))
            if self.game.capture_pending
            else set()
        )

        for start, end in self.game.layout.edges:
            pygame.draw.line(
                self.surface,
                BOARD_LINE,
                self._point_position(start),
                self._point_position(end),
                4,
            )

        for index in range(self.game.layout.point_count):
            point = self._point_position(index)
            radius = 10 if index in legal_destinations else 8
            color = GOLD if index in legal_destinations else BOARD_LINE
            pygame.draw.circle(self.surface, color, point, radius)

        if self.game.selected is not None:
            pygame.draw.circle(self.surface, GOLD, self._point_position(self.game.selected), 30, 4)

        for index in capture_targets:
            pygame.draw.circle(self.surface, GOLD, self._point_position(index), 31, 4)

        for index, piece in enumerate(self.game.board):
            if piece == EMPTY:
                continue
            x, y = self._point_position(index)
            color = RED if piece == Player.RED else BLUE
            pygame.draw.circle(self.surface, (70, 50, 35), (x + 4, y + 5), 24)
            pygame.draw.circle(self.surface, color, (x, y), 22)
            pygame.draw.circle(self.surface, WHITE, (x, y), 22, 2)

    def _draw_status_panel(self) -> None:
        panel_rect = pygame.Rect(750, 45, 390, 665)
        pygame.draw.rect(self.surface, PANEL, panel_rect, border_radius=16)
        pygame.draw.rect(self.surface, (73, 83, 86), panel_rect, 2, border_radius=16)

        draw_text(self.surface, "Morabaraba Magic", self.fonts.bold, GOLD, (775, 70))
        draw_text(self.surface, self.game.layout.subtitle, self.fonts.regular, MUTED, (775, 104))
        draw_wrapped_text(self.surface, self.game.layout.description, self.fonts.small, MUTED, 775, 132, 330, 20)

        y = 182
        for player in (Player.RED, Player.BLUE):
            name = PLAYER_NAMES[player]
            if self.game.mode == GameMode.COMPUTER and player == Player.BLUE:
                name += " (Computer)"
            draw_text(self.surface, name, self.fonts.bold, TEXT, (775, y))
            draw_text(
                self.surface,
                f"On board: {count_pieces(self.game.board, player)}   In hand: {self.game.hand[player]}",
                self.fonts.regular,
                MUTED,
                (775, y + 31),
            )
            y += 88

        draw_text(self.surface, "TURN", self.fonts.small, MUTED, (775, 352))
        draw_text(self.surface, PLAYER_NAMES[self.game.turn], self.fonts.bold, GOLD, (775, 376))
        draw_text(self.surface, "PHASE", self.fonts.small, MUTED, (945, 352))
        draw_text(self.surface, self.game.phase(), self.fonts.bold, GOLD, (945, 376))

        draw_text(self.surface, "STATUS", self.fonts.small, MUTED, (775, 445))
        draw_wrapped_text(self.surface, self.game.message, self.fonts.regular, TEXT, 775, 474, 330, 26)

        progress = STARTING_COWS * 2 - self.game.hand[Player.RED] - self.game.hand[Player.BLUE]
        pygame.draw.rect(self.surface, (19, 26, 29), pygame.Rect(775, 580, 320, 10), border_radius=8)
        pygame.draw.rect(
            self.surface,
            GOLD,
            pygame.Rect(775, 580, int(320 * progress / (STARTING_COWS * 2)), 10),
            border_radius=8,
        )
        draw_text(self.surface, "Placement progress", self.fonts.small, MUTED, (775, 598))

    def _draw_board_preview(self, layout: BoardLayout, rect: pygame.Rect) -> None:
        pygame.draw.rect(self.surface, BOARD_FILL, rect, border_radius=8)
        pygame.draw.rect(self.surface, (185, 156, 96), rect, 2, border_radius=8)

        def point_position(index: int) -> tuple[int, int]:
            grid_x, grid_y = layout.points[index]
            margin = rect.width * layout.margin + 12
            usable = rect.width - 2 * margin
            return (
                int(rect.x + margin + grid_x / 6 * usable),
                int(rect.y + margin + grid_y / 6 * usable),
            )

        for start, end in layout.edges:
            pygame.draw.line(self.surface, BOARD_LINE, point_position(start), point_position(end), 2)
        for index in range(layout.point_count):
            pygame.draw.circle(self.surface, BOARD_LINE, point_position(index), 4)

    def _handle_click(self, position: tuple[int, int], controls: dict[str, object]) -> None:
        if self.screen == "menu":
            self._handle_menu_click(position, controls)
        elif self.screen == "choose":
            self._handle_board_choice_click(position, controls)
        elif self.screen == "rules":
            if controls["back"].rect.collidepoint(position):
                self.screen = "menu"
        elif self.screen == "game":
            self._handle_game_click(position, controls)

    def _handle_menu_click(self, position: tuple[int, int], controls: dict[str, object]) -> None:
        buttons = controls["buttons"]
        for index, button in enumerate(buttons):
            if not button.rect.collidepoint(position):
                continue
            if index == 0:
                self.pending_mode = GameMode.COMPUTER
                self.screen = "choose"
            elif index == 1:
                self.pending_mode = GameMode.LOCAL
                self.screen = "choose"
            elif index == 2:
                self.screen = "rules"
            else:
                self._quit()

    def _handle_board_choice_click(self, position: tuple[int, int], controls: dict[str, object]) -> None:
        for index, rect in enumerate(controls["cards"]):
            if rect.collidepoint(position):
                self.board_choice = index

        if controls["back"].rect.collidepoint(position):
            self.screen = "menu"
        if controls["continue"].rect.collidepoint(position):
            self.game.start(self.pending_mode, BOARDS[self.board_choice])
            self.ai_wait_started_at = None
            self.screen = "game"

    def _handle_game_click(self, position: tuple[int, int], controls: dict[str, object]) -> None:
        if controls["new_game"].rect.collidepoint(position):
            self.game.start(self.game.mode, self.game.layout)
            self.ai_wait_started_at = None
            return
        if controls["boards"].rect.collidepoint(position):
            self.pending_mode = self.game.mode
            self.screen = "choose"
            return
        self.game.choose_position(self._hit_test_point(position))

    def _run_ai_turn(self) -> None:
        if not self.game.is_computer_turn or self.game.winner:
            self.ai_wait_started_at = None
            return

        now = pygame.time.get_ticks()
        if self.ai_wait_started_at is None:
            self.ai_wait_started_at = now
            return
        if now - self.ai_wait_started_at < AI_DELAY_MS:
            return

        if self.game.capture_pending:
            victim = choose_capture(self.game.layout, self.game.board, Player.RED, self.rng)
            if victim is not None:
                self.game.capture(victim)
            self.ai_wait_started_at = None
            return

        move = choose_move(self.game.layout, self.game.board, self.game.hand, Player.BLUE, self.rng)
        if move is None:
            self.game.winner = Player.RED
            self.game.message = "Red wins by blocking all legal moves."
            self.ai_wait_started_at = None
            return

        source, destination = move
        if source is None:
            self.game.place(destination)
        else:
            self.game.move(source, destination)
        self.ai_wait_started_at = now

    def _point_position(self, index: int) -> tuple[int, int]:
        grid_x, grid_y = self.game.layout.points[index]
        rect = self.play_board_rect.inflate(-42, -42)
        margin = rect.width * self.game.layout.margin
        usable = rect.width - 2 * margin
        return (
            int(rect.x + margin + grid_x / 6 * usable),
            int(rect.y + margin + grid_y / 6 * usable),
        )

    def _hit_test_point(self, position: tuple[int, int]) -> int | None:
        closest_point = None
        closest_distance = 32.0
        for index in range(self.game.layout.point_count):
            x, y = self._point_position(index)
            distance = math.hypot(position[0] - x, position[1] - y)
            if distance < closest_distance:
                closest_point = index
                closest_distance = distance
        return closest_point

    def _quit(self) -> None:
        pygame.quit()
        raise SystemExit
