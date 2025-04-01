"""Test configuration and fixtures for pytest."""
import pytest
from src.textual_game_of_life.canvas import Canvas
from src.textual_game_of_life.tui import CellularAutomatonTui


@pytest.fixture
def canvas():
    """Return a Canvas widget instance for testing."""
    canvas = Canvas(width=10, height=10, speed=0.5)
    # Initialize size constraints for tests
    canvas.max_width_by_term = canvas.MAX_CANVAS_WIDTH
    canvas.max_height_by_term = canvas.MAX_CANVAS_HEIGHT
    canvas.effective_max_width = canvas.MAX_CANVAS_WIDTH
    canvas.effective_max_height = canvas.MAX_CANVAS_HEIGHT
    return canvas


@pytest.fixture
def app():
    """Return an App instance with a canvas for testing."""
    app = CellularAutomatonTui(width=10, height=10, speed=0.5)

    # Make sure canvas is properly initialized
    app.canvas = Canvas(width=10, height=10, speed=0.5)

    # Set default size constraints for test environment
    app.canvas.max_width_by_term = app.canvas.MAX_CANVAS_WIDTH
    app.canvas.max_height_by_term = app.canvas.MAX_CANVAS_HEIGHT
    app.canvas.effective_max_width = app.canvas.MAX_CANVAS_WIDTH
    app.canvas.effective_max_height = app.canvas.MAX_CANVAS_HEIGHT

    return app
