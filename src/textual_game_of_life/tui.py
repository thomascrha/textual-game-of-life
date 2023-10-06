import asyncio
import json
import os
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer

from .canvas import Canvas
from .modals import Help
from . import Operation


class CellularAutomatonTui(App):
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
        Binding("c", "clear", "Clear"),
        Binding("q", "quit", "Quit"),
        Binding("left", "decrease_canvas_horizontally", " "),
        Binding("right", "increase_canvas_horizontally", " "),
        Binding("down", "increase_canvas_vertically", " "),
        Binding("up", "decrease_canvas_vertically", " "),
        Binding("h", "help", "Help"),
    ]

    def compose(self) -> ComposeResult:
        self.canvas = Canvas()
        yield self.canvas
        yield Footer()

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
        self.canvas.REFRESH_INTERVAL -= 0.1

    def action_decrease_speed(self) -> None:
        self.canvas.REFRESH_INTERVAL += 0.1

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
            "canvas_width": self.canvas.CANVAS_WIDTH,
            "canvas_height": self.canvas.CANVAS_HEIGHT,
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
                [[0 for _ in range(self.canvas.CANVAS_WIDTH + 1)] for _ in range(self.canvas.CANVAS_HEIGHT + 1)],
            )
            self.canvas.CANVAS_WIDTH = data.get("canvas_width", self.canvas.CANVAS_WIDTH)
            self.canvas.CANVAS_HEIGHT = data.get("canvas_height", self.canvas.CANVAS_HEIGHT)
            self.canvas.refresh()


