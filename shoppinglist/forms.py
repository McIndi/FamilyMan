from django import forms
from .models import Item

class ItemForm(forms.ModelForm):
    """
    Form for creating and updating Item objects.
    """
    class Meta:
        model = Item
        fields = ['text', 'kind', 'obtained']  # Include the 'text', 'kind', and 'obtained' fields in the form.
