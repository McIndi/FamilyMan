"""Form tests for _calendar app."""

from django.test import TestCase

from _calendar.forms import EventForm


class EventFormTests(TestCase):
    """Tests for EventForm behavior."""

    def test_host_excluded_on_create(self):
        """Host field is removed when creating a new event."""
        form = EventForm()
        self.assertNotIn("host", form.fields)
