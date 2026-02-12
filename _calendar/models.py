from django.db import models
from django.contrib.auth import get_user_model
from datetime import timedelta

class Event(models.Model):
    REPEAT_CHOICES = [
        ('false', 'Does not repeat'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('bi-monthly', 'Bi-Monthly'),
        ('semi-annually', 'Semi-Annually'),
        ('annually', 'Annually'),
    ]

    title = models.CharField(max_length=255)
    text = models.TextField()
    when = models.DateTimeField()
    attendees = models.ManyToManyField(get_user_model(), related_name='event_attendees')
    host = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='hosted_events')
    duration = models.DurationField()
    repeat = models.CharField(max_length=20, choices=REPEAT_CHOICES, default='false')

    def __str__(self):
        return self.title

    def upcoming(self, count=4):
        from django.utils.timezone import now
        from datetime import timedelta

        upcoming_occurrences = []
        if self.repeat == 'false':
            if self.when >= now():
                upcoming_occurrences.append(self.when)
        else:
            current_time = self.when
            while len(upcoming_occurrences) < count and current_time >= now():
                upcoming_occurrences.append(current_time)
                if self.repeat == 'daily':
                    current_time += timedelta(days=1)
                elif self.repeat == 'weekly':
                    current_time += timedelta(weeks=1)
                elif self.repeat == 'monthly':
                    current_time += timedelta(days=30)  # Approximation
                elif self.repeat == 'bi-monthly':
                    current_time += timedelta(days=60)  # Approximation
                elif self.repeat == 'semi-annually':
                    current_time += timedelta(days=182)  # Approximation
                elif self.repeat == 'annually':
                    current_time += timedelta(days=365)
        return sorted(upcoming_occurrences)[:count]

    @classmethod
    def get_occurrences_in_range(cls, start_date, end_date):
        events = cls.objects.all()
        occurrences = []
        for event in events:
            current_time = event.when
            while current_time <= end_date:
                if current_time >= start_date:
                    occurrences.append((event, current_time))  # Return a tuple of event and occurrence date
                if event.repeat == 'false':
                    break
                elif event.repeat == 'daily':
                    current_time += timedelta(days=1)
                elif event.repeat == 'weekly':
                    current_time += timedelta(weeks=1)
                elif event.repeat == 'monthly':
                    current_time += timedelta(days=30)  # Approximation
                elif event.repeat == 'bi-monthly':
                    current_time += timedelta(days=60)  # Approximation
                elif event.repeat == 'semi-annually':
                    current_time += timedelta(days=182)  # Approximation
                elif event.repeat == 'annually':
                    current_time += timedelta(days=365)
        return occurrences
    
    def is_recurring(self):
        return self.repeat != 'false'
