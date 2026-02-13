"""Form and model tests for mail app."""

from django.contrib.auth import get_user_model
from django.test import TestCase

from mail.forms import MessageForm
from mail.models import Message
from project.models import Family


class MailFormModelTests(TestCase):
    """Tests for mail forms and models."""

    def test_message_form_includes_recipients(self):
        """MessageForm defines a recipients field."""
        form = MessageForm()
        self.assertIn("recipients", form.fields)

    def test_message_str(self):
        """Message __str__ returns the subject."""
        user = get_user_model().objects.create_user("sender", password="Password123!")
        family = Family.objects.create(name="MailFamily")
        message = Message.objects.create(
            family=family,
            subject="Hello",
            body="Body",
            sender=user,
        )
        self.assertEqual(str(message), "Hello")
