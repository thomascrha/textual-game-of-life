from typing import Dict
from rich.segment import Segment
from rich.style import Style

from textual.app import App, ComposeResult
from textual.strip import Strip
from textual.widgets import Header
from textual.widget import Widget



class Canvas(Widget):
    COMPONENT_CLASSES: set = {
        "canvas--white-square",
        "canvas--black-square",
    }

    DEFAULT_CSS: str = """
    Canvas .canvas--white-square {
        background: #FFFFFF;
    }
    Canvas .canvas--black-square {
        background: #000000;
    }
    """
    ROW_HEIGHT: int = 2
    CANVAS_HEIGHT: int = 8
    CANVAS_WIDTH: int = 8

    CANVAS_OFFSET: int = 2

    @property
    def white(self) -> Style:
        return self.get_component_rich_style("canvas--white-square")

    @property
    def black(self) -> Style:
        return self.get_component_rich_style("canvas--black-square")

    def render_line(self, y: int) -> Strip:
        """Render a line of the widget. y is relative to the top of the widget."""

        row_index = y // (self.ROW_HEIGHT / 2)

        if row_index >= self.CANVAS_HEIGHT + self.CANVAS_OFFSET or row_index < self.CANVAS_OFFSET:
            return Strip.blank(self.size.width)

        is_odd = row_index % 2

        segments = [
            Segment(" " * self.ROW_HEIGHT, self.black if (column + is_odd) % 2 else self.white)
            for column in range(self.CANVAS_WIDTH)
        ]
        strip = Strip(segments, 8 * 8)
        return strip


class BoardApp(App):
    def compose(self) -> ComposeResult:
        yield Canvas()


if __name__ == "__main__":
    app = BoardApp()
    app.run()

