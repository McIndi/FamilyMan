"""Model tests for project app."""

from django.contrib.auth import get_user_model
from django.test import TestCase

from project.models import Family, Membership


class ProjectModelTests(TestCase):
    """Tests for Family and Membership models."""

    def test_family_str(self):
        """Family __str__ returns its name."""
        family = Family.objects.create(name="House")
        self.assertEqual(str(family), "House")

    def test_membership_str(self):
        """Membership __str__ includes username, role, and family name."""
        user = get_user_model().objects.create_user(username="member", password="Password123!")
        family = Family.objects.create(name="Team")
        membership = Membership.objects.create(user=user, family=family, role="parent")
        self.assertIn("member", str(membership))
        self.assertIn("parent", str(membership))
        self.assertIn("Team", str(membership))
