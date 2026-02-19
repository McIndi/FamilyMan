from django.db import models
from django.conf import settings

from project.models import Family


class DinnerDay(models.Model):
	family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='dinner_days')
	date = models.DateField()
	dinner_eaten = models.CharField(max_length=255, blank=True)
	decided_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name='dinner_decisions',
	)
	decided_at = models.DateTimeField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['-date']
		constraints = [
			models.UniqueConstraint(
				fields=['family', 'date'],
				name='uniq_dinner_day_per_family_date',
			),
		]

	def __str__(self):
		return f"{self.family.name} dinner for {self.date}"


class DinnerOption(models.Model):
	dinner_day = models.ForeignKey(DinnerDay, on_delete=models.CASCADE, related_name='options')
	name = models.CharField(max_length=255)
	notes = models.TextField(blank=True)
	created_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='created_dinner_options',
	)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['created_at', 'id']
		constraints = [
			models.UniqueConstraint(
				fields=['dinner_day', 'name'],
				name='uniq_dinner_option_name_per_day',
			),
		]

	def __str__(self):
		return f"{self.name} ({self.dinner_day.date})"


class DinnerVote(models.Model):
	dinner_day = models.ForeignKey(DinnerDay, on_delete=models.CASCADE, related_name='votes')
	option = models.ForeignKey(DinnerOption, on_delete=models.CASCADE, related_name='votes')
	voter = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='dinner_votes',
	)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at']
		constraints = [
			models.UniqueConstraint(
				fields=['dinner_day', 'voter'],
				name='uniq_dinner_vote_per_day_per_user',
			),
			models.UniqueConstraint(
				fields=['option', 'voter'],
				name='uniq_dinner_vote_per_option_per_user',
			),
		]

	def save(self, *args, **kwargs):
		if self.option_id and self.dinner_day_id and self.option.dinner_day_id != self.dinner_day_id:
			raise ValueError('Vote option must belong to the selected dinner day.')
		super().save(*args, **kwargs)

	def __str__(self):
		return f"{self.voter} voted {self.option.name} on {self.dinner_day.date}"
