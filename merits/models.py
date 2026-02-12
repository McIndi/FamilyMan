from django.db import models
from django.contrib.auth import get_user_model

class Merit(models.Model):
    """
    Model representing a merit point system for children.
    """
    child = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='merits')
    date_awarded = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    weight = models.IntegerField(default=1)
    creator = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='created_merits')

    def __str__(self):
        return f"{self.child.username} - {self.description}"

class Demerit(models.Model):
    """
    Model representing a demerit point system for children.
    """
    child = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='demerits')
    date_awarded = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    weight = models.IntegerField(default=1)
    creator = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='created_demerits')

    def __str__(self):
        return f"{self.child.username} - {self.description}"
