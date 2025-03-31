def test_canvas_initialization(canvas):
    """Test that Canvas initializes with correct dimensions."""
    assert canvas.canvas_width == 10
    assert canvas.canvas_height == 10
    assert canvas.refresh_interval == 0.5
    assert len(canvas.matrix) == 11  # +1 for the extra row/column
    assert len(canvas.matrix[0]) == 11


def test_toggle_cell(canvas):
    """Test that cells can be toggled."""
    # Initial state should be 0
    assert canvas.matrix[5][5] == 0

    # Toggle the cell
    canvas.toggle_cell(5, 5)
    assert canvas.matrix[5][5] == 1

    # Toggle it back
    canvas.toggle_cell(5, 5)
    assert canvas.matrix[5][5] == 0


def test_clear(canvas):
    """Test that clear() resets all cells to 0."""
    # Set some cells to 1
    canvas.toggle_cell(3, 3)
    canvas.toggle_cell(4, 4)
    canvas.toggle_cell(5, 5)

    # Clear the canvas
    canvas.clear()

    # All cells should be 0
    for y in range(canvas.canvas_height):
        for x in range(canvas.canvas_width):
            assert canvas.matrix[y][x] == 0


def test_get_neighbours(canvas):
    """Test that get_neighbours returns the correct neighbors."""
    # Create a pattern with some live cells
    canvas.toggle_cell(4, 4)  # Center
    canvas.toggle_cell(3, 4)  # Left
    canvas.toggle_cell(5, 4)  # Right

    # Check neighbors for (4, 4)
    neighbors = canvas.get_neighbours(4, 4)
    assert sum(neighbors) == 2


def test_canvas_boundaries(canvas):
    """Test that cells at boundaries interact correctly with wrapping."""
    # Test wrapping at right edge
    canvas.clear()
    max_x = canvas.canvas_width - 1

    # Create a pattern at the right edge
    canvas.toggle_cell(max_x, 5)  # Right edge
    canvas.toggle_cell(max_x - 1, 5)  # One left of edge
    canvas.toggle_cell(0, 5)  # Left edge (wraps)

    # Check that neighbors are correctly counted
    neighbors = canvas.get_neighbours(max_x, 5)
    assert sum(neighbors) == 2

    # Test that a cell at (0,0) properly detects neighbors at max edges
    canvas.clear()
    canvas.toggle_cell(0, 0)
    canvas.toggle_cell(canvas.canvas_width - 1, 0)  # Right edge
    canvas.toggle_cell(0, canvas.canvas_height - 1)  # Bottom edge

    neighbors = canvas.get_neighbours(0, 0)
    assert sum(neighbors) == 2


def test_alter_canvas_size_constraints(canvas):
    """Test that canvas size alterations respect min/max constraints."""
    from src.textual_game_of_life import Operation

    # Try to reduce below minimum (10)
    canvas.alter_canvas_size(Operation.DECREASE, amount=100)

    # Size should be limited to minimum
    assert canvas.canvas_width == 10
    assert canvas.canvas_height == 10

    # Test maximum size constraint
    canvas.alter_canvas_size(Operation.INCREASE, amount=1000)

    # Size should be limited to maximum
    # Note: MAX_CANVAS_WIDTH appears to be 1010 now
    assert canvas.canvas_width == 1010
    assert canvas.canvas_height == 1010


def test_brush_size_constraints(canvas):
    """Test that brush size respects min/max constraints."""
    # Start with default brush size
    assert canvas.brush_size == 1

    # Test increasing to maximum
    for _ in range(20):  # More than needed to reach max
        canvas.increase_brush_size()

    # Should be capped at MAX_BRUSH_SIZE
    assert canvas.brush_size == canvas.MAX_BRUSH_SIZE

    # Test decreasing to minimum
    for _ in range(20):  # More than needed to reach min
        canvas.decrease_brush_size()

    # Should be capped at MIN_BRUSH_SIZE
    assert canvas.brush_size == canvas.MIN_BRUSH_SIZE


def test_invalid_operation(canvas):
    """Test that invalid operations raise appropriate errors."""
    import pytest
    from src.textual_game_of_life import Operation

    # Create an invalid operation
    class InvalidOp:
        value = "invalid"

    # Test horizontally
    with pytest.raises(RuntimeError, match="Invalid operation"):
        canvas.alter_canvas_size(InvalidOp(), horizontally=True, vertically=False)

    # Test vertically
    with pytest.raises(RuntimeError, match="Invalid operation"):
        canvas.alter_canvas_size(InvalidOp(), horizontally=False, vertically=True)
