from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from appointments.models import Appointment
from chatbot.models import Conversation
from django.utils import timezone
from .forms import PatientRegistrationForm, StaffRegistrationForm
from .models import Patient

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
        patient_appointments = Appointment.objects.filter(patient=request.user.patient)
        context['appointment_total'] = patient_appointments.count()
        context['appointment_upcoming'] = patient_appointments.filter(
            appointment_date__gte=timezone.localdate(), status__in=['pending', 'confirmed']
        ).count()
        context['conversation_total'] = Conversation.objects.filter(user=request.user).count()
    elif request.user.user_type == 'staff':
        context['profile_type'] = 'staff'
        context['hospital_appointment_total'] = Appointment.objects.count()
        context['hospital_appointment_pending'] = Appointment.objects.filter(status='pending').count()
        context['hospital_patient_total'] = Patient.objects.count()
    
    return render(request, 'users/dashboard.html', context)
