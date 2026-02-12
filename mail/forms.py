from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from .models import Message

class MessageForm(forms.ModelForm):
    recipients = forms.ModelMultipleChoiceField(
        queryset=get_user_model().objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        required=True,
        label="Recipients"
    )

    class Meta:
        model = Message
        exclude = ['family']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Subject'}),
            'body': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Write your message here...'}),
        }