"""Form and model tests for merits app."""

from django.contrib.auth import get_user_model
from django.test import TestCase

from merits.forms import DemeritForm, MeritForm
from merits.models import Merit


class MeritsFormModelTests(TestCase):
    """Tests for merit form and model behavior."""

    def test_merit_form_fields(self):
        """MeritForm exposes child, description, and weight fields."""
        form = MeritForm()
        self.assertIn("child", form.fields)
        self.assertIn("description", form.fields)
        self.assertIn("weight", form.fields)

    def test_merit_str(self):
        """Merit __str__ includes username and description."""
        user = get_user_model().objects.create_user("child", password="Password123!")
        merit = Merit.objects.create(child=user, description="Chores", weight=2, creator=user)
        self.assertIn("child", str(merit))
        self.assertIn("Chores", str(merit))

    def test_merit_weight_rejects_negative(self):
        """MeritForm rejects negative weight values."""
        child = get_user_model().objects.create_user("kid1", password="Password123!")
        form = MeritForm(data={"child": child.id, "description": "Test", "weight": -1})
        self.assertFalse(form.is_valid())
        self.assertIn("weight", form.errors)

    def test_demerit_weight_rejects_negative(self):
        """DemeritForm rejects negative weight values."""
        child = get_user_model().objects.create_user("kid2", password="Password123!")
        form = DemeritForm(data={"child": child.id, "description": "Test", "weight": -2})
        self.assertFalse(form.is_valid())
        self.assertIn("weight", form.errors)

    def test_merit_weight_rejects_scientific_notation(self):
        """MeritForm rejects scientific notation values."""
        child = get_user_model().objects.create_user("kid3", password="Password123!")
        form = MeritForm(data={"child": child.id, "description": "Test", "weight": "1e2"})
        self.assertFalse(form.is_valid())
        self.assertIn("weight", form.errors)

    def test_demerit_weight_rejects_scientific_notation(self):
        """DemeritForm rejects scientific notation values."""
        child = get_user_model().objects.create_user("kid4", password="Password123!")
        form = DemeritForm(data={"child": child.id, "description": "Test", "weight": "2e1"})
        self.assertFalse(form.is_valid())
        self.assertIn("weight", form.errors)
