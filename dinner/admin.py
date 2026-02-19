from django.contrib import admin

from .models import DinnerDay, DinnerOption, DinnerVote


@admin.register(DinnerDay)
class DinnerDayAdmin(admin.ModelAdmin):
	list_display = ('family', 'date', 'dinner_eaten', 'decided_by', 'decided_at')
	list_filter = ('family', 'date')
	search_fields = ('family__name', 'dinner_eaten')


@admin.register(DinnerOption)
class DinnerOptionAdmin(admin.ModelAdmin):
	list_display = ('name', 'dinner_day', 'created_by', 'created_at')
	list_filter = ('dinner_day__family', 'dinner_day__date')
	search_fields = ('name', 'dinner_day__family__name', 'created_by__username')


@admin.register(DinnerVote)
class DinnerVoteAdmin(admin.ModelAdmin):
	list_display = ('dinner_day', 'option', 'voter', 'created_at')
	list_filter = ('dinner_day__family', 'dinner_day__date')
	search_fields = ('voter__username', 'option__name', 'dinner_day__family__name')
