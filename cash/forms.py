from django import forms
from .models import Fund, Expense, Category, Receipt


class FundForm(forms.ModelForm):
    class Meta:
        model = Fund
        fields = ['amount', 'note']


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['amount', 'category', 'note']

    def __init__(self, *args, **kwargs):
        family = kwargs.pop('family', None)
        super().__init__(*args, **kwargs)
        if family:
            self.fields['category'].queryset = Category.objects.filter(family=family)

class ReceiptForm(forms.ModelForm):
    class Meta:
        model = Receipt
        fields = ['image']

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
