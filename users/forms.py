from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Patient

class PatientRegistrationForm(UserCreationForm):
    """Patient registration form"""
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': ' '}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': ' '}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': ' '}))
    phone = forms.CharField(max_length=15, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': ' '}))
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), required=False)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': ' '}), required=False)
    emergency_contact = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': ' '}))

    # Add these two fields for password styling
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': ' '}))
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': ' '}))

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'phone')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': ' '}),
        }
    
    def save(self, commit=True):
        # ... (rest of the save method is unchanged)
        user = super().save(commit=False)
        user.user_type = 'patient'
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        user.phone = self.cleaned_data['phone']
        
        if commit:
            user.save()
            Patient.objects.create(
                user=user,
                date_of_birth=self.cleaned_data.get('date_of_birth'),
                address=self.cleaned_data.get('address', ''),
                emergency_contact=self.cleaned_data.get('emergency_contact', '')
            )
        return user

class StaffRegistrationForm(UserCreationForm):
    """Register a hospital staff account."""
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': ' '}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': ' '}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': ' '}))
    phone = forms.CharField(max_length=15, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': ' '}))
    # Also add these two fields for password styling
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': ' '}))
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': ' '}))

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'phone')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': ' '}),
        }

    def save(self, commit=True):
        # ... (rest of the save method is unchanged)
        user = super().save(commit=False)
        user.user_type = 'staff'
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        user.phone = self.cleaned_data['phone']
        # Staff access must be explicitly approved by a hospital administrator.
        user.is_active = False
        
        if commit:
            user.save()
        return user
