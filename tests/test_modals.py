from unittest.mock import MagicMock, patch
from textual.widgets import Button
from src.textual_game_of_life.modals import About, Help


def test_about_modal_creation():
    """Test that the About modal can be created."""
    version = "1.0.0"
    about = About(version)
    assert about.version == version


def test_help_modal_content():
    """Test that the Help modal contains expected content."""
    help_modal = Help()
    assert "Step one generation" in help_modal.HELP_STRING
    assert "[b]T[/b] - Toggle auto step" in help_modal.HELP_STRING
    assert "Random canvas" in help_modal.HELP_STRING


def test_modal_button_pressed():
    """Test that button press dismisses the modal."""
    # Create About modal
    about = About("1.0.0")

    # Mock the dismiss_modal method
    about.dismiss_modal = MagicMock()

    # Create a Button.Pressed event
    button_event = Button.Pressed(Button(label="Close"))

    # Call the event handler
    about.on_button_pressed(button_event)

    # Check that dismiss_modal was called
    about.dismiss_modal.assert_called_once()


def test_modal_esc_action():
    """Test that esc key dismisses the modal."""
    # Create Help modal
    help_modal = Help()

    # Mock the dismiss_modal method
    help_modal.dismiss_modal = MagicMock()

    # Call the action handler
    help_modal.action_pop_screen()

    # Check that dismiss_modal was called
    help_modal.dismiss_modal.assert_called_once()


def test_modal_resume_animation():
    """Test that animation resumes when modal is dismissed."""
    # Create Help modal
    help_modal = Help()

    # Mock the app and canvas - avoiding direct property assignment
    app_mock = MagicMock()
    app_mock.canvas = MagicMock()
    app_mock.canvas.toggle = MagicMock(return_value=None)

    # Create a property that returns our mock
    mock_property = property(lambda self: app_mock)

    # Use patch to replace the app property (only once)
    with patch.object(Help, "app", mock_property):
        # Set was_running flag
        help_modal.was_running = True

        # Mock asyncio.create_task
        with patch("asyncio.create_task") as mock_create_task:
            # Call dismiss_modal
            help_modal.dismiss_modal()

            # Check that create_task was called with canvas.toggle()
            mock_create_task.assert_called_once_with(app_mock.canvas.toggle())

            # Check that app.pop_screen was called - moved inside the patch context
            app_mock.pop_screen.assert_called_once()
