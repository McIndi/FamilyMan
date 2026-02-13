from django.contrib import admin

from .models import Category, Fund, Expense, Receipt

admin.site.register(Category)
admin.site.register(Fund)
admin.site.register(Expense)
admin.site.register(Receipt)

