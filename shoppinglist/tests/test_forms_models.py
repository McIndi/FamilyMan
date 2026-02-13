"""Form and model tests for shoppinglist app."""

from django.test import TestCase

from shoppinglist.forms import ItemForm
from shoppinglist.models import Item
from project.models import Family


class ShoppinglistFormModelTests(TestCase):
    """Tests for item form and model behavior."""

    def test_item_form_excludes_family(self):
        """ItemForm omits the family field."""
        form = ItemForm()
        self.assertNotIn("family", form.fields)

    def test_item_str(self):
        """Item __str__ returns the item text."""
        family = Family.objects.create(name="Grocers")
        item = Item.objects.create(family=family, text="Milk", kind="need")
        self.assertEqual(str(item), "Milk")
