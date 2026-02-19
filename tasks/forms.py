from django import forms
from django.contrib.auth import get_user_model

from .models import Task


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'due_date']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }


class CompleteTaskForm(forms.Form):
    completers = forms.ModelMultipleChoiceField(
        queryset=get_user_model().objects.none(),
        required=True,
        label='Completed by',
        widget=forms.SelectMultiple(),
        help_text='Select one or more family members who helped complete this task.',
    )

    def __init__(self, *args, family=None, **kwargs):
        super().__init__(*args, **kwargs)
        if family:
            self.fields['completers'].queryset = family.members.all()
