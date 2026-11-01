from django import forms
from .models import Appointment
from users.models import Doctor

class AppointmentForm(forms.ModelForm):
    """Appointment booking form"""
    
    class Meta:
        model = Appointment
        fields = ['doctor', 'appointment_date', 'appointment_time', 'reason']
        widgets = {
            'appointment_date': forms.DateInput(attrs={'type': 'date'}),
            'appointment_time': forms.TimeInput(attrs={'type': 'time'}),
            'reason': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Please describe your symptoms or reason for visit...'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['doctor'].queryset = Doctor.objects.filter(
            user__user_type='staff', user__is_active=True
        )
        self.fields['doctor'].label = "Provider"
        self.fields['doctor'].empty_label = "Select a provider"
