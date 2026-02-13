"""View tests for merits app."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from merits.models import Merit, Demerit
from project.models import Family, Membership


class MeritsViewTests(TestCase):
    """Tests for merit and demerit views."""

    def setUp(self):
        """Create a parent, child, and family."""
        self.parent = get_user_model().objects.create_user("parent", password="Password123!")
        self.child = get_user_model().objects.create_user("child", password="Password123!")
        self.family = Family.objects.create(name="MeritFamily")
        Membership.objects.create(user=self.parent, family=self.family, role="parent")
        Membership.objects.create(user=self.child, family=self.family, role="child")
        self.client.force_login(self.parent)
        self._set_current_family(self.family)

    def _set_current_family(self, family):
        """Attach current family to session."""
        session = self.client.session
        session["current_family_id"] = family.id
        session.save()

    def test_merit_dashboard_renders(self):
        """Merit dashboard renders for parent users."""
        response = self.client.get(reverse("merit_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("score_by_child", response.context)

    def test_add_merit_creates_merit(self):
        """Add merit stores a merit for a child in family."""
        response = self.client.post(
            reverse("add_merit"),
            {"merit-child": self.child.id, "merit-description": "Helped", "merit-weight": 1},
        )
        self.assertEqual(response.status_code, 302)
        merit = Merit.objects.get(description="Helped")
        self.assertEqual(merit.child, self.child)
        self.assertEqual(merit.creator, self.parent)

    def test_add_demerit_creates_demerit(self):
        """Add demerit stores a demerit for a child in family."""
        response = self.client.post(
            reverse("add_demerit"),
            {"demerit-child": self.child.id, "demerit-description": "Late", "demerit-weight": 2},
        )
        self.assertEqual(response.status_code, 302)
        demerit = Demerit.objects.get(description="Late")
        self.assertEqual(demerit.child, self.child)
        self.assertEqual(demerit.creator, self.parent)
