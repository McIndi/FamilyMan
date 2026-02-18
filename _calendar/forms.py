from django import forms
from .models import Event
from django.forms.widgets import DateTimeInput, Select

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        exclude = ['family', 'host']
        widgets = {
            'when': DateTimeInput(attrs={'type': 'datetime-local'}),
            'duration': Select(choices=[
                ('00:15:00', '15 minutes'),
                ('00:30:00', '30 minutes'),
                ('01:00:00', '1 hour'),
                ('02:00:00', '2 hours'),
                ('03:00:00', '3 hours'),
            ]),
        }

    def __init__(self, *args, family=None, **kwargs):
        super().__init__(*args, **kwargs)
        if 'attendees' in self.fields:
            if family:
                self.fields['attendees'].queryset = family.members.all()
            else:
                self.fields['attendees'].queryset = self.fields['attendees'].queryset.none()