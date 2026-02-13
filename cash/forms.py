from django import forms
from django.core.exceptions import ValidationError
from .models import Fund, Expense, Category, Receipt


class FundForm(forms.ModelForm):
    class Meta:
        model = Fund
        fields = ['amount', 'note']

    def clean_amount(self):
        """Reject negative amount values."""
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount < 0:
            raise ValidationError('Amount cannot be negative.')
        return amount


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['amount', 'category', 'note']

    def clean_amount(self):
        """Reject negative amount values."""
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount < 0:
            raise ValidationError('Amount cannot be negative.')
        return amount

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
