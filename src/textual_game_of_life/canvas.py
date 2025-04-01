import asyncio
import numpy as np
import random
import time
from rich.segment import Segment
from rich.style import Style
from textual import events
from textual.geometry import Offset, Region
from textual.message import Message
from textual.reactive import var
from textual.strip import Strip
from textual.widget import Widget
from typing_extensions import override
from . import Operation


class Canvas(Widget):
    class MessageRequest(Message):
        """Message sent when the canvas wants to display a notification."""

        def __init__(self, message: str, timeout: float = 2.0) -> None:
            self.message = message
            self.timeout = timeout
            super().__init__()

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

        # Precomputed max size constraints
        self.max_width_by_term = 0
        self.max_height_by_term = 0
        self.effective_max_width = 0  # Min of terminal constraint and MAX_CANVAS_WIDTH
        self.effective_max_height = 0  # Min of terminal constraint and MAX_CANVAS_HEIGHT

        self.matrix = np.zeros((self.canvas_height + 1, self.canvas_width + 1), dtype=np.int8)

        self.message = ""
        self.message_visible = False
        self.message_timestamp = 0.0
        self.message_timeout = 3.0  # Default timeout in seconds
        self.message_task = None

    def request_message(self, text: str, timeout: float = 2.0) -> None:
        """Request that a message be displayed by the parent application."""
        try:
            self.post_message(self.MessageRequest(text, timeout))
        except Exception:
            # In test environments or when no parent is available,
            # just set the message locally without posting
            self.message = text
            self.message_visible = True
            self.message_timestamp = time.time()
            self.message_timeout = timeout

    def display_message(self, text: str, timeout: float = 3.0) -> None:
        """Legacy method - now routes to request_message for compatibility."""
        self.request_message(text, timeout)

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
        self.matrix = np.zeros((self.canvas_height + 1, self.canvas_width + 1), dtype=np.int8)
        _ = self.refresh()

    def step(self) -> None:
        # Store old matrix to calculate changes
        old_matrix = self.matrix.copy()
        self.matrix = self.get_next_generation()

        # Find regions that changed
        changed = np.where(old_matrix[:self.canvas_height, :self.canvas_width] !=
                          self.matrix[:self.canvas_height, :self.canvas_width])

        # Only refresh if we have changes
        if len(changed[0]) > 0:
            # For larger changes, full refresh is more efficient
            if len(changed[0]) > (self.canvas_height * self.canvas_width) / 4:
                _ = self.refresh()
            else:
                # Refresh only the changed regions
                for y, x in zip(changed[0], changed[1]):
                    _ = self.refresh(self.get_square_region(Offset(x, y)))
        else:
            # No changes - could indicate a stable pattern
            pass

    async def toggle(self):
        self.running = not self.running
        # Only enter the animation loop if we're in a real event loop context
        # This prevents the "coroutine was never awaited" warning in tests
        if self.running and asyncio.get_event_loop().is_running():
            last_update = time.time()
            while self.running:
                now = time.time()
                elapsed = now - last_update

                # Ensure refresh_interval is never below the minimum threshold
                if self.refresh_interval < 0.1:
                    self.refresh_interval = 0.1

                # For fast speeds, compute multiple generations at once
                if self.refresh_interval == 0.1:
                    # Fixed batch size for maximum speed
                    batch_size = 3  # Use a reasonable fixed value instead of dynamic calculation
                    for _ in range(batch_size):
                        self.matrix = self.get_next_generation()
                    _ = self.refresh()
                else:
                    self.step()

                # Calculate time remaining to wait, with a minimum to prevent CPU overload
                elapsed = time.time() - now
                wait_time = max(0.01, self.refresh_interval - elapsed)
                await asyncio.sleep(wait_time)
                last_update = now

    def get_neighbours(self, x: int, y: int) -> np.ndarray:
        """Return the values of the 8 neighboring cells using NumPy slicing."""
        # Create the wrapped coordinates for the 3x3 neighborhood
        y_indices = (np.array([y-1, y, y+1])) % self.canvas_height
        x_indices = (np.array([x-1, x, x+1])) % self.canvas_width

        # Get the 3x3 neighborhood
        neighborhood = self.matrix[np.ix_(y_indices, x_indices)]

        # Set the center cell to 0 to exclude it
        neighborhood_copy = neighborhood.copy()
        neighborhood_copy[1, 1] = 0

        # Return the neighbors as a flattened array
        return neighborhood_copy.flatten()

    def get_next_generation(self) -> np.ndarray:
        """Calculate the next generation using NumPy vectorized operations."""
        # Create a padded matrix with wrap-around (toroidal) boundary conditions
        padded = np.pad(self.matrix[:self.canvas_height, :self.canvas_width],
                        ((1, 1), (1, 1)),
                        mode='wrap')

        # Count neighbors for all cells at once using sum of shifted arrays
        # This creates a sliding 3x3 window without explicit loops
        neighbors = np.zeros((self.canvas_height, self.canvas_width), dtype=np.int8)

        # Sum all 8 neighboring positions using slices
        for i in range(3):
            for j in range(3):
                if i == 1 and j == 1:  # Skip the center
                    continue
                neighbors += padded[i:i+self.canvas_height, j:j+self.canvas_width]

        # Create a new matrix based on Game of Life rules
        current_state = self.matrix[:self.canvas_height, :self.canvas_width]
        new_canvas_matrix = np.zeros((self.canvas_height + 1, self.canvas_width + 1), dtype=np.int8)

        # Apply Conway's Game of Life rules vectorized:
        # 1. Any live cell with 2 or 3 live neighbors survives
        # 2. Any dead cell with exactly 3 live neighbors becomes alive
        new_canvas_matrix[:self.canvas_height, :self.canvas_width] = (
            ((current_state == 1) & ((neighbors == 2) | (neighbors == 3))) |
            ((current_state == 0) & (neighbors == 3))
        ).astype(np.int8)

        return new_canvas_matrix

    def random(self) -> None:
        # Generate a random matrix using NumPy's vectorized random function
        self.matrix = np.random.randint(0, 2,
                                       (self.canvas_height + 1, self.canvas_width + 1),
                                       dtype=np.int8)
        _ = self.refresh()

    def add_random_glider(self) -> None:
        # Random position (leaving room for the 3x3 glider pattern)
        x = random.randint(0, self.canvas_width - 3)
        y = random.randint(0, self.canvas_height - 3)

        # Clear the area for the glider
        for i in range(3):
            for j in range(3):
                if y + i < self.canvas_height and x + j < self.canvas_width:
                    self.matrix[y + i, x + j] = 0

        # Standard glider pattern (will move southeast)
        # .O.
        # ..O
        # OOO
        if y < self.canvas_height and x + 1 < self.canvas_width:
            self.matrix[y, x + 1] = 1  # Top middle
        if y + 1 < self.canvas_height and x + 2 < self.canvas_width:
            self.matrix[y + 1, x + 2] = 1  # Middle right
        if y + 2 < self.canvas_height:
            for j in range(3):
                if x + j < self.canvas_width:
                    self.matrix[y + 2, x + j] = 1  # Bottom row

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
                    self.matrix[y + i, x + j] = 0

        # Define the correct pulsar pattern
        # This is a period-3 oscillator that requires precise positioning

        # The pattern's active cells (1-indexed relative to the pattern's top-left corner)
        # Format: (row, column)
        pulsar_pattern = [
            # Top section
            (3, 5), (3, 6), (3, 7), (3, 11), (3, 12), (3, 13),
            (5, 3), (6, 3), (7, 3), (5, 8), (6, 8), (7, 8), (5, 10), (6, 10), (7, 10), (5, 15), (6, 15), (7, 15),
            (8, 5), (8, 6), (8, 7), (8, 11), (8, 12), (8, 13),

            # Bottom section
            (10, 5), (10, 6), (10, 7), (10, 11), (10, 12), (10, 13),
            (11, 3), (12, 3), (13, 3), (11, 8), (12, 8), (13, 8), (11, 10), (12, 10), (13, 10), (11, 15), (12, 15), (13, 15),
            (15, 5), (15, 6), (15, 7), (15, 11), (15, 12), (15, 13)
        ]

        # Place the pulsar pattern onto the canvas
        for row, col in pulsar_pattern:
            if (y + row) < self.canvas_height and (x + col) < self.canvas_width:
                self.matrix[y + row, x + col] = 1

        _ = self.refresh()

    def extend_canvas(self) -> np.ndarray:
        # Create a new matrix with the new dimensions
        new_matrix = np.zeros((self.canvas_height + 1, self.canvas_width + 1), dtype=np.int8)

        # Copy over the existing data, limited by the smaller of the old and new dimensions
        old_height, old_width = self.matrix.shape
        copy_height = min(old_height, self.canvas_height + 1)
        copy_width = min(old_width, self.canvas_width + 1)

        new_matrix[:copy_height, :copy_width] = self.matrix[:copy_height, :copy_width]
        return new_matrix

    def update_size_constraints(self) -> None:
        """Update the maximum size constraints based on current terminal size."""
        # Get current terminal size
        term_width, term_height = self.size.width, self.size.height

        # Calculate max possible canvas dimensions based on terminal size
        # Each canvas cell takes ROW_HEIGHT horizontal characters and ROW_HEIGHT/2 vertical characters
        self.max_width_by_term = term_width // self.ROW_HEIGHT
        self.max_height_by_term = term_height // int(self.ROW_HEIGHT / 2)

        # Account for margins and UI elements
        self.max_width_by_term = max(10, self.max_width_by_term - 2)  # Subtract margins
        self.max_height_by_term = max(10, self.max_height_by_term - 2)  # Subtract margins

        # Maximum canvas size can't exceed terminal size or hard-coded maximums
        self.effective_max_width = min(self.max_width_by_term, self.MAX_CANVAS_WIDTH)
        self.effective_max_height = min(self.max_height_by_term, self.MAX_CANVAS_HEIGHT)

    def on_resize(self, event) -> None:
        """Handle terminal resize events."""
        # Update constraints when terminal resizes
        self.update_size_constraints()

        # If current canvas size exceeds new constraints, resize it
        if self.canvas_width > self.effective_max_width or self.canvas_height > self.effective_max_height:
            size_limited = False

            if self.canvas_width > self.effective_max_width:
                self.canvas_width = self.effective_max_width
                # Determine which limit we hit
                if self.max_width_by_term < self.MAX_CANVAS_WIDTH:
                    self.request_message(f"Canvas width adjusted to fit terminal ({self.max_width_by_term} cells)", 2.0)
                else:
                    self.request_message(f"Canvas width adjusted to maximum ({self.MAX_CANVAS_WIDTH} cells)", 2.0)
                size_limited = True

            if self.canvas_height > self.effective_max_height:
                self.canvas_height = self.effective_max_height
                # Determine which limit we hit
                if self.max_height_by_term < self.MAX_CANVAS_HEIGHT:
                    self.request_message(f"Canvas height adjusted to fit terminal ({self.max_height_by_term} cells)", 2.0)
                else:
                    self.request_message(f"Canvas height adjusted to maximum ({self.MAX_CANVAS_HEIGHT} cells)", 2.0)
                size_limited = True

            if size_limited:
                self.matrix = self.extend_canvas()
                _ = self.refresh()

    def alter_canvas_size(
        self, operation: Operation, horizontally: bool = True, vertically: bool = True, *, amount: int = 10
    ) -> None:
        """Alter the size of the canvas."""
        if self.running:
            try:
                _ = asyncio.create_task(self.toggle())
            except RuntimeError:
                # No running event loop (likely in test environment)
                self.running = not self.running

        # Always set constraints for test environments
        self.max_width_by_term = self.MAX_CANVAS_WIDTH
        self.max_height_by_term = self.MAX_CANVAS_HEIGHT
        self.effective_max_width = self.MAX_CANVAS_WIDTH
        self.effective_max_height = self.MAX_CANVAS_HEIGHT

        # In a real terminal, this would get updated based on terminal size
        if hasattr(self, 'size') and self.size:
            self.update_size_constraints()

        size_limited = False
        limit_reason = ""

        if horizontally:
            if operation.value == "increase":
                # Check if we'd exceed the maximum
                if self.canvas_width >= self.effective_max_width:
                    # Determine which limit we hit
                    if self.max_width_by_term < self.MAX_CANVAS_WIDTH:
                        limit_reason = f"terminal width ({self.max_width_by_term} cells)"
                    else:
                        limit_reason = f"maximum width ({self.MAX_CANVAS_WIDTH} cells)"
                    size_limited = True
                    # Set to the maximum allowed size
                    self.canvas_width = self.effective_max_width
                else:
                    # Increase the width, capped at the maximum
                    new_width = min(self.canvas_width + amount, self.effective_max_width)
                    self.canvas_width = new_width
            elif operation.value == "decrease":
                if self.canvas_width <= 10:
                    self.request_message(f"Minimum canvas width reached (10 cells)", 2.0)
                    return
                self.canvas_width -= amount
            else:
                raise RuntimeError(f"Invalid operation: {operation}")

        if vertically:
            if operation.value == "increase":
                if self.canvas_height >= self.effective_max_height:
                    # Determine which limit we hit (if not already set)
                    if not limit_reason:
                        if self.max_height_by_term < self.MAX_CANVAS_HEIGHT:
                            limit_reason = f"terminal height ({self.max_height_by_term} cells)"
                        else:
                            limit_reason = f"maximum height ({self.MAX_CANVAS_HEIGHT} cells)"
                    size_limited = True
                    # Set to the maximum allowed size
                    self.canvas_height = self.effective_max_height
                else:
                    # Increase the height, capped at the maximum
                    new_height = min(self.canvas_height + amount, self.effective_max_height)
                    self.canvas_height = new_height
            elif operation.value == "decrease":
                if self.canvas_height <= 10:
                    self.request_message(f"Minimum canvas height reached (10 cells)", 2.0)
                    return
                self.canvas_height -= amount
            else:
                raise RuntimeError(f"Invalid operation: {operation}")

        # Always extend the canvas matrix regardless of whether we hit a limit
        # This ensures the matrix is always the right size for the current dimensions
        self.matrix = self.extend_canvas()
        _ = self.refresh()

        if size_limited:
            # Display message about which limit was reached
            self.request_message(f"Canvas size limited by {limit_reason}", 2.0)

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
            if (self.cursor_square.y < self.matrix.shape[0] and
                self.cursor_square.x < self.matrix.shape[1]):
                self.cursor_colour = "black" if self.matrix[self.cursor_square.y, self.cursor_square.x] == 0 else "white"

    def toggle_cell(self, x: int, y: int) -> None:
        if y < self.matrix.shape[0] and x < self.matrix.shape[1]:
            # Use XOR operation to toggle between 0 and 1
            self.matrix[y, x] ^= 1
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
            int(x * self.ROW_HEIGHT),
            int(y * int(self.ROW_HEIGHT / 2)),
            int(self.ROW_HEIGHT),
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
                if row < self.matrix.shape[0] and column < self.matrix.shape[1]:
                    square_style = self.black if self.matrix[row, column] == 1 else self.white

            return square_style

        segments = [
            Segment(" " * self.ROW_HEIGHT, get_square_style(column, row_index)) for column in range(self.canvas_width)
        ]
        strip = Strip(segments)
        return strip
