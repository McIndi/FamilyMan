"""View tests for shoppinglist app."""

from django.contrib.auth import get_user_model
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

    def _set_current_family(self, family):
        """Attach current family to session."""
        session = self.client.session
        session["current_family_id"] = family.id
        session.save()

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

    def test_item_list_redirects_without_family(self):
        """List view redirects when there is no selected family context."""
        another_family = Family.objects.create(name="AnotherGrocers")
        Membership.objects.create(user=self.user, family=another_family, role="parent")
        session = self.client.session
        session.pop("current_family_id", None)
        session.save()

        response = self.client.get(reverse("item_list"))

        self.assertRedirects(response, reverse("switch_family"), target_status_code=302)

    def test_item_update_not_found_for_other_family_item(self):
        """Update endpoint cannot mutate items from another family."""
        other_family = Family.objects.create(name="OtherGrocers")
        item = Item.objects.create(family=other_family, text="Hidden", kind="need")

        response = self.client.post(
            reverse("item_update", args=[item.id]),
            {"text": "Visible", "kind": "want", "obtained": False},
        )

        self.assertEqual(response.status_code, 404)

    def test_child_can_create_and_update_items(self):
        """Child users can create and update items for their family."""
        child = get_user_model().objects.create_user("kid", password="Password123!")
        Membership.objects.create(user=child, family=self.family, role="child")
        self.client.force_login(child)
        self._set_current_family(self.family)

        create_response = self.client.post(
            reverse("item_create"),
            {"text": "Juice", "kind": "need"},
        )
        self.assertEqual(create_response.status_code, 302)
        item = Item.objects.get(text="Juice")

        update_response = self.client.post(
            reverse("item_update", args=[item.id]),
            {"text": "Juice", "kind": "want", "obtained": False},
        )
        self.assertEqual(update_response.status_code, 302)
        item.refresh_from_db()
        self.assertEqual(item.kind, "want")
