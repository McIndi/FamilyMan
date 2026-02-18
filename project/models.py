from django.contrib.auth.models import AbstractUser
from django.db import models
import os
from uuid import uuid4


def user_profile_pic_path(instance, filename):
    """Generate a standardized path for user profile pictures."""
    ext = filename.split('.')[-1]
    filename = f"user_{instance.id}_{uuid4().hex[:8]}.{ext}"
    return os.path.join('profile_pics', filename)


class CustomUser(AbstractUser):
    """
    Custom user model extending the default Django user.
    """
    child = models.BooleanField(default=True)
    bio = models.TextField(blank=True, null=True, help_text="Tell us about yourself")
    profile_pic = models.ImageField(upload_to=user_profile_pic_path, blank=True, null=True)

CustomUser.add_to_class('families', models.ManyToManyField('Family', through='Membership', related_name='members'))

class Family(models.Model):
    """
    Represents a family group. Users can belong to multiple families.
    """
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Membership(models.Model):
    """
    Represents the relationship between a user and a family.
    """
    ROLE_CHOICES = [
        ('parent', 'Parent'),
        ('child', 'Child'),
    ]
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    family = models.ForeignKey(Family, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'family')

    def __str__(self):
        return f"{self.user.username} ({self.role}) in {self.family.name}"
