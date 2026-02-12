from django.contrib import admin
from .models import Message, Recipient

class RecipientInline(admin.TabularInline):
    model = Recipient
    extra = 1  # Number of empty forms to display

# Registering the Message and Recipient models
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'sender', 'sent_at')
    search_fields = ('subject', 'body', 'sender__username')
    list_filter = ('sent_at',)
    readonly_fields = ('sent_at', 'sender')
    inlines = [RecipientInline]  # Add the inline

@admin.register(Recipient)
class RecipientAdmin(admin.ModelAdmin):
    list_display = ('message', 'recipient', 'read_at')
    search_fields = ('message__subject', 'recipient__username')
    list_filter = ('read_at',)
    fieldsets = (
        (None, {
            'fields': ('message', 'recipient')
        }),
        ('Read Information', {
            'fields': ('read_at',),
            'classes': ('collapse',)
        }),
    )

