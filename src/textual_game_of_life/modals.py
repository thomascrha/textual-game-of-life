from textual.app import ComposeResult
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Static


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
