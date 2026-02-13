"""Model tests for _calendar app."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from _calendar.models import Event
from project.models import Family


class EventModelTests(TestCase):
    """Tests for Event model helpers."""

    def setUp(self):
        """Create user, family, and a base event."""
        self.user = get_user_model().objects.create_user("host", password="Password123!")
        self.family = Family.objects.create(name="EventFamily")

    def test_upcoming_non_recurring(self):
        """Non-recurring events return at most one upcoming occurrence."""
        future_time = timezone.now() + timedelta(days=1)
        event = Event.objects.create(
            family=self.family,
            title="Meeting",
            text="Notes",
            when=future_time,
            host=self.user,
            duration=timedelta(minutes=30),
            repeat="false",
        )
        event.attendees.add(self.user)
        upcoming = event.upcoming(count=3, family=self.family)
        self.assertEqual(upcoming, [future_time])

    def test_get_occurrences_in_range_daily(self):
        """Recurring daily events appear within the requested range."""
        start_time = timezone.now() + timedelta(days=1)
        event = Event.objects.create(
            family=self.family,
            title="Daily",
            text="Daily event",
            when=start_time,
            host=self.user,
            duration=timedelta(minutes=15),
            repeat="daily",
        )
        event.attendees.add(self.user)
        start = start_time
        end = start_time + timedelta(days=2)
        occurrences = Event.get_occurrences_in_range(start, end, family=self.family)
        # Expect at least two occurrences in a 3-day window.
        self.assertGreaterEqual(len(occurrences), 2)

    def test_is_recurring(self):
        """is_recurring reflects the repeat flag."""
        event = Event.objects.create(
            family=self.family,
            title="One-off",
            text="Notes",
            when=timezone.now() + timedelta(days=2),
            host=self.user,
            duration=timedelta(minutes=15),
            repeat="false",
        )
        self.assertFalse(event.is_recurring())
        event.repeat = "weekly"
        self.assertTrue(event.is_recurring())
