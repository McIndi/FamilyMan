
from django.db import models
from django.conf import settings
from django.utils import timezone


from project.models import Family

class Category(models.Model):
	family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='categories')
	name = models.CharField(max_length=100)
	description = models.TextField(blank=True)

	class Meta:
		unique_together = ('family', 'name')

	def __str__(self):
		return f"{self.name}"


class Fund(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='funds')
	amount = models.DecimalField(max_digits=10, decimal_places=2)
	date = models.DateTimeField(default=timezone.now, editable=True)
	note = models.CharField(max_length=255, blank=True)

	def __str__(self):
		return f"{self.user.username} - {self.amount} for {self.family.name} on {self.date:%Y-%m-%d}"


class Expense(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='expenses')
	category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
	amount = models.DecimalField(max_digits=10, decimal_places=2)
	date = models.DateTimeField(default=timezone.now, editable=True)
	note = models.CharField(max_length=255, blank=True)

	def __str__(self):
		return f"{self.user.username} - {self.amount} for {self.category} in {self.family.name} on {self.date:%Y-%m-%d}"


class Receipt(models.Model):
	expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name='receipts')
	family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='receipts')
	image = models.ImageField(upload_to='receipts/')
	uploaded_at = models.DateTimeField(default=timezone.now, editable=True)

	def __str__(self):
		return f"Receipt for {self.expense} in {self.family.name} on {self.uploaded_at:%Y-%m-%d %H:%M:%S}"
