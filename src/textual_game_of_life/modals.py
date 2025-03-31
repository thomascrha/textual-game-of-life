from typing import Any
from typing_extensions import override

from textual.app import ComposeResult
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Static


class Help(ModalScreen[Any]):
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

    Button {
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
    [b]C[/b] - Clear canvas
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
            Button("Close", id="close"),
            id="help-dialog",
        )

    def on_button_pressed(self, _: Button.Pressed) -> None:
        self.app.pop_screen()
