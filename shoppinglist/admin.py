from django.contrib import admin
from .models import Item

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Item model.
    """
    list_display = ('id', 'text', 'kind', 'obtained')  # Display these fields in the admin list view.
    list_filter = ('kind', 'obtained')  # Add a filter for the 'kind' field.
    search_fields = ('text',)  # Enable search by the 'text' field.
