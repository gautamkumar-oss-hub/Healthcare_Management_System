from django.contrib import admin
from .models import Appointment

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'provider_name', 'appointment_date', 'appointment_time', 'status', 'created_at')
    list_filter = ('status', 'appointment_date', 'doctor__specialization')
    search_fields = ('patient__user__username', 'doctor__user__username', 'reason')
    date_hierarchy = 'appointment_date'
    
    fieldsets = (
        ('Appointment Details', {
            'fields': ('patient', 'doctor', 'appointment_date', 'appointment_time', 'reason')
        }),
        ('Status & Notes', {
            'fields': ('status', 'notes')
        }),
    )

    @admin.display(description='Provider')
    def provider_name(self, obj):
        return obj.doctor
