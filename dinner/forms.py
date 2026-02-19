from django import forms

class AddDinnerOptionForm(forms.Form):
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'placeholder': 'Dinner option (e.g., Tacos)'}),
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                'rows': 3,
                'placeholder': 'Optional notes (pros/cons, cost, prep time, etc.)',
            }
        ),
    )


class RecordDinnerForm(forms.Form):
    dinner_eaten = forms.CharField(
        required=False,
        max_length=255,
        label='What we ate',
        widget=forms.TextInput(attrs={'placeholder': 'Optional: record what was eaten'}),
    )
