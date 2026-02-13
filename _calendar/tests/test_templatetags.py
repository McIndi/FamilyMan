"""Tests for _calendar template tags."""

from datetime import date, timedelta

from django.test import TestCase
from django.utils import timezone

from _calendar.templatetags.week_start import week_start
from _calendar.templatetags.date_range import date_range
from _calendar.templatetags.range_filter import range_filter


class CalendarTemplateTagTests(TestCase):
    """Tests for template tag utilities."""

    def test_week_start_is_monday(self):
        """week_start returns the Monday for the current week."""
        today = timezone.localdate()
        monday = today - timedelta(days=today.weekday())
        self.assertEqual(week_start(), monday)

    def test_date_range_inclusive(self):
        """date_range yields an inclusive list of dates."""
        start = date(2026, 1, 1)
        end = date(2026, 1, 3)
        dates = list(date_range(start, end))
        self.assertEqual(dates, [date(2026, 1, 1), date(2026, 1, 2), date(2026, 1, 3)])

    def test_range_filter(self):
        """range_filter returns a range of the given size."""
        self.assertEqual(list(range_filter(3)), [0, 1, 2])
