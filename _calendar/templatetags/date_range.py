from django import template
from datetime import timedelta

register = template.Library()

@register.filter
def date_range(start_date, end_date):
    current_date = start_date
    while current_date <= end_date:
        yield current_date
        current_date += timedelta(days=1)