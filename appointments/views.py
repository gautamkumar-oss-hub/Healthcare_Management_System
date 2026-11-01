from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Appointment
from .forms import AppointmentForm
from users.models import Patient

# ✅ NEW: Helper function to check appointment conflicts
def check_appointment_conflict(provider, appointment_date, appointment_time, exclude_id=None):
    """
    Check if the provider already has an appointment at this date/time.
    """
    conflicts = Appointment.objects.filter(
        doctor=provider,
        appointment_date=appointment_date,
        appointment_time=appointment_time,
        status__in=['pending', 'confirmed']  # Only check active appointments
    )
    
    # If updating an appointment, exclude it from conflict check
    if exclude_id:
        conflicts = conflicts.exclude(id=exclude_id)
    
    return conflicts.exists()

@login_required
def book_appointment(request):
    """Book a new appointment - ✅ NOW WITH VALIDATION"""
    if request.user.user_type != 'patient' or not hasattr(request.user, 'patient'):
        messages.error(request, 'Only patients can book appointments.')
        return redirect('users:dashboard')
    
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.patient = request.user.patient
            
            # ✅ NEW: Validate appointment date is not in the past
            if appointment.appointment_date < timezone.now().date():
                messages.error(request, 'Cannot book appointments in the past. Please select a future date.')
                return render(request, 'appointments/book.html', {'form': form})
            
            # ✅ NEW: Check if it's today and time has passed
            if appointment.appointment_date == timezone.now().date():
                current_time = timezone.now().time()
                if appointment.appointment_time < current_time:
                    messages.error(request, 'Cannot book appointments in the past. Please select a future time.')
                    return render(request, 'appointments/book.html', {'form': form})
            
            # ✅ NEW: Check for appointment conflicts
            if check_appointment_conflict(appointment.doctor, appointment.appointment_date, appointment.appointment_time):
                messages.error(
                    request, 
                    'This time slot is already booked. Please choose another time or provider.'
                )
                return render(request, 'appointments/book.html', {'form': form})
            
            # All validations passed - save the appointment
            appointment.save()
            messages.success(request, 'Appointment booked successfully!')
            return redirect('appointments:success', appointment_id=appointment.id)
    else:
        form = AppointmentForm()
    
    return render(request, 'appointments/book.html', {'form': form})

@login_required
def my_appointments(request):
    """View user's appointments"""
    if request.user.user_type == 'patient' and hasattr(request.user, 'patient'):
        # ✅ IMPROVED: Use select_related to avoid N+1 queries
        appointments = Appointment.objects.filter(
            patient=request.user.patient
        ).select_related('doctor__user')
    elif request.user.user_type == 'staff' and hasattr(request.user, 'doctor'):
        # ✅ IMPROVED: Use select_related to avoid N+1 queries
        appointments = Appointment.objects.filter(
            doctor=request.user.doctor
        ).select_related('patient__user')
    else:
        appointments = []
    
    return render(request, 'appointments/list.html', {'appointments': appointments})

@login_required
def appointment_success(request, appointment_id):
    """Appointment booking success page"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # A patient may view their own appointment; staff may view only their assigned one.
    owns_appointment = (
        request.user.user_type == 'patient'
        and hasattr(request.user, 'patient')
        and appointment.patient_id == request.user.patient.id
    ) or (
        request.user.user_type == 'staff'
        and hasattr(request.user, 'doctor')
        and appointment.doctor_id == request.user.doctor.id
    )
    if not owns_appointment:
        messages.error(request, 'You can only view appointments assigned to your account.')
        return redirect('appointments:my_appointments')
    
    return render(request, 'appointments/success.html', {'appointment': appointment})

@login_required
def update_appointment(request, appointment_id):
    """Staff can update appointment status with validation."""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Only staff accounts with provider profiles can update appointments.
    if request.user.user_type != 'staff' or not hasattr(request.user, 'doctor'):
        messages.error(request, 'Only staff can update appointments.')
        return redirect('appointments:my_appointments')
    
    # Only the assigned staff provider can update.
    if appointment.doctor != request.user.doctor:
        messages.error(request, 'You can only update your own appointments.')
        return redirect('appointments:my_appointments')
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        notes = request.POST.get('notes', '')
        
        # ✅ NEW: Validate status transitions
        valid_statuses = ['pending', 'confirmed', 'completed', 'cancelled']
        
        if new_status not in valid_statuses:
            messages.error(request, 'Invalid status selected.')
            return render(request, 'appointments/update.html', {'appointment': appointment})
        
        # ✅ NEW: Business logic validation
        # Can't confirm a cancelled appointment
        if appointment.status == 'cancelled' and new_status == 'confirmed':
            messages.error(request, 'Cannot confirm a cancelled appointment. Please create a new one.')
            return render(request, 'appointments/update.html', {'appointment': appointment})
        
        # Can't cancel a completed appointment
        if appointment.status == 'completed' and new_status == 'cancelled':
            messages.error(request, 'Cannot cancel a completed appointment.')
            return render(request, 'appointments/update.html', {'appointment': appointment})
        
        # Update the appointment
        appointment.status = new_status
        appointment.notes = notes
        appointment.save()
        
        messages.success(request, f'Appointment status updated to {appointment.get_status_display()}!')
        return redirect('appointments:my_appointments')
    
    return render(request, 'appointments/update.html', {'appointment': appointment})
