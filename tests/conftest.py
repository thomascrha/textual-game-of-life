"""Test configuration and fixtures for pytest."""
import pytest
from src.textual_game_of_life.canvas import Canvas
from src.textual_game_of_life.tui import CellularAutomatonTui


@pytest.fixture
def canvas():
    """Return a Canvas widget instance for testing."""
    return Canvas(width=10, height=10, speed=0.5)


@pytest.fixture
def app():
    """Return an App instance with a canvas for testing."""
    app = CellularAutomatonTui(width=10, height=10, speed=0.5)
    # Create and attach canvas attribute for test compatibility
    app.canvas = Canvas(width=10, height=10, speed=0.5)
    return app

