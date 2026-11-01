from django.db import models
from users.models import User, Patient, Doctor

class Appointment(models.Model):
    """Appointment model"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, verbose_name="provider")
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-appointment_date', '-appointment_time']
    
    def __str__(self):
        return f"{self.patient} with {self.doctor} on {self.appointment_date} at {self.appointment_time}"

    def can_transition_to(self, new_status):
        """Apply the same staff status rules from the UI and assistant tools."""
        if new_status not in {'confirmed', 'completed', 'cancelled'}:
            return False
        if self.status == 'cancelled' and new_status == 'confirmed':
            return False
        if self.status == 'completed' and new_status == 'cancelled':
            return False
        return True
