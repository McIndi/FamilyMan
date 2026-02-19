from django.contrib import admin
from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
	list_display = ('title', 'family', 'created_by', 'due_date', 'completed', 'completed_at')
	list_filter = ('family', 'completed')
	search_fields = ('title', 'description', 'created_by__username')
