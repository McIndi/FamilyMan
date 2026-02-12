from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    """
    Custom user model extending the default Django user.
    """
    child = models.BooleanField(default=True)

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
