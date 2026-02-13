"""API tests for shoppinglist app."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from project.models import Family, Membership
from shoppinglist.models import Item


class ShoppinglistApiTests(TestCase):
    """Tests for ItemViewSet API."""

    def setUp(self):
        """Create user, family, and API client."""
        self.user = get_user_model().objects.create_user("apiuser", password="Password123!")
        self.family = Family.objects.create(name="ApiFamily")
        Membership.objects.create(user=self.user, family=self.family, role="parent")
        self.client = APIClient()
        # Use session-backed auth so FamilyContextMiddleware can attach current_family.
        self.client.force_login(self.user)
        self._set_current_family(self.family)

    def _set_current_family(self, family):
        """Attach current family to session for middleware."""
        session = self.client.session
        session["current_family_id"] = family.id
        session.save()

    def test_api_create_item(self):
        """API create stores family-scoped item."""
        response = self.client.post(
            "/shoppinglist/api/shoppinglist/",
            {"text": "Apples", "kind": "need", "obtained": False},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        item = Item.objects.get(text="Apples")
        self.assertEqual(item.family, self.family)

    def test_api_list_items(self):
        """API list returns family items only."""
        Item.objects.create(family=self.family, text="Bananas", kind="need")
        response = self.client.get("/shoppinglist/api/shoppinglist/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
