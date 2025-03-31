import asyncio
import json
import os
from typing import Any
from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.widgets import Footer
from . import Operation
from .canvas import Canvas
from .modals import About, Help


class CellularAutomatonTui(App[Any]):
    """Conway's Game of Life TUI application."""

    def __init__(
        self,
        width: int = 20,
        height: int = 20,
        speed: float = 0.5,
        brush_size: int = 1,
        load_file: str = None,
        random_start: bool = False,
    ) -> None:
        """Initialize the application with optional configuration.

        Args:
            width: Initial canvas width
            height: Initial canvas height
            speed: Simulation speed (lower is faster)
            brush_size: Initial brush size
            load_file: Path to a saved game state file to load
            random_start: Whether to start with a random pattern
        """
        super().__init__()
        self.initial_width = width
        self.initial_height = height
        self.initial_speed = speed
        self.initial_brush_size = brush_size
        self.load_file = load_file
        self.random_start = random_start

    VERSION = "0.10.0"  # Hardcoded version to match pyproject.toml

    BINDINGS: list[BindingType] = [
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
    canvas: Canvas

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
        """Called when app is mounted."""
        # Handle initial loading if specified
        if self.load_file:
            self._load_from_file(self.load_file)

        # Initialize with random pattern if requested
        if self.random_start:
            self.canvas.random()

    def action_quit(self) -> None:
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

    def action_toggle(self) -> None:
        try:
            # In normal operation, create a task that can be properly managed
            task = self.canvas.toggle()
            asyncio.create_task(task)
        except RuntimeError:
            # No running event loop (likely in test environment)
            # Just toggle the running state directly
            self.canvas.running = not self.canvas.running
            status = "Simulation started" if self.canvas.running else "Simulation paused"
            self.display_message(status, 1.0)

    def action_increase_speed(self) -> None:
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
        """Display a temporary message on the canvas.

        Args:
            text: The message to display
            timeout: How long to show the message in seconds
        """
        self.canvas.display_message(text, timeout)

    def action_help(self) -> None:
        # Pause animation if running when opening help screen
        was_running = self.canvas.running
        if was_running:
            try:
                asyncio.create_task(self.canvas.toggle())
            except RuntimeError:
                # No running event loop (likely in test environment)
                self.canvas.running = not self.canvas.running
        help_screen = Help()
        help_screen.was_running = was_running
        self.push_screen(help_screen)

    def action_about(self) -> None:
        # Pause animation if running when opening about screen
        was_running = self.canvas.running
        if was_running:
            try:
                asyncio.create_task(self.canvas.toggle())
            except RuntimeError:
                # No running event loop (likely in test environment)
                self.canvas.running = not self.canvas.running
        about_screen = About(self.VERSION)
        about_screen.was_running = was_running

        self.push_screen(about_screen)

    def action_save(self) -> None:
        data = {
            "matrix": self.canvas.matrix,
            "canvas_width": self.canvas.canvas_width,
            "canvas_height": self.canvas.canvas_height,
        }
        with open("./save.textual", "w") as save_file:
            json.dump(data, save_file)
        self.display_message("Game state saved to save.textual", 1.0)

    def action_load(self) -> None:
        if not os.path.exists("./save.textual"):
            self.display_message("Save file not found", 1.0)
            return

        with open("./save.textual") as load_file:
            data = json.load(load_file)
            self.canvas.matrix = data.get(
                "matrix",
                [[0 for _ in range(self.canvas.canvas_width + 1)] for _ in range(self.canvas.canvas_height + 1)],
            )
            self.canvas.canvas_width = data.get("canvas_width", self.canvas.canvas_width)
            self.canvas.canvas_height = data.get("canvas_height", self.canvas.canvas_height)
            self.canvas.refresh()
            self.display_message("Game state loaded from save.textual", 1.0)
