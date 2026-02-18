"""View tests for mail app."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from mail.models import Message, Recipient
from project.models import Family, Membership


class MailViewTests(TestCase):
    """Tests for mail views."""

    def setUp(self):
        """Create users, family, and login session."""
        self.sender = get_user_model().objects.create_user("sender", password="Password123!")
        self.recipient = get_user_model().objects.create_user("recipient", password="Password123!")
        self.outsider = get_user_model().objects.create_user("outsider", password="Password123!")
        self.family = Family.objects.create(name="MailFamily")
        self.other_family = Family.objects.create(name="OtherFamily")
        Membership.objects.create(user=self.sender, family=self.family, role="parent")
        Membership.objects.create(user=self.recipient, family=self.family, role="child")
        Membership.objects.create(user=self.outsider, family=self.other_family, role="parent")
        self.client.force_login(self.sender)
        self._set_current_family(self.family)

    def _set_current_family(self, family):
        """Attach current family to session."""
        session = self.client.session
        session["current_family_id"] = family.id
        session.save()

    def test_compose_message_creates_recipients(self):
        """Compose view creates a message and recipient rows."""
        response = self.client.post(
            reverse("compose_message"),
            {"subject": "Hi", "body": "Hello", "recipients": [self.recipient.id]},
        )
        self.assertEqual(response.status_code, 302)
        message = Message.objects.get(subject="Hi")
        self.assertEqual(message.family, self.family)
        self.assertTrue(Recipient.objects.filter(message=message, recipient=self.recipient).exists())

    def test_inbox_lists_messages(self):
        """Inbox view paginates recipient messages."""
        message = Message.objects.create(
            family=self.family,
            subject="Update",
            body="Body",
            sender=self.sender,
        )
        Recipient.objects.create(message=message, recipient=self.sender)
        response = self.client.get(reverse("inbox"), {"page": 1})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(hasattr(response.context["page_obj"], "object_list"))

    def test_message_detail_marks_read(self):
        """Message detail sets read_at when opened."""
        message = Message.objects.create(
            family=self.family,
            subject="Note",
            body="Body",
            sender=self.sender,
        )
        recipient = Recipient.objects.create(message=message, recipient=self.sender)
        response = self.client.get(reverse("message_detail", args=[message.id]))
        self.assertEqual(response.status_code, 200)
        recipient.refresh_from_db()
        self.assertIsNotNone(recipient.read_at)

    def test_delete_message_by_sender(self):
        """Sender deletion removes message and recipients."""
        message = Message.objects.create(
            family=self.family,
            subject="Delete",
            body="Body",
            sender=self.sender,
        )
        Recipient.objects.create(message=message, recipient=self.sender)
        response = self.client.post(reverse("delete_message", args=[message.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Message.objects.filter(id=message.id).exists())

    def test_edit_message(self):
        """Edit view updates message fields."""
        message = Message.objects.create(
            family=self.family,
            subject="Old",
            body="Body",
            sender=self.sender,
        )
        response = self.client.post(
            reverse("edit_message", args=[message.id]),
            {"subject": "New", "body": "Body", "recipients": [self.recipient.id]},
        )
        self.assertEqual(response.status_code, 302)
        message.refresh_from_db()
        self.assertEqual(message.subject, "New")

    def test_message_detail_forbidden_for_non_participant(self):
        """Only sender or listed recipients can view a message."""
        message = Message.objects.create(
            family=self.family,
            subject="Private",
            body="Body",
            sender=self.sender,
        )
        Recipient.objects.create(message=message, recipient=self.recipient)

        self.client.force_login(self.outsider)
        self._set_current_family(self.other_family)
        response = self.client.get(reverse("message_detail", args=[message.id]))

        self.assertEqual(response.status_code, 404)

    def test_sender_can_view_message_detail_without_recipient_row(self):
        """Message sender can view detail even without being in Recipient table."""
        message = Message.objects.create(
            family=self.family,
            subject="Sender access",
            body="Body",
            sender=self.sender,
        )
        Recipient.objects.create(message=message, recipient=self.recipient)

        response = self.client.get(reverse("message_detail", args=[message.id]))
        self.assertEqual(response.status_code, 200)

    def test_compose_rejects_recipient_outside_current_family(self):
        """Compose form only accepts recipients in current family."""
        response = self.client.post(
            reverse("compose_message"),
            {"subject": "Hi", "body": "Body", "recipients": [self.outsider.id]},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Message.objects.filter(subject="Hi", body="Body").exists())
