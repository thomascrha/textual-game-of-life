"""Tests for brush functionality in the Canvas widget."""
import pytest
from src.textual_game_of_life.canvas import Canvas


def test_brush_initialization():
    """Test that brush size initializes correctly."""
    # Default brush size
    canvas = Canvas()
    assert canvas.brush_size == 1

    # Custom brush size
    canvas = Canvas(brush_size=5)
    assert canvas.brush_size == 5

    # Test brush size limits
    # Should be capped at MAX_BRUSH_SIZE
    canvas = Canvas(brush_size=20)
    assert canvas.brush_size == canvas.MAX_BRUSH_SIZE

    # Should be at least MIN_BRUSH_SIZE
    canvas = Canvas(brush_size=0)
    assert canvas.brush_size == canvas.MIN_BRUSH_SIZE


def test_brush_size_adjustments(canvas):
    """Test brush size increase and decrease."""
    # Set to a middle value for testing both directions
    canvas.brush_size = 5
    assert canvas.brush_size == 5

    # Increase
    canvas.increase_brush_size()
    assert canvas.brush_size == 6

    # Decrease
    canvas.decrease_brush_size()
    assert canvas.brush_size == 5

    # Test upper limit
    for _ in range(20):  # More than needed to reach max
        canvas.increase_brush_size()
    assert canvas.brush_size == canvas.MAX_BRUSH_SIZE

    # Test one more increase at the limit (should have no effect)
    canvas.increase_brush_size()
    assert canvas.brush_size == canvas.MAX_BRUSH_SIZE

    # Test lower limit
    for _ in range(20):  # More than needed to reach min
        canvas.decrease_brush_size()
    assert canvas.brush_size == canvas.MIN_BRUSH_SIZE

    # Test one more decrease at the limit (should have no effect)
    canvas.decrease_brush_size()
    assert canvas.brush_size == canvas.MIN_BRUSH_SIZE
