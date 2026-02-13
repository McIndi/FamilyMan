"""View tests for project app."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from project.models import Family, Membership


class ProjectViewsTests(TestCase):
    """Tests for project app views."""

    def setUp(self):
        """Create a user, family, and logged-in session."""
        self.user = self._create_user("parent")
        self.family = Family.objects.create(name="Smith")
        Membership.objects.create(user=self.user, family=self.family, role="parent")
        self.client.force_login(self.user)
        self._set_current_family(self.family)

    def _create_user(self, username):
        """Create and return a user with a known password."""
        return get_user_model().objects.create_user(
            username=username,
            password="Password123!",
            email=f"{username}@example.com",
        )

    def _set_current_family(self, family):
        """Attach the current family id to the session."""
        session = self.client.session
        session["current_family_id"] = family.id
        session.save()

    def test_landing_page_authenticated(self):
        """Landing page renders for authenticated users."""
        response = self.client.get(reverse("landing_page"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("current_family", response.context)

    def test_signup_creates_user(self):
        """Signup creates a new user and redirects to login."""
        response = self.client.post(
            reverse("signup"),
            {
                "username": "newuser",
                "email": "newuser@example.com",
                "password1": "ComplexPass123!",
                "password2": "ComplexPass123!",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(get_user_model().objects.filter(username="newuser").exists())

    def test_add_child_creates_membership(self):
        """Add child creates a child user and membership in current family."""
        response = self.client.post(
            reverse("add_child"),
            {
                "username": "child1",
                "email": "child1@example.com",
                "password1": "ChildPass123!",
                "password2": "ChildPass123!",
            },
        )
        self.assertEqual(response.status_code, 302)
        child_user = get_user_model().objects.get(username="child1")
        self.assertTrue(
            Membership.objects.filter(user=child_user, family=self.family, role="child").exists()
        )

    def test_family_dashboard_create_family(self):
        """Family dashboard supports create_family action."""
        response = self.client.post(
            reverse("family_dashboard"),
            {"action": "create_family", "family_name": "Jones"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Family.objects.filter(name="Jones").exists())

    def test_update_role_updates_membership(self):
        """Update role changes the membership role for current user."""
        response = self.client.post(
            reverse("update_role"),
            {"family_id": self.family.id, "role": "child"},
        )
        self.assertEqual(response.status_code, 302)
        membership = Membership.objects.get(user=self.user, family=self.family)
        self.assertEqual(membership.role, "child")

    def test_switch_family_sets_session(self):
        """Switch family stores the family id in session and redirects back."""
        response = self.client.post(
            reverse("switch_family"),
            {"family_id": self.family.id},
            HTTP_REFERER=reverse("landing_page"),
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session.get("current_family_id"), str(self.family.id))
