from django.contrib import admin
from .models import CustomUser, Membership, Family

# Registering the CustomUser model with the Django admin site
@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'profile_pic')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_active')
    ordering = ('username',)
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('Personal info', {
            'fields': ('first_name', 'last_name', 'email')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important dates', {
            'fields': ('last_login',)
        }),
        ('Profile', {
            'fields': ('bio', 'profile_pic')
        }),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser', 'bio', 'profile_pic')
        }),
    )
    filter_horizontal = ('groups', 'user_permissions')
    add_filter_horizontal = ('groups', 'user_permissions')
    readonly_fields = ('last_login',)

@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'family', 'role')
    search_fields = ('user__username', 'family__name', 'role')
    list_filter = ('role',)
    ordering = ('family', 'user')

@admin.register(Family)
class FamilyAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)
