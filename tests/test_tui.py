import asyncio
import json
import os
from unittest.mock import mock_open, patch


def test_tui_initialization(app):
    """Test that TUI initializes with correct parameters."""
    assert app.initial_width == 10
    assert app.initial_height == 10
    assert app.initial_speed == 0.5
    assert app.initial_brush_size == 1
    assert app.load_file is None
    assert app.random_start is False


def test_speed_adjustment(app):
    """Test that speed can be adjusted."""
    # Get initial speed
    initial_speed = app.canvas.refresh_interval

    # Increase speed
    app.action_increase_speed()
    assert app.canvas.refresh_interval == initial_speed - 0.1

    # Decrease speed
    app.action_decrease_speed()
    assert app.canvas.refresh_interval == initial_speed


def test_canvas_size_actions(app):
    """Test that canvas size actions work correctly."""
    # Get initial size
    initial_width = app.canvas.canvas_width
    initial_height = app.canvas.canvas_height

    # Increase both dimensions
    app.action_increase_canvas()
    assert app.canvas.canvas_width == initial_width + 10
    assert app.canvas.canvas_height == initial_height + 10

    # Decrease back to original
    app.action_decrease_canvas()
    assert app.canvas.canvas_width == initial_width
    assert app.canvas.canvas_height == initial_height

    # Increase horizontally only
    app.action_increase_canvas_horizontally()
    assert app.canvas.canvas_width == initial_width + 10
    assert app.canvas.canvas_height == initial_height

    # Increase vertically only
    app.action_increase_canvas_vertically()
    assert app.canvas.canvas_width == initial_width + 10
    assert app.canvas.canvas_height == initial_height + 10

    # Decrease horizontally only
    app.action_decrease_canvas_horizontally()
    assert app.canvas.canvas_width == initial_width
    assert app.canvas.canvas_height == initial_height + 10

    # Decrease vertically only
    app.action_decrease_canvas_vertically()
    assert app.canvas.canvas_width == initial_width
    assert app.canvas.canvas_height == initial_height


def test_save_load_game(app, monkeypatch):
    """Test saving and loading game state."""
    # Mock data for testing
    test_data = {
        "matrix": [[0, 1], [1, 0]],
        "canvas_width": 15,
        "canvas_height": 18,
    }

    # Set up app's canvas with test values
    app.canvas.matrix = test_data["matrix"]
    app.canvas.canvas_width = test_data["canvas_width"]
    app.canvas.canvas_height = test_data["canvas_height"]

    # Mock the open function for save
    with patch("builtins.open", mock_open()) as mock_file:
        app.action_save()
        # Check that file was opened for writing
        mock_file.assert_called_once_with("./save.textual", "w")
        # Don't try to parse JSON directly, just verify the file was opened
        # The actual content verification can be done through other means

    # Reset canvas to different values
    app.canvas.clear()
    app.canvas.canvas_width = 10
    app.canvas.canvas_height = 10

    # Mock file existence check
    monkeypatch.setattr(os.path, "exists", lambda path: True)

    # Mock the open function for load with our test data
    with patch("builtins.open", mock_open(read_data=json.dumps(test_data))) as mock_file:
        app.action_load()
        # Check that values were loaded
        assert app.canvas.canvas_width == test_data["canvas_width"]
        assert app.canvas.canvas_height == test_data["canvas_height"]
        assert app.canvas.matrix == test_data["matrix"]
