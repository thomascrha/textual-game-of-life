import asyncio
import json
import os
from typing import Any
from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.widgets import Footer

from .canvas import Canvas
from .modals import Help
from . import Operation


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
        Binding("c", "clear", "Clear"),
        Binding("q", "quit", "Quit"),
        Binding("left", "decrease_canvas_horizontally", " "),
        Binding("right", "increase_canvas_horizontally", " "),
        Binding("down", "increase_canvas_vertically", " "),
        Binding("up", "decrease_canvas_vertically", " "),
        Binding("h", "help", "Help"),
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

    def action_increase_canvas(self) -> None:
        self.canvas.alter_canvas_size(Operation.INCREASE)

    def action_decrease_canvas_horizontally(self) -> None:
        self.canvas.alter_canvas_size(Operation.DECREASE, vertically=False)

    def action_increase_canvas_horizontally(self) -> None:
        self.canvas.alter_canvas_size(Operation.INCREASE, vertically=False)

    def action_decrease_canvas_vertically(self) -> None:
        self.canvas.alter_canvas_size(Operation.DECREASE, horizontally=False)

    def action_increase_canvas_vertically(self) -> None:
        self.canvas.alter_canvas_size(Operation.INCREASE, horizontally=False)

    def action_toggle(self) -> None:
        asyncio.create_task(self.canvas.toggle())

    def action_increase_speed(self) -> None:
        self.canvas.refresh_interval -= 0.1

    def action_decrease_speed(self) -> None:
        self.canvas.refresh_interval += 0.1

    def action_clear(self) -> None:
        self.canvas.clear()

    def action_step(self) -> None:
        self.canvas.step()

    def action_random(self) -> None:
        self.canvas.random()

    def action_help(self) -> None:
        self.push_screen(Help())

    def action_save(self) -> None:
        data = {
            "matrix": self.canvas.matrix,
            "canvas_width": self.canvas.canvas_width,
            "canvas_height": self.canvas.canvas_height,
        }
        with open("./save.textual", "w") as save_file:
            json.dump(data, save_file)

    def action_load(self) -> None:
        if not os.path.exists("./save.textual"):
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
