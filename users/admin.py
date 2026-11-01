from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Patient, Doctor

# Customize User admin
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'is_staff')
    list_filter = ('user_type', 'is_staff', 'is_superuser', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('user_type', 'phone')}),
    )

# Register the User model
admin.site.register(User, CustomUserAdmin)

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('user', 'date_of_birth', 'phone_number')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    
    def phone_number(self, obj):
        return obj.user.phone
    phone_number.short_description = 'Phone'

@admin.register(Doctor)
class ProviderAdmin(admin.ModelAdmin):
    list_display = ('provider_name', 'specialization', 'license_number', 'experience_years', 'consultation_fee')
    list_filter = ('specialization',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'specialization')

    @admin.display(description='Provider')
    def provider_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
