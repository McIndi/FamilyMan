"""Middleware tests for project app."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from project.models import Family, Membership


class FamilyContextMiddlewareTests(TestCase):
    """Tests for FamilyContextMiddleware behavior."""

    def setUp(self):
        """Create a user with one family."""
        self.user = get_user_model().objects.create_user(
            username="solo",
            password="Password123!",
        )
        self.family = Family.objects.create(name="SoloFamily")
        Membership.objects.create(user=self.user, family=self.family, role="parent")
        self.client.force_login(self.user)

    def test_auto_selects_single_family(self):
        """Middleware auto-selects the only family into session."""
        response = self.client.get(reverse("landing_page"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.session.get("current_family_id"), self.family.id)

    def test_invalid_session_family_is_cleared(self):
        """Middleware clears forged session family ids not linked to the user."""
        other_family = Family.objects.create(name="NotMine")
        session = self.client.session
        session["current_family_id"] = other_family.id
        session.save()

        response = self.client.get(reverse("landing_page"))

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(self.client.session.get("current_family_id"))
