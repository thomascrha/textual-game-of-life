import asyncio
import json
import os
import time
import numpy as np
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer
from typing_extensions import final, override
from . import Operation
from .canvas import Canvas
from .modals import About, Help


@final
class CellularAutomatonTui(App[None]):
    VERSION = "1.2.0"  # Hardcoded version to match pyproject.toml

    # Extend parent bindings rather than replace them
    BINDINGS = [
        Binding("s", "step", "Step"),
        Binding("t", "toggle", "Toggle"),
        Binding("+", "increase_canvas", "Larger"),
        Binding("-", "decrease_canvas", "Smaller"),
        Binding("f", "increase_speed", "Faster"),
        Binding("l", "decrease_speed", "Slower"),
        Binding("a", "save", "Save"),
        Binding("o", "load", "Load"),
        Binding("r", "random", "Random"),
        Binding("g", "add_glider", "Glider"),
        Binding("p", "add_pulsar", "Pulsar"),
        Binding("c", "clear", "Clear"),
        Binding("q", "quit", "Quit"),
        Binding("left", "decrease_canvas_horizontally", " "),
        Binding("right", "increase_canvas_horizontally", " "),
        Binding("down", "increase_canvas_vertically", " "),
        Binding("up", "decrease_canvas_vertically", " "),
        Binding("h", "help", "Help"),
        Binding("i", "about", "About"),
    ]

    canvas: Canvas  # pyright: ignore[reportUninitializedInstanceVariable]

    def __init__(
        self,
        width: int = 20,
        height: int = 20,
        speed: float = 0.5,
        brush_size: int = 1,
        load_file: str | None = None,
        random_start: bool = False,
    ) -> None:
        super().__init__()
        self.initial_width = width
        self.initial_height = height
        self.initial_speed = speed
        self.initial_brush_size = brush_size
        self.load_file = load_file
        self.random_start = random_start

    @override
    def compose(self) -> ComposeResult:
        self.canvas = Canvas(
            width=self.initial_width,
            height=self.initial_height,
            speed=self.initial_speed,
            brush_size=self.initial_brush_size,
        )
        yield self.canvas
        yield Footer()

    def on_mount(self) -> None:
        self.canvas.update_size_constraints()

        if self.random_start:
            self.canvas.random()
        if self.load_file:
            self._load_from_file(self.load_file)

    def on_canvas_message_request(self, event: Canvas.MessageRequest) -> None:
        self.display_message(event.message, event.timeout)

    @override
    async def action_quit(self) -> None:
        exit()

    def action_decrease_canvas(self) -> None:
        self.canvas.alter_canvas_size(Operation.DECREASE)
        self.display_message("Canvas size decreased", 1.0)

    def action_increase_canvas(self) -> None:
        self.canvas.alter_canvas_size(Operation.INCREASE)
        self.display_message("Canvas size increased", 1.0)

    def action_decrease_canvas_horizontally(self) -> None:
        self.canvas.alter_canvas_size(Operation.DECREASE, vertically=False)
        self.display_message("Canvas width decreased", 1.0)

    def action_increase_canvas_horizontally(self) -> None:
        self.canvas.alter_canvas_size(Operation.INCREASE, vertically=False)
        self.display_message("Canvas width increased", 1.0)

    def action_decrease_canvas_vertically(self) -> None:
        self.canvas.alter_canvas_size(Operation.DECREASE, horizontally=False)
        self.display_message("Canvas height decreased", 1.0)

    def action_increase_canvas_vertically(self) -> None:
        self.canvas.alter_canvas_size(Operation.INCREASE, horizontally=False)
        self.display_message("Canvas height increased", 1.0)

    @override
    def action_toggle(self) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        toggle_coro = self.canvas.toggle()

        try:
            # Try to create a task with the coroutine - this should be mocked in tests
            _ = asyncio.create_task(toggle_coro)
        except RuntimeError:
            # No running event loop (likely in test environment)
            # Just toggle the running state directly
            self.canvas.running = not self.canvas.running

        status = "Simulation paused" if self.canvas.running else "Simulation started"
        self.display_message(status, 1.0)

    def action_increase_speed(self) -> None:
        if self.canvas.refresh_interval <= 0.2:
            self.canvas.refresh_interval = 0.1  # Set to exact minimum
            self.display_message("Speed is at maximum (0.1s per step)", 1.0)
            return

        self.canvas.refresh_interval -= 0.1
        self.display_message(f"Speed increased - {self.canvas.refresh_interval:.1f}s per step", 1.0)

    def action_decrease_speed(self) -> None:
        self.canvas.refresh_interval += 0.1
        self.display_message(f"Speed decreased - {self.canvas.refresh_interval:.1f}s per step", 1.0)

    def action_clear(self) -> None:
        self.canvas.clear()
        self.display_message("Canvas cleared", 1.0)

    def action_step(self) -> None:
        self.canvas.step()
        self.display_message("Advanced one generation", 1.0)

    def action_random(self) -> None:
        self.canvas.random()
        self.display_message("Random pattern generated", 1.0)

    def action_add_glider(self) -> None:
        self.canvas.add_random_glider()
        self.display_message("Random glider added", 1.0)

    def action_add_pulsar(self) -> None:
        self.canvas.add_random_pulsar()
        self.display_message("Random pulsar added", 1.0)

    def display_message(self, text: str, timeout: float = 3.0) -> None:
        self.canvas.message = text
        self.canvas.message_visible = True
        self.canvas.message_timestamp = time.time()
        self.canvas.message_timeout = timeout
        _ = self.canvas.refresh()  # Force refresh to show the message

        # Schedule the message removal
        if self.canvas.message_task and not self.canvas.message_task.done():
            _ = self.canvas.message_task.cancel()

        try:
            # Create and store the task for auto-timeout
            self.canvas.message_task = asyncio.create_task(self._message_timeout_task(timeout))
        except RuntimeError:
            # No running event loop (likely in test environment)
            # For test environments, just mark message as not visible after timeout
            self.canvas.message_visible = False

    async def _message_timeout_task(self, timeout: float) -> None:
        try:
            await asyncio.sleep(timeout)
            if self.canvas.message_visible:
                self.canvas.message_visible = False
                try:
                    _ = self.canvas.refresh()
                except Exception:
                    # Handle potential errors in test environments
                    pass
        except asyncio.CancelledError:
            # Task was cancelled, likely because a new message is being displayed
            pass

    def action_help(self) -> None:
        was_running = self.canvas.running
        if was_running:
            try:
                task = self.canvas.toggle()
                _ = asyncio.create_task(task)
            except RuntimeError:
                # No running event loop (likely in test environment)
                self.canvas.running = not self.canvas.running

        help_screen = Help()
        help_screen.was_running = was_running
        _ = self.push_screen(help_screen)

    def action_about(self) -> None:
        was_running = self.canvas.running
        if was_running:
            try:
                task = self.canvas.toggle()
                _ = asyncio.create_task(task)
            except RuntimeError:
                # No running event loop (likely in test environment)
                self.canvas.running = not self.canvas.running

        about_screen = About(self.VERSION)
        about_screen.was_running = was_running
        _ = self.push_screen(about_screen)

    def action_save(self) -> None:
        data = {
            "matrix": self.canvas.matrix.tolist(),  # Convert NumPy array to list for JSON serialization
            "canvas_width": self.canvas.canvas_width,
            "canvas_height": self.canvas.canvas_height,
        }
        with open("./save.textual", "w") as save_file:
            json.dump(data, save_file)
        self.display_message("Game state saved to save.textual", 1.0)

    def action_load(self) -> None:
        self._load_from_file("./save.textual")

    def _load_from_file(self, filepath: str) -> None:
        if not os.path.exists(filepath):
            self.display_message(f"Save file not found: {filepath}", 1.0)
            return

        with open(filepath) as load_file:
            data = json.load(load_file)  # pyright: ignore[reportAny]
            # Convert the loaded matrix (which is a list of lists) to a NumPy array
            matrix_data = data.get("matrix", [])  # pyright: ignore[reportAny]
            if matrix_data:
                self.canvas.matrix = np.array(matrix_data, dtype=np.int8)
            else:
                self.canvas.matrix = np.zeros(
                    (self.canvas.canvas_height + 1, self.canvas.canvas_width + 1), dtype=np.int8
                )

            self.canvas.canvas_width = data.get("canvas_width", self.canvas.canvas_width)  # pyright: ignore[reportAny]
            self.canvas.canvas_height = data.get(
                "canvas_height", self.canvas.canvas_height
            )  # pyright: ignore[reportAny]
            _ = self.canvas.refresh()
            self.display_message(f"Game state loaded from {filepath}", 1.0)
