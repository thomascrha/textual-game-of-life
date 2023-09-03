from rich.segment import Segment
from rich.style import Style
from textual.binding import Binding
from textual.geometry import Offset, Region
from textual.app import App, ComposeResult
from textual.strip import Strip
from textual.widget import Widget
from textual.widgets import Footer
from textual import events
from textual.reactive import var
import random


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

    REFRESH_INTERVAL: float = 5

    cursor_square = var(Offset(0, 0))

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.canvas_matrix = [
            [0 for _ in range(self.CANVAS_WIDTH + 1)]
            for _ in range(self.CANVAS_HEIGHT + 1)
        ]
        self.cellular_automaton = CellularAutomaton(self.canvas_matrix)

        self.running = False
        self.x = -1
        self.y = -1

    def action_clear(self) -> None:
        print("clear")
        self.canvas_matrix = [
            [0 for _ in range(self.CANVAS_WIDTH + 1)]
            for _ in range(self.CANVAS_HEIGHT + 1)
        ]
        self.refresh()

    # step methods
    def action_step(self) -> None:
        print("step")
        self.canvas_matrix = self.get_next_generation()
        self.refresh()

    def get_neighbours(self, x: int, y: int) -> list[int]:
        """Get the neighbours of a cell."""
        neighbours = []
        for i in range(-1, 2):
            for j in range(-1, 2):
                if i == j == 0:
                    continue
                neighbours.append(
                    self.canvas_matrix[(y + i) % self.CANVAS_HEIGHT][
                        (x + j) % self.CANVAS_WIDTH
                    ]
                )
        return neighbours

    def get_next_generation(self) -> list[list[int]]:
        """Get the next generation of the canvas."""
        new_canvas_matrix = [
            [0 for _ in range(self.CANVAS_WIDTH + 1)]
            for _ in range(self.CANVAS_HEIGHT + 1)
        ]
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
        print("random")
        for y in range(self.CANVAS_HEIGHT):
            for x in range(self.CANVAS_WIDTH):
                self.canvas_matrix[y][x] = random.randint(0, 1)
        self.refresh()

    def action_decrease_canvas(self) -> None:
        print("decrease")
        if self.CANVAS_HEIGHT <= 10 or self.CANVAS_WIDTH <= 10:
            return

        self.CANVAS_HEIGHT -= 10
        self.CANVAS_WIDTH -= 10
        self.canvas_matrix = [
            [0 for _ in range(self.CANVAS_WIDTH + 1)]
            for _ in range(self.CANVAS_HEIGHT + 1)
        ]
        self.refresh()

    def action_increase_canvas(self) -> None:
        print("increase")
        if self.CANVAS_HEIGHT >= 100 or self.CANVAS_WIDTH >= 100:
            return

        self.CANVAS_HEIGHT += 10
        self.CANVAS_WIDTH += 10
        self.canvas_matrix = [
            [0 for _ in range(self.CANVAS_WIDTH + 1)]
            for _ in range(self.CANVAS_HEIGHT + 1)
        ]
        self.refresh()

    @property
    def white(self) -> Style:
        return self.get_component_rich_style("canvas--white-square")

    @property
    def black(self) -> Style:
        return self.get_component_rich_style("canvas--black-square")

    @property
    def cursor(self) -> Style:
        return self.get_component_rich_style("canvas--cursor-square")

    @property
    def information_bar_region(self) -> Region:
        """Get the header region."""
        return Region(0, self.CANVAS_HEIGHT + 1, self.size.width, self.ROW_HEIGHT)

    def on_mouse_move(self, event: events.MouseMove) -> None:
        """Called when the user moves the mouse over the widget."""
        mouse_position = event.offset + self.scroll_offset
        self.cursor_square = Offset(
            mouse_position.x // self.ROW_HEIGHT,
            mouse_position.y // int(self.ROW_HEIGHT / 2),
        )

    def on_click(self, event: events.Click) -> None:
        """Called when the user clicks on the widget."""
        mouse_position = event.offset + self.scroll_offset
        self.cursor_square = Offset(
            mouse_position.x // self.ROW_HEIGHT,
            mouse_position.y // int(self.ROW_HEIGHT / 2),
        )
        self.x = self.cursor_square.x
        self.y = self.cursor_square.y

        # toggle the square
        if (
            len(self.canvas_matrix) > self.y
            and len(self.canvas_matrix[self.y]) > self.x
        ):
            self.canvas_matrix[self.y][self.x] ^= 1

        self.refresh(self.information_bar_region)
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

    def watch_cursor_square(
        self, previous_square: Offset, cursor_square: Offset
    ) -> None:
        """Called when the cursor square changes."""
        # Refresh the previous cursor square
        self.refresh(self.get_square_region(previous_square))

        # Refresh the new cursor square
        self.refresh(self.get_square_region(cursor_square))

    def render_line(self, y: int) -> Strip:
        """Render a line of the widget. y is relative to the top of the widget."""
        row_index = y // int(self.ROW_HEIGHT / 2)
        if row_index == self.CANVAS_HEIGHT + 1:
            self.information_bar = True
            return Strip([Segment(f"X: {self.x} Y: {self.y}")])

        if row_index >= self.CANVAS_HEIGHT:
            return Strip.blank(self.size.width)

        def get_square_style(column: int, row: int) -> Style:
            """Get the cursor style at the given position on the checkerboard."""
            if self.cursor_square == Offset(column, row):
                square_style = self.cursor
            else:
                square_style = self.black
                # only update the scauare that aren't out of range
                if (
                    len(self.canvas_matrix) > row
                    and len(self.canvas_matrix[row]) > column
                ):
                    square_style = (
                        self.black
                        if self.canvas_matrix[row][column] == 1
                        else self.white
                    )

            return square_style

        segments = [
            Segment(" " * self.ROW_HEIGHT, get_square_style(column, row_index))
            for column in range(self.CANVAS_WIDTH)
        ]
        strip = Strip(segments)
        return strip


class CellularAutomatonTui(App):
    BINDINGS = [
        Binding("s", "step", "Step"),
        Binding("+", "increase_canvas", "Increase canvas size"),
        Binding("-", "decrease_canvas", "Decrease canvas size"),
        Binding("r", "random", "Random"),
        Binding("c", "clear", "Clear", priority=True),
        Binding("q", "quit", "Quit"),
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

    def action_clear(self) -> None:
        self.canvas.action_clear()

    def action_step(self) -> None:
        self.canvas.action_step()

    def action_random(self) -> None:
        self.canvas.action_random()


if __name__ == "__main__":
    app = CellularAutomatonTui()
    app.run()
