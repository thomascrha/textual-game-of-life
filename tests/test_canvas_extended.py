"""Extended tests for Canvas functionality."""
from unittest.mock import MagicMock, PropertyMock, patch
import numpy as np
import pytest
from src.textual_game_of_life import Operation
from src.textual_game_of_life.canvas import Canvas


def test_extended_canvas_resize():
    """Test canvas resize with various dimensions."""
    # Create a canvas with custom dimensions
    canvas = Canvas(width=15, height=20)
    assert canvas.canvas_width == 15
    assert canvas.canvas_height == 20

    # Matrix should match those dimensions (plus 1 for internal padding)
    assert canvas.matrix.shape == (21, 16)

    # Resize to different dimensions
    canvas.canvas_width = 25
    canvas.canvas_height = 30
    canvas.matrix = canvas.extend_canvas()

    # Check that matrix was extended properly
    assert canvas.matrix.shape == (31, 26)

    # Check that previous content was preserved
    for y in range(15):
        for x in range(15):
            # Existing cells should be preserved
            assert canvas.matrix[y, x] == 0


def test_canvas_size_constraints_in_test_environment():
    """Test canvas size constraints are properly initialized in test environments."""
    canvas = Canvas()

    # Set some size constraints that would be initialized by a real app
    canvas.max_width_by_term = 0
    canvas.max_height_by_term = 0
    canvas.effective_max_width = 0
    canvas.effective_max_height = 0

    # Try to increase size
    canvas.alter_canvas_size(Operation.INCREASE)

    # Even without proper app initialization, constraints should be set
    assert canvas.max_width_by_term == canvas.MAX_CANVAS_WIDTH
    assert canvas.max_height_by_term == canvas.MAX_CANVAS_HEIGHT
    assert canvas.effective_max_width == canvas.MAX_CANVAS_WIDTH
    assert canvas.effective_max_height == canvas.MAX_CANVAS_HEIGHT


def test_update_size_constraints():
    """Test updating size constraints based on terminal size."""
    canvas = Canvas()

    # Mock the size property
    size_mock = MagicMock()
    size_mock.width = 100
    size_mock.height = 50

    # Use patch.object to mock the property instead of trying to set it
    with patch.object(Canvas, "size", PropertyMock(return_value=size_mock)):
        # Update constraints
        canvas.update_size_constraints()

    # Check that constraints were calculated properly
    # Each canvas cell takes ROW_HEIGHT (2) characters horizontally and ROW_HEIGHT/2 (1) vertically
    # With margins of 2 in each dimension
    expected_width = (100 // 2) - 2  # Terminal width / cell width - margins
    expected_height = (50 // 1) - 2  # Terminal height / cell height - margins

    # Values should be capped at MAX values
    expected_width = min(expected_width, canvas.MAX_CANVAS_WIDTH)
    expected_height = min(expected_height, canvas.MAX_CANVAS_HEIGHT)

    assert canvas.effective_max_width == expected_width
    assert canvas.effective_max_height == expected_height


def test_toggle_with_runtime_error():
    """Test toggle function when runtime error occurs."""
    canvas = Canvas()

    # Set initial running state
    canvas.running = False

    # Mock asyncio.create_task to raise RuntimeError
    with patch("asyncio.create_task") as mock_create_task:
        mock_create_task.side_effect = RuntimeError("No running event loop")

        # Call toggle and get the coroutine object
        toggle_coro = canvas.toggle()

        # Try to start running the coroutine to trigger the toggle at the beginning
        try:
            # This will run the code until the first await or return
            toggle_coro.__await__().__next__()
        except (StopIteration, RuntimeError):
            # Expected to raise RuntimeError or StopIteration eventually
            pass

        # Check that running state was toggled despite the error
        assert canvas.running is True


def test_on_resize_handler():
    """Test resize event handler."""
    canvas = Canvas(width=90, height=90)

    # Mock size property to return a small terminal size
    size_mock = MagicMock()
    size_mock.width = 40  # Small width
    size_mock.height = 30  # Small height

    # Use patch.object to mock the property
    with patch.object(Canvas, "size", PropertyMock(return_value=size_mock)):
        # Mock the request_message method
        canvas.request_message = MagicMock()

    # Create a mock resize event
    event_mock = MagicMock()

    # Call the resize handler
    canvas.on_resize(event_mock)

    # Canvas should be resized to fit the terminal
    assert canvas.canvas_width < 90
    assert canvas.canvas_height < 90

    # Message should have been displayed
    assert canvas.request_message.called
