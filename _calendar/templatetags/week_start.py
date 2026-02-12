from datetime import timedelta

from django import template
from django.utils import timezone

register = template.Library()


@register.simple_tag
def week_start():
    today = timezone.localdate()
    # Week starts on Monday; change to 6 for Sunday-based weeks.
    return today - timedelta(days=today.weekday())
