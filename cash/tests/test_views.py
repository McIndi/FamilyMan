"""View tests for cash app."""

import io
import json
import tempfile
from datetime import datetime, time, timedelta

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
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

    def test_dashboard_renders_chart_data(self):
        """Dashboard returns chart data arrays matching the days window."""
        response = self.client.get(
            reverse("cash_transaction_dashboard"),
            {"days": "60", "window": "30"},
        )
        self.assertEqual(response.status_code, 200)
        chart_data = json.loads(response.context["chart_data"])
        self.assertEqual(len(chart_data["dates"]), 60)
        self.assertEqual(len(chart_data["rolling_income"]), 60)
        self.assertEqual(len(chart_data["rolling_expenses"]), 60)
        self.assertEqual(len(chart_data["rolling_net"]), 60)

    def test_dashboard_clamps_days_and_window(self):
        """Dashboard clamps days and rolling window query params."""
        response = self.client.get(
            reverse("cash_transaction_dashboard"),
            {"days": "5", "window": "400"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["days"], 30)
        self.assertEqual(response.context["window"], 30)

    def test_dashboard_filters_records_by_window(self):
        """Dashboard tables show only records inside the selected window."""
        days = 30
        end_date = timezone.localdate()
        start_date = end_date - timedelta(days=days - 1)

        old_expense = Expense.objects.create(
            user=self.user,
            family=self.family,
            amount="10.00",
            note="Old",
        )
        in_range_expense = Expense.objects.create(
            user=self.user,
            family=self.family,
            amount="12.00",
            note="Current",
        )

        old_dt = timezone.make_aware(datetime.combine(start_date - timedelta(days=1), time(12, 0)))
        in_range_dt = timezone.make_aware(datetime.combine(end_date, time(12, 0)))
        Expense.objects.filter(id=old_expense.id).update(date=old_dt)
        Expense.objects.filter(id=in_range_expense.id).update(date=in_range_dt)

        response = self.client.get(
            reverse("cash_transaction_dashboard"),
            {"days": str(days)},
        )
        self.assertEqual(response.status_code, 200)
        expenses = list(response.context["expenses"])
        self.assertIn(in_range_expense, expenses)
        self.assertNotIn(old_expense, expenses)

    def test_dashboard_rolling_values_include_events(self):
        """Rolling totals include values inside the window."""
        days = 10
        window = 10
        end_date = timezone.localdate()
        start_date = end_date - timedelta(days=days - 1)

        fund_one = Fund.objects.create(user=self.user, family=self.family, amount="100.00", note="Start")
        fund_two = Fund.objects.create(user=self.user, family=self.family, amount="50.00", note="End")
        expense = Expense.objects.create(user=self.user, family=self.family, amount="30.00", note="Bill")

        start_dt = timezone.make_aware(datetime.combine(start_date, time(12, 0)))
        end_dt = timezone.make_aware(datetime.combine(end_date, time(12, 0)))
        Fund.objects.filter(id=fund_one.id).update(date=start_dt)
        Fund.objects.filter(id=fund_two.id).update(date=end_dt)
        Expense.objects.filter(id=expense.id).update(date=start_dt)

        response = self.client.get(
            reverse("cash_transaction_dashboard"),
            {"days": str(days), "window": str(window)},
        )
        self.assertEqual(response.status_code, 200)
        chart_data = json.loads(response.context["chart_data"])
        self.assertEqual(chart_data["rolling_income"][-1], 150.0)
        self.assertEqual(chart_data["rolling_expenses"][-1], 30.0)
        self.assertEqual(chart_data["rolling_net"][-1], 120.0)

    def test_dashboard_redirects_without_family(self):
        """Dashboard redirects to family switch when no family is selected."""
        other_user = get_user_model().objects.create_user("orphan", password="Password123!")
        self.client.force_login(other_user)
        response = self.client.get(reverse("cash_transaction_dashboard"))
        self.assertRedirects(response, reverse("switch_family"), target_status_code=302)
