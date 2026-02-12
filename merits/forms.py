from django import forms
from django.contrib.auth import get_user_model

from merits.models import Merit, Demerit

class MeritForm(forms.ModelForm):
    """
    Form for creating and updating Merit instances.
    """
    class Meta:
        model = Merit
        fields = ['child', 'description', 'weight']  # Include the fields you want to display in the form
        widgets = {
            'child': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
class DemeritForm(forms.ModelForm):
    """
    Form for creating and updating Demerit instances.
    """
    class Meta:
        model = Demerit
        fields = ['child', 'description', 'weight']  # Include the fields you want to display in the form
        widgets = {
            'child': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
