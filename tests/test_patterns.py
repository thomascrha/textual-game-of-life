"""Tests for pattern generation in the Canvas widget."""
import numpy as np
import pytest
from src.textual_game_of_life.canvas import Canvas


def test_random_glider_addition(canvas):
    """Test that random glider can be added to the canvas."""
    # Clear canvas
    canvas.clear()

    # Add a glider
    canvas.add_random_glider()

    # Check that at least 5 cells are alive (glider has 5 alive cells)
    live_cells = np.sum(canvas.matrix)
    assert live_cells >= 5, "Random glider should have created at least 5 live cells"

    # Add another glider
    canvas.add_random_glider()

    # Check that more cells are now alive
    new_live_cells = np.sum(canvas.matrix)
    assert new_live_cells > live_cells, "Adding a second glider should increase the number of live cells"


def test_random_pulsar_addition(canvas):
    """Test that random pulsar can be added to the canvas."""
    # Create a larger canvas to fit the pulsar
    large_canvas = Canvas(width=50, height=50)

    # Clear canvas
    large_canvas.clear()

    # Add a pulsar
    large_canvas.add_random_pulsar()

    # Check that at least 48 cells are alive (pulsar has 48 alive cells)
    live_cells = np.sum(large_canvas.matrix)
    assert live_cells >= 48, "Random pulsar should have created at least 48 live cells"

    # Add another pulsar
    large_canvas.add_random_pulsar()

    # Check that more cells are now alive
    new_live_cells = np.sum(large_canvas.matrix)
    assert new_live_cells > live_cells, "Adding a second pulsar should increase the number of live cells"


def test_pulsar_in_small_canvas():
    """Test that adding a pulsar to a too-small canvas is handled gracefully."""
    # Create a canvas too small for a pulsar (requires 17x17)
    small_canvas = Canvas(width=15, height=15)
    small_canvas.clear()

    # This should not cause errors
    small_canvas.add_random_pulsar()

    # Canvas should remain unchanged
    assert small_canvas.canvas_width == 15
    assert small_canvas.canvas_height == 15
