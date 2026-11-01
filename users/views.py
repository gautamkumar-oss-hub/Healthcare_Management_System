from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import PatientRegistrationForm, StaffRegistrationForm

def register_patient(request):
    """Patient registration view"""
    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful! Welcome to Healthcare Management System.')
            return redirect('users:dashboard')
    else:
        form = PatientRegistrationForm()
    
    return render(request, 'users/register.html', {
        'form': form,
        'user_type': 'Patient'
    })

def register_staff(request):
    """Staff registration view."""
    if request.method == 'POST':
        form = StaffRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request,
                'Your staff access request has been submitted. A hospital administrator must approve your account before you can sign in.'
            )
            return redirect('users:login')
    else:
        form = StaffRegistrationForm()
    
    return render(request, 'users/register.html', {
        'form': form,
        'user_type': 'Staff'
    })

@login_required
def dashboard(request):
    """User dashboard"""
    context = {
        'user': request.user,
    }
    
    if request.user.user_type == 'patient' and hasattr(request.user, 'patient'):
        context['profile'] = request.user.patient
        context['profile_type'] = 'patient'
    elif request.user.user_type == 'staff':
        context['profile_type'] = 'staff'
        if hasattr(request.user, 'doctor'):
            context['profile'] = request.user.doctor
            context['has_appointment_profile'] = True
        else:
            context['has_appointment_profile'] = False
    
    return render(request, 'users/dashboard.html', context)
