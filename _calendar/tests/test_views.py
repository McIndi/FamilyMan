"""View tests for _calendar app."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from _calendar.models import Event
from project.models import Family, Membership


class CalendarViewTests(TestCase):
    """Tests for calendar views."""

    def setUp(self):
        """Create user, family, and permissions."""
        self.user = get_user_model().objects.create_user("host", password="Password123!")
        self.outsider = get_user_model().objects.create_user("outsider", password="Password123!")
        self.family = Family.objects.create(name="EventFamily")
        self.other_family = Family.objects.create(name="OtherEventFamily")
        Membership.objects.create(user=self.user, family=self.family, role="parent")
        Membership.objects.create(user=self.outsider, family=self.other_family, role="parent")
        self.client.force_login(self.user)
        self._set_current_family(self.family)

    def _set_current_family(self, family):
        """Attach current family to session."""
        session = self.client.session
        session["current_family_id"] = family.id
        session.save()

    def test_event_create(self):
        """Event create stores event with host and family."""
        when = (timezone.now() + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M")
        response = self.client.post(
            reverse("event_create"),
            {
                "title": "Party",
                "text": "Bring snacks",
                "when": when,
                "duration": "00:30:00",
                "repeat": "false",
                "attendees": [self.user.id],
            },
        )
        self.assertEqual(response.status_code, 302)
        event = Event.objects.get(title="Party")
        self.assertEqual(event.host, self.user)
        self.assertEqual(event.family, self.family)

    def test_day_view_lists_events(self):
        """Day view includes events for the selected date."""
        event_time = timezone.now() + timedelta(days=1)
        event = Event.objects.create(
            family=self.family,
            title="Checkup",
            text="Doctor",
            when=event_time,
            host=self.user,
            duration=timedelta(minutes=15),
            repeat="false",
        )
        event.attendees.add(self.user)
        response = self.client.get(
            reverse("day_view", args=[event_time.year, event_time.month, event_time.day])
        )
        self.assertEqual(response.status_code, 200)
        events = response.context["events"]
        self.assertTrue(any(evt.id == event.id for evt, _ in events))

    def test_event_create_rejects_attendee_outside_family(self):
        """Event create blocks attendees that are not in current family."""
        when = (timezone.now() + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M")
        response = self.client.post(
            reverse("event_create"),
            {
                "title": "Private",
                "text": "Family only",
                "when": when,
                "duration": "00:30:00",
                "repeat": "false",
                "attendees": [self.outsider.id],
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Event.objects.filter(title="Private").exists())

    def test_day_view_redirects_without_family(self):
        """Calendar views redirect to family switch when no family is selected."""
        another_family = Family.objects.create(name="AnotherEventFamily")
        Membership.objects.create(user=self.user, family=another_family, role="parent")
        session = self.client.session
        session.pop("current_family_id", None)
        session.save()

        today = timezone.localdate()
        response = self.client.get(reverse("day_view", args=[today.year, today.month, today.day]))

        self.assertRedirects(response, reverse("switch_family"), target_status_code=302)
