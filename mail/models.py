from django.db import models
from django.conf import settings
from django.db.models.signals import post_delete
from django.dispatch import receiver

# Create your models here.

class Message(models.Model):
    subject = models.CharField(max_length=255)
    body = models.TextField()
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        editable=False,
    )
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.subject

class Recipient(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='recipients')
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages')
    read_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.recipient.username} - {self.message.subject}"
