import asyncio
import random
from rich.segment import Segment
from rich.style import Style
from textual import events
from textual.geometry import Offset, Region
from textual.reactive import var
from textual.strip import Strip
from textual.widget import Widget

from . import Operation


class Canvas(Widget):
    COMPONENT_CLASSES: set[str] = {
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

    CANVAS_OFFSET: int = 2

    refresh_interval: float = 0.5

    MAX_CANVAS_HEIGHT: int = 100
    MAX_CANVAS_WIDTH: int = 100

    # Brush size settings
    brush_size: int = 1
    MAX_BRUSH_SIZE: int = 10
    MIN_BRUSH_SIZE: int = 1

    canvas_height: int = 20
    canvas_width: int = 20
    cursor_square: var[Offset] = var(Offset(0, 0))
    running: bool = False
    x: int = -1
    y: int = -1
    cursor_colour: str = "black"

    def __init__(self, width: int = 20, height: int = 20, speed: float = 0.5, brush_size: int = 1) -> None:
        super().__init__()

        self.canvas_width = width
        self.canvas_height = height
        self.refresh_interval = speed
        self.brush_size = max(min(brush_size, self.MAX_BRUSH_SIZE), self.MIN_BRUSH_SIZE)
        self.mouse_captured = False

        self.matrix: list[list[int]] = [
            [0 for _ in range(self.canvas_width + 1)] for _ in range(self.canvas_height + 1)
        ]

    def clear(self) -> None:
        self.matrix = [[0 for _ in range(self.canvas_width + 1)] for _ in range(self.canvas_height + 1)]
        self.refresh()

    # step methods
    def step(self) -> None:
        self.matrix = self.get_next_generation()
        self.refresh()

    async def toggle(self):
        self.running = not self.running
        while self.running:
            await asyncio.sleep(self.refresh_interval)
            self.step()

    def get_neighbours(self, x: int, y: int) -> list[int]:
        neighbours = []
        for i in range(-1, 2):
            for j in range(-1, 2):
                if i == j == 0:
                    continue
                neighbours.append(self.matrix[(y + i) % self.canvas_height][(x + j) % self.canvas_width])
        return neighbours

    def get_next_generation(self) -> list[list[int]]:
        new_canvas_matrix = [[0 for _ in range(self.canvas_width + 1)] for _ in range(self.canvas_height + 1)]
        for y in range(self.canvas_height):
            for x in range(self.canvas_width):
                neighbours = self.get_neighbours(x, y)
                if self.matrix[y][x] == 1:
                    if 2 <= sum(neighbours) <= 3:
                        new_canvas_matrix[y][x] = 1
                else:
                    if sum(neighbours) == 3:
                        new_canvas_matrix[y][x] = 1
        return new_canvas_matrix

    def random(self) -> None:
        for y in range(self.canvas_height):
            for x in range(self.canvas_width):
                self.matrix[y][x] = random.randint(0, 1)
        self.refresh()

    def extend_canvas(self) -> list[list[int]]:
        matirx = [[0 for _ in range(self.canvas_width + 1)] for _ in range(self.canvas_height + 1)]
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
                if self.canvas_width >= self.MAX_CANVAS_WIDTH:
                    return

                self.canvas_width += amount
            elif operation.value == "decrease":
                if self.canvas_width <= 10:
                    return

                self.canvas_width -= amount
            else:
                raise RuntimeError(f"Invalid operation: {operation}")

        if vertically:
            if operation.value == "increase":
                if self.canvas_height >= self.MAX_CANVAS_HEIGHT:
                    return

                self.canvas_height += amount
            elif operation.value == "decrease":
                if self.canvas_height <= 10:
                    return

                self.canvas_height -= amount
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
        current_cursor = Offset(
            mouse_position.x // self.ROW_HEIGHT,
            mouse_position.y // int(self.ROW_HEIGHT / 2),
        )

        # If the cursor position has changed
        if current_cursor != self.cursor_square:
            self.cursor_square = current_cursor

            # If mouse is captured (dragging), toggle cells
            if self.mouse_captured and event.button == 1:  # Left mouse button
                self.toggle_cell(self.cursor_square.x, self.cursor_square.y)

        # only update the square that aren't out of range
        self.cursor_colour = "black"
        if len(self.matrix) > self.cursor_square.y and len(self.matrix[self.cursor_square.y]) > self.cursor_square.x:
            self.cursor_colour = "black" if self.matrix[self.cursor_square.y][self.cursor_square.x] == 0 else "white"

    def toggle_cell(self, x: int, y: int) -> None:
        """Toggle the state of a cell at the given coordinates."""
        if len(self.matrix) > y and len(self.matrix[y]) > x:
            self.matrix[y][x] ^= 1
            self.refresh(self.get_square_region(Offset(x, y)))

    def on_click(self, event: events.Click) -> None:
        """Called when the mouse is clicked."""
        mouse_position = event.offset + self.scroll_offset
        self.cursor_square = Offset(
            mouse_position.x // self.ROW_HEIGHT,
            mouse_position.y // int(self.ROW_HEIGHT / 2),
        )
        self.x = self.cursor_square.x
        self.y = self.cursor_square.y

        # toggle the square
        self.toggle_cell(self.x, self.y)

        # Start tracking the drag
        self.capture_mouse()
        self.mouse_captured = True

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

    def on_mouse_up(self, event: events.MouseUp) -> None:
        """Called when the mouse button is released."""
        self.release_mouse()
        self.mouse_captured = False

    def increase_brush_size(self) -> None:
        """Increase the brush size, respecting the maximum limit."""
        if self.brush_size < self.MAX_BRUSH_SIZE:
            self.brush_size += 1

    def decrease_brush_size(self) -> None:
        """Decrease the brush size, respecting the minimum limit."""
        if self.brush_size > self.MIN_BRUSH_SIZE:
            self.brush_size -= 1

    def render_line(self, y: int) -> Strip:
        """Render a line of the widget. y is relative to the top of the widget."""
        row_index = y // int(self.ROW_HEIGHT / 2)

        if row_index >= self.canvas_height:
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
            Segment(" " * self.ROW_HEIGHT, get_square_style(column, row_index)) for column in range(self.canvas_width)
        ]
        strip = Strip(segments)
        return strip
