"""View tests for cash app."""

import io
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from cash.models import Category, Expense, Fund, Receipt
from project.models import Family, Membership


class CashViewTests(TestCase):
    """Tests for cash views."""

    def setUp(self):
        """Create a user, family, and login session."""
        self.user = get_user_model().objects.create_user("spender", password="Password123!")
        self.family = Family.objects.create(name="Budget")
        Membership.objects.create(user=self.user, family=self.family, role="parent")
        self.client.force_login(self.user)
        self._set_current_family(self.family)

    def _set_current_family(self, family):
        """Attach current family to session."""
        session = self.client.session
        session["current_family_id"] = family.id
        session.save()

    def test_add_category_in_add_expense(self):
        """Add expense view can create a category via add_category POST."""
        response = self.client.post(
            reverse("add_expense"),
            {"add_category": "1", "name": "Utilities", "description": "Bills"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Category.objects.filter(name="Utilities", family=self.family).exists())

    def test_add_expense_creates_expense(self):
        """Add expense view stores an expense and redirects to receipt upload."""
        category = Category.objects.create(family=self.family, name="Food")
        response = self.client.post(
            reverse("add_expense"),
            {"amount": "12.34", "category": category.id, "note": "Lunch"},
        )
        self.assertEqual(response.status_code, 302)
        expense = Expense.objects.get(note="Lunch")
        self.assertEqual(expense.family, self.family)

    def test_add_fund_creates_fund(self):
        """Add fund view stores a fund for the current family."""
        response = self.client.post(
            reverse("add_fund"),
            {"amount": "50.00", "note": "Allowance"},
        )
        self.assertEqual(response.status_code, 302)
        fund = Fund.objects.get(note="Allowance")
        self.assertEqual(fund.family, self.family)

    def test_upload_receipt_creates_receipt(self):
        """Upload receipt stores an image file on the expense."""
        category = Category.objects.create(family=self.family, name="Travel")
        expense = Expense.objects.create(
            user=self.user,
            family=self.family,
            category=category,
            amount="20.00",
            note="Taxi",
        )
        # Use Pillow to generate a valid PNG payload for ImageField validation.
        image_buffer = io.BytesIO()
        Image.new("RGB", (1, 1), color=(255, 255, 255)).save(image_buffer, format="PNG")
        image = SimpleUploadedFile(
            "receipt.png",
            image_buffer.getvalue(),
            content_type="image/png",
        )
        with tempfile.TemporaryDirectory() as media_root:
            # Use a temp media root so uploaded files are cleaned up automatically.
            with override_settings(MEDIA_ROOT=media_root):
                response = self.client.post(
                    reverse("upload_receipt", args=[expense.id]),
                    {"image": image},
                )
                self.assertEqual(response.status_code, 302)
                self.assertTrue(Receipt.objects.filter(expense=expense).exists())

    def test_cash_transaction_list_filters(self):
        """Transaction list respects search and period filters."""
        Fund.objects.create(user=self.user, family=self.family, amount="100.00", note="Paycheck")
        category = Category.objects.create(family=self.family, name="Groceries")
        Expense.objects.create(
            user=self.user,
            family=self.family,
            category=category,
            amount="25.00",
            note="Store",
        )
        response = self.client.get(
            reverse("cash_transaction_list"),
            {"period": "month", "search": "Store"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("family_cash", response.context)
