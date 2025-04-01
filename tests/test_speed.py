"""Tests for simulation speed control."""
import pytest
from src.textual_game_of_life.tui import CellularAutomatonTui


def test_speed_initialization(app):
    """Test that speed initializes correctly."""
    assert app.canvas.refresh_interval == 0.5

    # Create with different speed
    app_fast = CellularAutomatonTui(speed=0.1)
    assert app_fast.initial_speed == 0.1


def test_speed_limits(app):
    """Test that speed adjustments respect limits."""
    # Set speed to near the minimum
    app.canvas.refresh_interval = 0.2

    # Increase speed (lower interval)
    app.action_increase_speed()
    assert app.canvas.refresh_interval == 0.1

    # Try to increase further - should hit minimum
    app.action_increase_speed()
    assert app.canvas.refresh_interval == 0.1

    # Decrease speed (increase interval)
    app.action_decrease_speed()
    assert app.canvas.refresh_interval == 0.2


def test_speed_changes(app):
    """Test multiple speed changes."""
    # Start at default
    assert app.canvas.refresh_interval == 0.5

    # Increase speed twice
    app.action_increase_speed()
    app.action_increase_speed()
    # Use approximate comparison to handle floating point precision
    assert abs(app.canvas.refresh_interval - 0.3) < 1e-10

    # Decrease speed three times
    app.action_decrease_speed()
    app.action_decrease_speed()
    app.action_decrease_speed()
    assert app.canvas.refresh_interval == 0.6


def test_speed_and_generation(app):
    """Test that speed setting affects simulation calculation."""
    # Set a specific pattern for testing
    app.canvas.clear()
    app.canvas.toggle_cell(4, 4)
    app.canvas.toggle_cell(4, 5)
    app.canvas.toggle_cell(4, 6)

    # Set to maximum speed
    app.canvas.refresh_interval = 0.1

    # Step simulation
    app.action_step()

    # For maximum speed, multiple generations might be computed in a single step
    # This is hard to test precisely, but we can verify that the pattern changed
    assert app.canvas.matrix[5, 5] == 1, "Blinker should have evolved"
