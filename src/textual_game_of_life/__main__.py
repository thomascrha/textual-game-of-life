import asyncio
import random
from enum import Enum
from typing import List
from rich.segment import Segment
from rich.style import Style
from textual import events
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Grid
from textual.geometry import Offset, Region
from textual.reactive import var
from textual.screen import ModalScreen
from textual.strip import Strip
from textual.widget import Widget
from textual.widgets import Button, Footer, Label, Static


class Operation(str, Enum):
    INCREASE = "increase"
    DECREASE = "decrease"


class Help(ModalScreen):
    DEFAULT_CSS = """
    Help {
        align: center middle;
    }

    #help-dialog {
        padding: 1 1;
        width: 70;
        height: 40;
        border: thick $background 80%;
        background: $surface;
    }

    Button {
        width: 100%;
        align: center middle;
    }
    """
    HELP_STRING = """

    [b]Help[/b]

    [b]S[/b] - Step one generation
    [b]T[/b] - Toggle auto step
    [b]+[/b] - Increse the size of the canvas
    [b]-[/b] - Decrease the size of the canvas
    [b]R[/b] - Random canvas
    [b]C[/b] - Clear canvas
    [b]Q[/b] - Quit
    [b]LEFT[/b] - Decrease canvas horizontally
    [b]RIGHT[/b] - Increase canvas horizontally
    [b]DOWN[/b] - Increase canvas vertically
    [b]UP[/b] - Decrease canvas vertically
    [b]H[/b] - Help
    """

    def compose(self) -> ComposeResult:
        yield Grid(
            Static(self.HELP_STRING, id="help"),
            Button("Close", id="close"),
            id="help-dialog",
        )

    def on_button_pressed(self, _: Button.Pressed) -> None:
        self.app.pop_screen()


class Canvas(Widget):
    COMPONENT_CLASSES: set = {
        "canvas--white-square",
        "canvas--black-square",
        "canvas--cursor-square",
    }

    DEFAULT_CSS: str = """
    Canvas .canvas--white-square {
        background: #FFFFFF;
    }
    Canvas .canvas--black-square {
        background: #000000;
    }
    Canvas > .canvas--cursor-square {
        background: darkred;
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

    def __init__(self) -> None:
        super().__init__()
        self.canvas_matrix: List[List[int]] = [
            [0 for _ in range(self.CANVAS_WIDTH + 1)] for _ in range(self.CANVAS_HEIGHT + 1)
        ]

    def action_clear(self) -> None:
        self.canvas_matrix = [[0 for _ in range(self.CANVAS_WIDTH + 1)] for _ in range(self.CANVAS_HEIGHT + 1)]
        self.refresh()

    # step methods
    def action_step(self) -> None:
        self.canvas_matrix = self.get_next_generation()
        self.refresh()

    async def action_toggle(self):
        self.running = not self.running
        while self.running:
            await asyncio.sleep(self.REFRESH_INTERVAL)
            self.action_step()

    def get_neighbours(self, x: int, y: int) -> list[int]:
        neighbours = []
        for i in range(-1, 2):
            for j in range(-1, 2):
                if i == j == 0:
                    continue
                neighbours.append(self.canvas_matrix[(y + i) % self.CANVAS_HEIGHT][(x + j) % self.CANVAS_WIDTH])
        return neighbours

    def get_next_generation(self) -> list[list[int]]:
        new_canvas_matrix = [[0 for _ in range(self.CANVAS_WIDTH + 1)] for _ in range(self.CANVAS_HEIGHT + 1)]
        for y in range(self.CANVAS_HEIGHT):
            for x in range(self.CANVAS_WIDTH):
                neighbours = self.get_neighbours(x, y)
                if self.canvas_matrix[y][x] == 1:
                    if 2 <= sum(neighbours) <= 3:
                        new_canvas_matrix[y][x] = 1
                else:
                    if sum(neighbours) == 3:
                        new_canvas_matrix[y][x] = 1
        return new_canvas_matrix

    def action_random(self) -> None:
        for y in range(self.CANVAS_HEIGHT):
            for x in range(self.CANVAS_WIDTH):
                self.canvas_matrix[y][x] = random.randint(0, 1)
        self.refresh()

    def alter_canvas_size(
        self, operation: Operation, horizontally: bool = True, vertically: bool = True, *, amount: int = 10
    ) -> None:
        if self.running:
            asyncio.create_task(self.action_toggle())

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

        self.canvas_matrix = [[0 for _ in range(self.CANVAS_WIDTH + 1)] for _ in range(self.CANVAS_HEIGHT + 1)]
        self.refresh()

    def action_decrease_canvas(self) -> None:
        self.alter_canvas_size(Operation.DECREASE)

    def action_increase_canvas(self) -> None:
        self.alter_canvas_size(Operation.INCREASE)

    def action_decrease_canvas_horizontally(self) -> None:
        self.alter_canvas_size(Operation.DECREASE, vertically=False)

    def action_increase_canvas_horizontally(self) -> None:
        self.alter_canvas_size(Operation.INCREASE, vertically=False)

    def action_decrease_canvas_vertically(self) -> None:
        self.alter_canvas_size(Operation.DECREASE, horizontally=False)

    def action_increase_canvas_vertically(self) -> None:
        self.alter_canvas_size(Operation.INCREASE, horizontally=False)

    @property
    def white(self) -> Style:
        return self.get_component_rich_style("canvas--white-square")

    @property
    def black(self) -> Style:
        return self.get_component_rich_style("canvas--black-square")

    @property
    def cursor(self) -> Style:
        return self.get_component_rich_style("canvas--cursor-square")

    def on_mouse_move(self, event: events.MouseMove) -> None:
        mouse_position = event.offset + self.scroll_offset
        self.cursor_square = Offset(
            mouse_position.x // self.ROW_HEIGHT,
            mouse_position.y // int(self.ROW_HEIGHT / 2),
        )

    def on_click(self, event: events.Click) -> None:
        mouse_position = event.offset + self.scroll_offset
        self.cursor_square = Offset(
            mouse_position.x // self.ROW_HEIGHT,
            mouse_position.y // int(self.ROW_HEIGHT / 2),
        )
        self.x = self.cursor_square.x
        self.y = self.cursor_square.y

        # toggle the square
        if len(self.canvas_matrix) > self.y and len(self.canvas_matrix[self.y]) > self.x:
            self.canvas_matrix[self.y][self.x] ^= 1

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
                if len(self.canvas_matrix) > row and len(self.canvas_matrix[row]) > column:
                    square_style = self.black if self.canvas_matrix[row][column] == 1 else self.white

            return square_style

        segments = [
            Segment(" " * self.ROW_HEIGHT, get_square_style(column, row_index)) for column in range(self.CANVAS_WIDTH)
        ]
        strip = Strip(segments)
        return strip


class CellularAutomatonTui(App):
    BINDINGS = [
        Binding("s", "step", "Step"),
        Binding("t", "toggle", "Toggle"),
        Binding("+", "increase_canvas", "Larger"),
        Binding("-", "decrease_canvas", "Smaller"),
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

    def action_increase_canvas(self) -> None:
        self.canvas.action_increase_canvas()

    def action_decrease_canvas(self) -> None:
        self.canvas.action_decrease_canvas()

    def action_increase_canvas_horizontally(self) -> None:
        self.canvas.action_increase_canvas_horizontally()

    def action_decrease_canvas_horizontally(self) -> None:
        self.canvas.action_decrease_canvas_horizontally()

    def action_increase_canvas_vertically(self) -> None:
        self.canvas.action_increase_canvas_vertically()

    def action_decrease_canvas_vertically(self) -> None:
        self.canvas.action_decrease_canvas_vertically()

    def action_toggle(self) -> None:
        asyncio.create_task(self.canvas.action_toggle())

    def action_clear(self) -> None:
        self.canvas.action_clear()

    def action_step(self) -> None:
        self.canvas.action_step()

    def action_random(self) -> None:
        self.canvas.action_random()

    def action_help(self) -> None:
        self.push_screen(Help())


def main():
    app = CellularAutomatonTui()
    app.run()


if __name__ == "__main__":
    main()
