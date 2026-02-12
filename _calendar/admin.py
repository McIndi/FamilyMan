from django.contrib import admin
from .models import Event

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'when', 'host', 'duration', 'repeat')
    list_filter = ('when', 'repeat')
    search_fields = ('title', 'text')
