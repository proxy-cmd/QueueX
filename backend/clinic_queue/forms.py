import re

from django import forms

from .models import QueueSettings


class PatientForm(forms.Form):
    name = forms.CharField(max_length=120)
    phone = forms.CharField(max_length=20)

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if len(name) < 2:
            raise forms.ValidationError('Enter the patient name.')
        return name

    def clean_phone(self):
        phone = self.cleaned_data['phone'].strip()
        if not re.fullmatch(r'[0-9+\-\s]{7,20}', phone):
            raise forms.ValidationError('Enter a valid phone number.')
        return phone


class QueueSettingsForm(forms.ModelForm):
    class Meta:
        model = QueueSettings
        fields = ['clinic_name', 'average_consultation_minutes']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['average_consultation_minutes'].min_value = 1
        self.fields['average_consultation_minutes'].widget.attrs['min'] = 1
