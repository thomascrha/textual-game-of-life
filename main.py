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


class Canvas(Widget):
    COMPONENT_CLASSES: set = {
        "canvas--white-square",
        "canvas--black-square",
        "canvas--cursor-square"
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

    cursor_square = var(Offset(0, 0))

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.canvas_matrix = [[0 for _ in range(self.CANVAS_WIDTH + 1)] for _ in range(self.CANVAS_HEIGHT + 1)]
        self.x = -1
        self.y = -1

    def action_clear(self) -> None:
        self.canvas_matrix = [[0 for _ in range(self.CANVAS_WIDTH + 1)] for _ in range(self.CANVAS_HEIGHT + 1)]
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
    def header_region(self) -> Region:
        """Get the header region."""
        return Region(0, 0, self.size.width, self.ROW_HEIGHT)

    def on_mouse_move(self, event: events.MouseMove) -> None:
        """Called when the user moves the mouse over the widget."""
        mouse_position = event.offset + self.scroll_offset
        self.cursor_square = Offset(mouse_position.x // self.ROW_HEIGHT, mouse_position.y // int(self.ROW_HEIGHT / 2))

    def on_click(self, event: events.Click) -> None:
        """Called when the user clicks on the widget."""
        mouse_position = event.offset + self.scroll_offset
        self.cursor_square = Offset(mouse_position.x // self.ROW_HEIGHT, mouse_position.y // int(self.ROW_HEIGHT / 2))
        self.clicked = True
        self.x = self.cursor_square.x
        self.y = self.cursor_square.y

        # toggle the square
        if len(self.canvas_matrix) > self.y and len(self.canvas_matrix[self.y]) > self.x:
            self.canvas_matrix[self.y][self.x] ^= 1

        self.refresh(self.header_region)
        self.refresh(self.get_square_region(self.cursor_square))

    def get_square_region(self, square_offset: Offset) -> Region:
        """Get region relative to widget from square coordinate."""
        x, y = square_offset
        region = Region(x * self.ROW_HEIGHT, y * int(self.ROW_HEIGHT / 2), self.ROW_HEIGHT, int(self.ROW_HEIGHT / 2))
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
        if row_index == 0:
            return Strip([Segment(f"X: {self.x} Y: {self.y}")])

        if row_index >= self.CANVAS_HEIGHT + self.CANVAS_OFFSET or row_index < self.CANVAS_OFFSET:
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
            Segment(" " * self.ROW_HEIGHT, get_square_style(column, row_index))
            for column in range(self.CANVAS_WIDTH)
        ]
        strip = Strip(segments)
        return strip


class CellularAutomatonTui(App):
    BINDINGS = [
        Binding("t", "toggle", "Toggle"),
        Binding("q", "quit", "Quit"),
        Binding("c", "clear", "Clear", priority=True),
        Binding("r", "random", "Random"),
        Binding("p", "pause", "Pause")
    ]

    def compose(self) -> ComposeResult:
        self.canvas = Canvas()
        yield self.canvas
        yield Footer()

    def action_quit(self) -> None:
        exit()

    def action_clear(self) -> None:
        self.canvas.action_clear()


if __name__ == "__main__":
    app = CellularAutomatonTui()
    app.run()

