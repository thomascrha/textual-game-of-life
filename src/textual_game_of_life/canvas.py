import asyncio
import random
import time
from rich.segment import Segment
from rich.style import Style
from textual import events
from textual.geometry import Offset, Region
from textual.reactive import var
from textual.strip import Strip
from textual.widget import Widget
from typing_extensions import override
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

    # Message display settings
    message: str = ""
    message_visible: bool = False
    message_timeout: float = 3.0  # Default timeout in seconds
    message_timestamp: float = 0.0
    message_style: Style = Style(color="bright_white", bgcolor="dark_blue", bold=True, italic=True)
    message_task: asyncio.Task[None] | None = None  # Track the current message timeout task

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
        self.mouse_captured: bool = True

        self.matrix: list[list[int]] = [
            [0 for _ in range(self.canvas_width + 1)] for _ in range(self.canvas_height + 1)
        ]

        self.message = ""
        self.message_visible = False
        self.message_timestamp = 0.0
        self.message_timeout = 3.0  # Default timeout in seconds
        self.message_task = None

    def display_message(self, text: str, timeout: float = 3.0) -> None:
        if self.message_task and not self.message_task.done():
            _ = self.message_task.cancel()

        self.message = text
        self.message_visible = True
        self.message_timestamp = time.time()
        self.message_timeout = timeout
        _ = self.refresh()  # Force refresh to show the message

        # Schedule the message removal and track the task
        try:
            # Create and store the task for auto-timeout
            self.message_task = asyncio.create_task(self._message_timeout_task())
        except RuntimeError:
            # No running event loop (likely in test environment)
            # For test environments, just mark message as not visible after timeout
            # to avoid the unawaited coroutine warning
            self.message_visible = False

    async def _message_timeout_task(self) -> None:
        try:
            await asyncio.sleep(self.message_timeout)
            if self.message_visible:
                self.message_visible = False
                _ = self.refresh()
        except asyncio.CancelledError:
            # Task was cancelled, likely because a new message is being displayed
            pass

    def clear_message(self) -> None:
        if self.message_visible:
            # Cancel any existing message timeout task
            if self.message_task and not self.message_task.done():
                try:
                    _ = self.message_task.cancel()
                except (RuntimeError, AttributeError):
                    # No running event loop or task is None
                    pass

            self.message_visible = False
            _ = self.refresh()

    def clear(self) -> None:
        self.matrix = [[0 for _ in range(self.canvas_width + 1)] for _ in range(self.canvas_height + 1)]
        _ = self.refresh()

    def step(self) -> None:
        self.matrix = self.get_next_generation()
        _ = self.refresh()

    async def toggle(self):
        self.running = not self.running
        # Only enter the animation loop if we're in a real event loop context
        # This prevents the "coroutine was never awaited" warning in tests
        if self.running and asyncio.get_event_loop().is_running():
            while self.running:
                await asyncio.sleep(self.refresh_interval)
                self.step()

    def get_neighbours(self, x: int, y: int) -> list[int]:
        neighbours: list[int] = []
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
        _ = self.refresh()

    def add_random_glider(self) -> None:
        # Random position (leaving room for the 3x3 glider pattern)
        x = random.randint(0, self.canvas_width - 3)
        y = random.randint(0, self.canvas_height - 3)

        # Clear the area for the glider
        for i in range(3):
            for j in range(3):
                if y + i < self.canvas_height and x + j < self.canvas_width:
                    self.matrix[y + i][x + j] = 0

        # Standard glider pattern (will move southeast)
        # .O.
        # ..O
        # OOO
        if y < self.canvas_height and x + 1 < self.canvas_width:
            self.matrix[y][x + 1] = 1  # Top middle
        if y + 1 < self.canvas_height and x + 2 < self.canvas_width:
            self.matrix[y + 1][x + 2] = 1  # Middle right
        if y + 2 < self.canvas_height:
            for j in range(3):
                if x + j < self.canvas_width:
                    self.matrix[y + 2][x + j] = 1  # Bottom row

        _ = self.refresh()

    def add_random_pulsar(self) -> None:
        # Pulsar requires a 17x17 area (13x13 with 2-cell border all around)
        pulsar_size = 17

        # Check if canvas is big enough
        if self.canvas_width < pulsar_size or self.canvas_height < pulsar_size:
            return  # Canvas too small for pulsar

        # Random position (leaving room for the pulsar pattern with border)
        x = random.randint(0, self.canvas_width - pulsar_size)
        y = random.randint(0, self.canvas_height - pulsar_size)

        # Clear the area for the pulsar (including border)
        for i in range(pulsar_size):
            for j in range(pulsar_size):
                if y + i < self.canvas_height and x + j < self.canvas_width:
                    self.matrix[y + i][x + j] = 0

        # Add 2-cell buffer to allow pattern to oscillate properly
        buffer = 2
        x += buffer
        y += buffer

        # The correct pulsar pattern has 4 sets of 3-cell segments:
        # - Horizontal segments at rows 2, 7, 9, 14 with columns 4-6 and 10-12
        # - Vertical segments at columns 2, 7, 9, 14 with rows 4-6 and 10-12

        # Create full coordinates list for all cells in the pulsar
        pulsar_cells: list[tuple[int, int]] = []

        # Top and bottom horizontal bars
        for row in [0, 5, 7, 12]:
            for col in range(2, 5):
                pulsar_cells.append((row, col))
                pulsar_cells.append((row, col + 6))

        # Left and right vertical bars
        for col in [0, 5, 7, 12]:
            for row in range(2, 5):
                pulsar_cells.append((row, col))
                pulsar_cells.append((row + 6, col))

        # Place all cells of the pulsar
        for row, col in pulsar_cells:
            if y + row < self.canvas_height and x + col < self.canvas_width:
                self.matrix[y + row][x + col] = 1

        _ = self.refresh()

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
            try:
                _ = asyncio.create_task(self.toggle())
            except RuntimeError:
                # No running event loop (likely in test environment)
                self.running = not self.running

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
        _ = self.refresh()

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
        if len(self.matrix) > y and len(self.matrix[y]) > x:
            self.matrix[y][x] ^= 1
            _ = self.refresh(self.get_square_region(Offset(x, y)))

    def on_click(self, event: events.Click) -> None:
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
        _ = self.refresh(self.get_square_region(previous_square))

        # Refresh the new cursor square
        _ = self.refresh(self.get_square_region(cursor_square))

    def on_mouse_up(self, _: events.MouseUp) -> None:
        self.release_mouse()
        self.mouse_captured = False

    def increase_brush_size(self) -> None:
        if self.brush_size < self.MAX_BRUSH_SIZE:
            self.brush_size += 1

    def decrease_brush_size(self) -> None:
        if self.brush_size > self.MIN_BRUSH_SIZE:
            self.brush_size -= 1

    @override
    def render_line(self, y: int) -> Strip:
        row_index = y // int(self.ROW_HEIGHT / 2)

        # Check if this line should display the message
        if self.message_visible and y == self.size.height - 2:  # Position at the bottom
            # Create a full-width message with padding
            padding = " " * 2  # Add some padding at the start
            return Strip([Segment(f"{padding}{self.message}", self.message_style)])

        # Don't render canvas content for lines beyond the canvas height
        if row_index >= self.canvas_height:
            return Strip.blank(self.size.width)

        # Normal canvas rendering
        def get_square_style(column: int, row: int) -> Style:
            if self.cursor_square == Offset(column, row):
                square_style = self.cursor
            else:
                square_style = self.black
                # only update the square that aren't out of range
                if len(self.matrix) > row and len(self.matrix[row]) > column:
                    square_style = self.black if self.matrix[row][column] == 1 else self.white

            return square_style

        segments = [
            Segment(" " * self.ROW_HEIGHT, get_square_style(column, row_index)) for column in range(self.canvas_width)
        ]
        strip = Strip(segments)
        return strip
