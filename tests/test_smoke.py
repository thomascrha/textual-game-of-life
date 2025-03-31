from textual.app import App
from src.textual_game_of_life.canvas import Canvas
from src.textual_game_of_life.tui import CellularAutomatonTui


def test_import():
    """Test that all necessary modules can be imported."""
    import src.textual_game_of_life as textual_game_of_life
    import src.textual_game_of_life.canvas
    import src.textual_game_of_life.modals
    import src.textual_game_of_life.tui

    assert True


def test_create_app():
    """Test that app can be created without errors."""
    app = CellularAutomatonTui()
    assert isinstance(app, App)


def test_create_canvas():
    """Test that canvas can be created with various sizes."""
    # Default size
    canvas = Canvas()
    assert canvas.canvas_width == 20
    assert canvas.canvas_height == 20

    # Custom size
    canvas = Canvas(width=30, height=40)
    assert canvas.canvas_width == 30
    assert canvas.canvas_height == 40


def test_random_canvas(canvas):
    """Test that random() populates the canvas."""
    canvas.clear()

    # Initially, all cells should be 0
    all_zeros = all(canvas.matrix[y][x] == 0 for y in range(canvas.canvas_height) for x in range(canvas.canvas_width))
    assert all_zeros

    # Randomize the canvas
    canvas.random()

    # Now some cells should be 1
    has_ones = any(canvas.matrix[y][x] == 1 for y in range(canvas.canvas_height) for x in range(canvas.canvas_width))
    assert has_ones
