from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from .models import CustomUser


class ProfileForm(forms.ModelForm):
    """Form for editing user profile information."""
    
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'bio', 'profile_pic']
        widgets = {
            'bio': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control',
                'placeholder': 'Tell us about yourself...'
            }),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'profile_pic': forms.FileInput(attrs={'class': 'form-control'}),
        }


class CustomPasswordChangeForm(PasswordChangeForm):
    """Custom password change form with Bootstrap styling."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ['old_password', 'new_password1', 'new_password2']:
            self.fields[field_name].widget.attrs['class'] = 'form-control'
