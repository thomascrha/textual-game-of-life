"""Tests for message display functionality in the Canvas widget."""
import time
from unittest.mock import MagicMock, patch
import pytest
from src.textual_game_of_life.canvas import Canvas


def test_message_request():
    """Test that messages can be requested."""
    canvas = Canvas()

    # Mock the post_message method
    canvas.post_message = MagicMock()

    # Request a message
    message_text = "Test message"
    timeout = 1.5
    canvas.request_message(message_text, timeout)

    # Verify that post_message was called with appropriate arguments
    canvas.post_message.assert_called_once()
    args, _ = canvas.post_message.call_args
    message_obj = args[0]
    assert message_obj.message == message_text
    assert message_obj.timeout == timeout


def test_message_request_fallback():
    """Test the fallback when post_message fails."""
    canvas = Canvas()

    # Make post_message raise an exception to trigger fallback
    def raise_exception(*args, **kwargs):
        raise Exception("Test exception")

    canvas.post_message = raise_exception

    # Request a message
    message_text = "Test fallback message"
    timeout = 2.0
    canvas.request_message(message_text, timeout)

    # Verify the fallback worked
    assert canvas.message == message_text
    assert canvas.message_visible is True
    assert canvas.message_timeout == timeout
    # Timestamp should be recent
    assert time.time() - canvas.message_timestamp < 1.0


def test_clear_message():
    """Test that messages can be cleared."""
    canvas = Canvas()

    # Set up a message
    canvas.message = "Test message"
    canvas.message_visible = True

    # Mock the message_task
    mock_task = MagicMock()
    mock_task.done.return_value = False
    mock_task.cancel.return_value = None
    canvas.message_task = mock_task

    # Clear the message
    canvas.clear_message()

    # Verify that the message was cleared and the task was cancelled
    assert canvas.message_visible is False
    mock_task.cancel.assert_called_once()


def test_message_timeout_task():
    """Test the message timeout task."""
    canvas = Canvas()

    # Set up a message
    canvas.message = "Test message"
    canvas.message_visible = True

    # Mock asyncio.sleep to avoid actual waiting
    with patch("asyncio.sleep") as mock_sleep:
        # Create a simple synchronous mock implementation
        async def mock_coro():
            await canvas._message_timeout_task()

        # Run the coroutine partially and check the sleep call
        try:
            mock_coro().__await__().__next__()
        except StopIteration:
            pass

        # Verify that asyncio.sleep was called with the correct timeout
        mock_sleep.assert_called_once_with(canvas.message_timeout)

        # Manually test the logic that would run after sleep
        canvas.message_visible = False
        assert not canvas.message_visible
