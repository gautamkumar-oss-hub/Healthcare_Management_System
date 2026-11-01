from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import Appointment
from .forms import AppointmentForm
from users.models import Doctor, Patient

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
            if appointment.appointment_date < timezone.localdate():
                messages.error(request, 'Cannot book appointments in the past. Please select a future date.')
                return render(request, 'appointments/book.html', {'form': form})
            
            # ✅ NEW: Check if it's today and time has passed
            if appointment.appointment_date == timezone.localdate():
                current_time = timezone.localtime().time().replace(tzinfo=None)
                if appointment.appointment_time <= current_time:
                    messages.error(request, 'Cannot book appointments in the past. Please select a future time.')
                    return render(request, 'appointments/book.html', {'form': form})
            
            # ✅ NEW: Check for appointment conflicts
            try:
                with transaction.atomic():
                    provider = Doctor.objects.select_for_update().get(
                        pk=appointment.doctor_id, user__user_type='staff', user__is_active=True
                    )
                    if check_appointment_conflict(
                        provider, appointment.appointment_date, appointment.appointment_time
                    ):
                        messages.error(
                            request,
                            'This time slot is already booked. Please choose another time or provider.'
                        )
                        return render(request, 'appointments/book.html', {'form': form})
                    appointment.doctor = provider
                    appointment.save()
            except Doctor.DoesNotExist:
                form.add_error('doctor', 'That provider is no longer available.')
                return render(request, 'appointments/book.html', {'form': form})
            
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
    elif request.user.user_type == 'staff':
        # ✅ IMPROVED: Use select_related to avoid N+1 queries
        appointments = Appointment.objects.select_related('doctor__user', 'patient__user')
    else:
        appointments = Appointment.objects.none()

    counts = appointments.aggregate(
        total=Count('id'),
        pending=Count('id', filter=Q(status='pending')),
        confirmed=Count('id', filter=Q(status='confirmed')),
        completed=Count('id', filter=Q(status='completed')),
        cancelled=Count('id', filter=Q(status='cancelled')),
    )
    return render(request, 'appointments/list.html', {
        'appointments': appointments,
        'appointment_counts': counts,
    })


@login_required
@require_POST
def cancel_appointment(request, appointment_id):
    """Let a patient cancel only their own pending appointment."""
    if request.user.user_type != 'patient' or not hasattr(request.user, 'patient'):
        messages.error(request, 'Only patients can cancel their appointments.')
        return redirect('appointments:my_appointments')

    appointment = get_object_or_404(
        Appointment,
        pk=appointment_id,
        patient=request.user.patient,
        status='pending',
    )
    appointment.status = 'cancelled'
    appointment.save(update_fields=['status', 'updated_at'])
    messages.success(request, 'Your appointment has been cancelled.')
    return redirect('appointments:my_appointments')

@login_required
def appointment_success(request, appointment_id):
    """Show appointment details to its patient or authenticated hospital staff."""
    appointment = get_object_or_404(
        Appointment.objects.select_related('patient__user', 'doctor__user'),
        id=appointment_id,
    )
    
    # Patients can view their own appointment; hospital staff can view hospital appointments.
    owns_appointment = (
        request.user.user_type == 'patient'
        and hasattr(request.user, 'patient')
        and appointment.patient_id == request.user.patient.id
    ) or request.user.user_type == 'staff'
    if not owns_appointment:
        messages.error(request, 'You can only view appointments associated with your account.')
        return redirect('appointments:my_appointments')
    
    return render(request, 'appointments/success.html', {'appointment': appointment})

@login_required
def update_appointment(request, appointment_id):
    """Staff can update appointment status with validation."""
    # Only hospital staff can update appointments.
    if request.user.user_type != 'staff':
        messages.error(request, 'Only staff can update appointments.')
        return redirect('appointments:my_appointments')

    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        notes = request.POST.get('notes', '')
        
        if not appointment.can_transition_to(new_status):
            messages.error(request, 'That appointment status change is not allowed.')
            return render(request, 'appointments/update.html', {'appointment': appointment})

        if not isinstance(notes, str) or len(notes) > 5000:
            messages.error(request, 'Staff notes must be 5,000 characters or fewer.')
            return render(request, 'appointments/update.html', {'appointment': appointment})
        
        # Update the appointment
        appointment.status = new_status
        appointment.notes = notes.strip()
        appointment.save()
        
        messages.success(request, f'Appointment status updated to {appointment.get_status_display()}!')
        return redirect('appointments:my_appointments')
    
    return render(request, 'appointments/update.html', {'appointment': appointment})
