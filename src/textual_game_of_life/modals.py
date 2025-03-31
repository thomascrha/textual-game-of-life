import asyncio
from typing import Any
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Static
from typing_extensions import override


class About(ModalScreen[Any]):
    BINDINGS = [Binding("escape", "pop_screen", "Close")]

    DEFAULT_CSS: str = """
    About {
        align: center middle;
    }

    #about-dialog {
        padding: 1 1;
        width: 80;
        height: 30;
        border: thick $background 80%;
        background: $surface;
    }

    #about-close {
        width: 100%;
        align: center middle;
    }
    """

    def __init__(self, version: str):
        super().__init__()
        self.version = version

    @override
    def compose(self) -> ComposeResult:
        about_text = f"""
        [b]Textual Game of Life[/b]
        A Conway's Game of Life implementation in the terminal
        built with the Textual TUI framework.

        [b]Version:[/b] {self.version}
        [b]Author:[/b] Thomas Crha
        [b]GitHub:[/b] https://github.com/thomascrha/textual-game-of-life

        """
        yield Grid(
            Static(about_text, id="about-content"),
            Button("Close", id="about-close"),
            id="about-dialog",
        )

    def on_button_pressed(self, _: Button.Pressed) -> None:
        self.dismiss_modal()

    def action_pop_screen(self) -> None:
        self.dismiss_modal()

    def dismiss_modal(self) -> None:
        # Resume animation if it was running before
        if hasattr(self, "was_running") and self.was_running:
            asyncio.create_task(self.app.canvas.toggle())
        self.app.pop_screen()


class Help(ModalScreen[Any]):
    BINDINGS = [Binding("escape", "pop_screen", "Close")]

    DEFAULT_CSS: str = """
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

    #help-close {
        width: 100%;
        align: center middle;
    }
    """
    HELP_STRING: str = """

    [b]Help[/b]

    [b]S[/b] - Step one generation
    [b]T[/b] - Toggle auto step
    [b]+[/b] - Increse the size of the canvas
    [b]-[/b] - Decrease the size of the canvas
    [b]F[/b] - Faster simulation
    [b]L[/b] - Slower simulation
    [b]A[/b] - Save game state
    [b]O[/b] - Load game state
    [b]R[/b] - Random canvas
    [b]G[/b] - Add random glider
    [b]P[/b] - Add random pulsar
    [b]C[/b] - Clear canvas
    [b]M[/b] - Show example message
    [b]Q[/b] - Quit
    [b]LEFT[/b] - Decrease canvas horizontally
    [b]RIGHT[/b] - Increase canvas horizontally
    [b]DOWN[/b] - Increase canvas vertically
    [b]UP[/b] - Decrease canvas vertically
    [b]H[/b] - Help
    """

    @override
    def compose(self) -> ComposeResult:
        yield Grid(
            Static(self.HELP_STRING, id="help"),
            Button("Close", id="help-close"),
            id="help-dialog",
        )

    def on_button_pressed(self, _: Button.Pressed) -> None:
        self.dismiss_modal()

    def action_pop_screen(self) -> None:
        self.dismiss_modal()

    def dismiss_modal(self) -> None:
        # Resume animation if it was running before
        if hasattr(self, "was_running") and self.was_running:
            asyncio.create_task(self.app.canvas.toggle())
        self.app.pop_screen()
