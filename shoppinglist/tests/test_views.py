"""View tests for shoppinglist app."""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from project.models import Family, Membership
from shoppinglist.models import Item


class ShoppinglistViewTests(TestCase):
    """Tests for shopping list views."""

    def setUp(self):
        """Create user, family, and permissions."""
        self.user = get_user_model().objects.create_user("shopper", password="Password123!")
        self.family = Family.objects.create(name="Grocers")
        Membership.objects.create(user=self.user, family=self.family, role="parent")
        self.client.force_login(self.user)
        self._set_current_family(self.family)
        self._grant_permissions(self.user)

    def _set_current_family(self, family):
        """Attach current family to session."""
        session = self.client.session
        session["current_family_id"] = family.id
        session.save()

    def _grant_permissions(self, user):
        """Grant item permissions for view and mutation."""
        codenames = ["view_item", "add_item", "change_item", "delete_item"]
        for codename in codenames:
            permission = Permission.objects.get(codename=codename)
            user.user_permissions.add(permission)

    def test_item_create(self):
        """Create view stores an item for the family."""
        response = self.client.post(
            reverse("item_create"),
            {"text": "Eggs", "kind": "need"},
        )
        self.assertEqual(response.status_code, 302)
        item = Item.objects.get(text="Eggs")
        self.assertEqual(item.family, self.family)

    def test_item_update(self):
        """Update view changes item fields."""
        item = Item.objects.create(family=self.family, text="Bread", kind="need")
        response = self.client.post(
            reverse("item_update", args=[item.id]),
            {"text": "Bread", "kind": "want", "obtained": False},
        )
        self.assertEqual(response.status_code, 302)
        item.refresh_from_db()
        self.assertEqual(item.kind, "want")

    def test_item_delete(self):
        """Delete view removes the item."""
        item = Item.objects.create(family=self.family, text="Cheese", kind="need")
        response = self.client.post(reverse("item_delete", args=[item.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Item.objects.filter(id=item.id).exists())

    def test_download_shopping_list_needs(self):
        """Download view returns markdown with Needs header."""
        Item.objects.create(family=self.family, text="Milk", kind="need", obtained=False)
        response = self.client.get(reverse("download_shopping_list"), {"kind": "need"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"# Needs", response.content)
