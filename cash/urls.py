from django.urls import path
from . import views

urlpatterns = [
    path('add_fund/', views.add_fund, name='add_fund'),
    path('add_expense/', views.add_expense, name='add_expense'),
    path('upload_receipt/<int:expense_id>/', views.upload_receipt, name='upload_receipt'),
    path('transactions/', views.cash_transaction_list, name='cash_transaction_list'),
    path('expense/<int:expense_id>/edit/', views.edit_expense, name='edit_expense'),
    path('expense/<int:expense_id>/delete/', views.delete_expense, name='delete_expense'),
    path('fund/<int:fund_id>/edit/', views.edit_fund, name='edit_fund'),
    path('fund/<int:fund_id>/delete/', views.delete_fund, name='delete_fund'),
]