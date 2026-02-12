from django import forms
from .models import Item

class ItemForm(forms.ModelForm):
    """
    Form for creating and updating Item objects.
    """
    class Meta:
        model = Item
        exclude = ['family']  # Exclude the 'family' field from the form.
