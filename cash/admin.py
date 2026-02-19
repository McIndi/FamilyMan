from django.contrib import admin

from .models import Category, Fund, Expense, Receipt, WalletTransaction

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'family')
    list_filter = ('family',)
    search_fields = ('name', 'description')

@admin.register(Fund)
class FundAdmin(admin.ModelAdmin):
    list_display = ('user', 'family', 'amount', 'date', 'note')
    list_filter = ('family', 'date')
    search_fields = ('note',)

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('user', 'family', 'category', 'amount', 'date', 'note')
    list_filter = ('family', 'category', 'date')
    search_fields = ('note',)

@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ('expense', 'family', 'uploaded_at')
    list_filter = ('family', 'uploaded_at')
    search_fields = ('expense__note',)

@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'family', 'direction', 'amount', 'date', 'note')
    list_filter = ('family', 'direction', 'date')
    search_fields = ('note', 'user__username')
