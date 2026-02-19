from django.db import models
from django.conf import settings

from project.models import Family


class Task(models.Model):
	title = models.CharField(max_length=255)
	description = models.TextField(blank=True)
	due_date = models.DateField(blank=True, null=True)
	family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='tasks')
	created_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='created_tasks',
	)
	completed = models.BooleanField(default=False)
	completed_at = models.DateTimeField(blank=True, null=True)
	completed_by = models.ManyToManyField(
		settings.AUTH_USER_MODEL,
		blank=True,
		related_name='completed_tasks',
	)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['completed', 'due_date', '-created_at']

	def __str__(self):
		return self.title
