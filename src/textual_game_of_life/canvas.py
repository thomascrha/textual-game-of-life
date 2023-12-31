import asyncio
import random
from typing import List
from rich.segment import Segment
from rich.style import Style
from textual import events
from textual.geometry import Offset, Region
from textual.reactive import var
from textual.strip import Strip
from textual.widget import Widget

from . import Operation


class Canvas(Widget):
    COMPONENT_CLASSES: set = {
        "canvas--white-square",
        "canvas--black-square",
        "canvas--cursor-square-white",
        "canvas--cursor-square-black",
    }

    DEFAULT_CSS: str = """
    Canvas .canvas--white-square {
        background: #FFFFFF;
    }
    Canvas .canvas--black-square {
        background: #000000;
    }
    Canvas > .canvas--cursor-square-white {
        background: #FFFFFF;
    }
    Canvas > .canvas--cursor-square-black {
        background: #000000;
    }
    """
    ROW_HEIGHT: int = 2
    CANVAS_HEIGHT: int = 20
    CANVAS_WIDTH: int = 20

    CANVAS_OFFSET: int = 2

    REFRESH_INTERVAL: float = 0.5

    MAX_CANVAS_HEIGHT: int = 100
    MAX_CANVAS_WIDTH: int = 100

    cursor_square = var(Offset(0, 0))
    running: bool = False
    x: int = -1
    y: int = -1
    cursor_colour = "black"

    def __init__(self) -> None:
        super().__init__()
        self.matrix: List[List[int]] = [
            [0 for _ in range(self.CANVAS_WIDTH + 1)] for _ in range(self.CANVAS_HEIGHT + 1)
        ]

    def clear(self) -> None:
        self.matrix = [[0 for _ in range(self.CANVAS_WIDTH + 1)] for _ in range(self.CANVAS_HEIGHT + 1)]
        self.refresh()

    # step methods
    def step(self) -> None:
        self.matrix = self.get_next_generation()
        self.refresh()

    async def toggle(self):
        self.running = not self.running
        while self.running:
            await asyncio.sleep(self.REFRESH_INTERVAL)
            self.step()

    def get_neighbours(self, x: int, y: int) -> list[int]:
        neighbours = []
        for i in range(-1, 2):
            for j in range(-1, 2):
                if i == j == 0:
                    continue
                neighbours.append(self.matrix[(y + i) % self.CANVAS_HEIGHT][(x + j) % self.CANVAS_WIDTH])
        return neighbours

    def get_next_generation(self) -> list[list[int]]:
        new_canvas_matrix = [[0 for _ in range(self.CANVAS_WIDTH + 1)] for _ in range(self.CANVAS_HEIGHT + 1)]
        for y in range(self.CANVAS_HEIGHT):
            for x in range(self.CANVAS_WIDTH):
                neighbours = self.get_neighbours(x, y)
                if self.matrix[y][x] == 1:
                    if 2 <= sum(neighbours) <= 3:
                        new_canvas_matrix[y][x] = 1
                else:
                    if sum(neighbours) == 3:
                        new_canvas_matrix[y][x] = 1
        return new_canvas_matrix

    def random(self) -> None:
        for y in range(self.CANVAS_HEIGHT):
            for x in range(self.CANVAS_WIDTH):
                self.matrix[y][x] = random.randint(0, 1)
        self.refresh()

    def extend_canvas(self) -> List[List[int]]:
        matirx = [[0 for _ in range(self.CANVAS_WIDTH + 1)] for _ in range(self.CANVAS_HEIGHT + 1)]
        for y, _ in enumerate(self.matrix):
            for x, value in enumerate(self.matrix[y]):
                if len(matirx) > y and len(matirx[y]) > x:
                    matirx[y][x] = value
        return matirx

    def alter_canvas_size(
        self, operation: Operation, horizontally: bool = True, vertically: bool = True, *, amount: int = 10
    ) -> None:
        if self.running:
            asyncio.create_task(self.toggle())

        if horizontally:
            if operation.value == "increase":
                if self.CANVAS_WIDTH >= self.MAX_CANVAS_WIDTH:
                    return

                self.CANVAS_WIDTH += amount
            elif operation.value == "decrease":
                if self.CANVAS_WIDTH <= 10:
                    return

                self.CANVAS_WIDTH -= amount
            else:
                raise RuntimeError(f"Invalid operation: {operation}")

        if vertically:
            if operation.value == "increase":
                if self.CANVAS_HEIGHT >= self.MAX_CANVAS_HEIGHT:
                    return

                self.CANVAS_HEIGHT += amount
            elif operation.value == "decrease":
                if self.CANVAS_HEIGHT <= 10:
                    return

                self.CANVAS_HEIGHT -= amount
            else:
                raise RuntimeError(f"Invalid operation: {operation}")

        self.matrix = self.extend_canvas()
        self.refresh()

    @property
    def white(self) -> Style:
        return self.get_component_rich_style("canvas--white-square")

    @property
    def black(self) -> Style:
        return self.get_component_rich_style("canvas--black-square")

    @property
    def cursor(self) -> Style:
        return self.get_component_rich_style(f"canvas--cursor-square-{self.cursor_colour}")

    def on_mouse_move(self, event: events.MouseMove) -> None:
        mouse_position = event.offset + self.scroll_offset
        self.cursor_square = Offset(
            mouse_position.x // self.ROW_HEIGHT,
            mouse_position.y // int(self.ROW_HEIGHT / 2),
        )

        # only update the scauare that aren't out of range
        self.cursor_colour = "black"
        if len(self.matrix) > self.cursor_square.y and len(self.matrix[self.cursor_square.y]) > self.cursor_square.x:
            self.cursor_colour = "black" if self.matrix[self.cursor_square.y][self.cursor_square.x] == 0 else "white"

    def on_click(self, event: events.Click) -> None:
        mouse_position = event.offset + self.scroll_offset
        self.cursor_square = Offset(
            mouse_position.x // self.ROW_HEIGHT,
            mouse_position.y // int(self.ROW_HEIGHT / 2),
        )
        self.x = self.cursor_square.x
        self.y = self.cursor_square.y

        # toggle the square
        if len(self.matrix) > self.y and len(self.matrix[self.y]) > self.x:
            self.matrix[self.y][self.x] ^= 1

        self.refresh(self.get_square_region(self.cursor_square))

    def get_square_region(self, square_offset: Offset) -> Region:
        """Get region relative to widget from square coordinate."""
        x, y = square_offset
        region = Region(
            x * self.ROW_HEIGHT,
            y * int(self.ROW_HEIGHT / 2),
            self.ROW_HEIGHT,
            int(self.ROW_HEIGHT / 2),
        )
        # Move the region in to the widgets frame of reference
        region = region.translate(-self.scroll_offset)
        return region

    def watch_cursor_square(self, previous_square: Offset, cursor_square: Offset) -> None:
        """Called when the cursor square changes."""
        # Refresh the previous cursor square
        self.refresh(self.get_square_region(previous_square))

        # Refresh the new cursor square
        self.refresh(self.get_square_region(cursor_square))

    def render_line(self, y: int) -> Strip:
        """Render a line of the widget. y is relative to the top of the widget."""
        row_index = y // int(self.ROW_HEIGHT / 2)

        if row_index >= self.CANVAS_HEIGHT:
            return Strip.blank(self.size.width)

        def get_square_style(column: int, row: int) -> Style:
            """Get the cursor style at the given position on the checkerboard."""
            if self.cursor_square == Offset(column, row):
                square_style = self.cursor
            else:
                square_style = self.black
                # only update the scauare that aren't out of range
                if len(self.matrix) > row and len(self.matrix[row]) > column:
                    square_style = self.black if self.matrix[row][column] == 1 else self.white

            return square_style

        segments = [
            Segment(" " * self.ROW_HEIGHT, get_square_style(column, row_index)) for column in range(self.CANVAS_WIDTH)
        ]
        strip = Strip(segments)
        return strip
