"""Form and model tests for cash app."""

from django.contrib.auth import get_user_model
from django.test import TestCase

from cash.forms import ExpenseForm, FundForm
from cash.models import Category
from project.models import Family


class CashFormModelTests(TestCase):
    """Tests for cash forms and models."""

    def setUp(self):
        """Create a user and two families."""
        self.user = get_user_model().objects.create_user("cashuser", password="Password123!")
        self.family_one = Family.objects.create(name="One")
        self.family_two = Family.objects.create(name="Two")

    def test_expense_form_filters_categories_by_family(self):
        """ExpenseForm limits category choices to the provided family."""
        Category.objects.create(family=self.family_one, name="Food")
        Category.objects.create(family=self.family_two, name="Travel")
        form = ExpenseForm(family=self.family_one)
        category_names = list(form.fields["category"].queryset.values_list("name", flat=True))
        self.assertEqual(category_names, ["Food"])

    def test_fund_form_rejects_negative_amount(self):
        """FundForm rejects negative amount values."""
        form = FundForm(data={"amount": "-1.00", "note": "Bad"})
        self.assertFalse(form.is_valid())
        self.assertIn("amount", form.errors)

    def test_expense_form_rejects_negative_amount(self):
        """ExpenseForm rejects negative amount values."""
        category = Category.objects.create(family=self.family_one, name="Fuel")
        form = ExpenseForm(data={"amount": "-5.00", "category": category.id, "note": "Bad"})
        self.assertFalse(form.is_valid())
        self.assertIn("amount", form.errors)
