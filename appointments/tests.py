from django.test import TestCase, Client
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import date, time, timedelta
from .models import Appointment
from users.models import Patient, Doctor

User = get_user_model()

class AppointmentValidationTests(TestCase):
    """Test appointment validation and conflict detection"""
    
    def setUp(self):
        """Create test users for each test"""
        # Create patient
        self.patient_user = User.objects.create_user(
            username='testpatient',
            password='testpass123',
            email='patient@test.com',
            user_type='patient',
            first_name='Test',
            last_name='Patient'
        )
        self.patient = Patient.objects.create(
            user=self.patient_user,
            date_of_birth=date(1990, 1, 1)
        )
        
        # Create a staff-linked provider record for appointment selection.
        self.doctor_user = User.objects.create_user(
            username='testprovider',
            password='testpass123',
            email='provider@test.com',
            user_type='staff',
            first_name='Dr.',
            last_name='Smith'
        )
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            specialization='General Medicine',
            license_number='DOC12345',
            experience_years=5,
            consultation_fee=100.00
        )
        
        # Create client for making requests
        self.client = Client()
    
    def test_appointment_creation(self):
        """Test creating a basic appointment"""
        tomorrow = timezone.now().date() + timedelta(days=1)
        appointment_time = time(10, 0)
        
        appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            appointment_date=tomorrow,
            appointment_time=appointment_time,
            reason='Regular checkup'
        )
        
        self.assertEqual(appointment.status, 'pending')
        self.assertEqual(appointment.patient, self.patient)
        self.assertEqual(appointment.doctor, self.doctor)
        print("✅ Test 1 passed: Appointment created successfully")
    
    def test_appointment_conflict_detection(self):
        """Test that duplicate appointments are prevented"""
        tomorrow = timezone.now().date() + timedelta(days=1)
        appointment_time = time(10, 0)
        
        # Create first appointment
        Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            appointment_date=tomorrow,
            appointment_time=appointment_time,
            reason='First appointment',
            status='confirmed'
        )
        
        # Login as patient
        self.client.login(username='testpatient', password='testpass123')
        
        # Try to book same time slot
        response = self.client.post('/appointments/book/', {
            'doctor': self.doctor.id,
            'appointment_date': tomorrow,
            'appointment_time': appointment_time,
            'reason': 'Second appointment (should fail)'
        })
        
        # Should have only 1 appointment (conflict prevented)
        appointment_count = Appointment.objects.filter(
            doctor=self.doctor,
            appointment_date=tomorrow,
            appointment_time=appointment_time
        ).count()
        
        self.assertEqual(appointment_count, 1)
        print("✅ Test 2 passed: Appointment conflict detected")
    
    def test_cannot_book_past_date(self):
        """Test that past dates are rejected"""
        self.client.login(username='testpatient', password='testpass123')
        
        yesterday = timezone.now().date() - timedelta(days=1)
        
        response = self.client.post('/appointments/book/', {
            'doctor': self.doctor.id,
            'appointment_date': yesterday,
            'appointment_time': time(10, 0),
            'reason': 'Past appointment (should fail)'
        })
        
        # Should not create appointment in the past
        past_appointments = Appointment.objects.filter(
            appointment_date__lt=timezone.now().date()
        ).count()
        
        self.assertEqual(past_appointments, 0)
        print("✅ Test 3 passed: Past date rejected")
    
    def test_patient_can_view_own_appointments(self):
        """Test that patients can see their appointments"""
        tomorrow = timezone.now().date() + timedelta(days=1)
        
        Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            appointment_date=tomorrow,
            appointment_time=time(10, 0),
            reason='Test appointment'
        )
        
        self.client.login(username='testpatient', password='testpass123')
        response = self.client.get('/appointments/my/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dr. Smith')
        print("✅ Test 4 passed: Patient can view appointments")
    
    def test_staff_can_update_appointment_status(self):
        """Test that staff can update appointment status"""
        tomorrow = timezone.now().date() + timedelta(days=1)
        
        appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            appointment_date=tomorrow,
            appointment_time=time(10, 0),
            reason='Test appointment',
            status='pending'
        )
        
        self.client.login(username='testprovider', password='testpass123')
        
        response = self.client.post(f'/appointments/update/{appointment.id}/', {
            'status': 'confirmed',
            'notes': 'Appointment confirmed by staff'
        })
        
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, 'confirmed')
        self.assertEqual(appointment.notes, 'Appointment confirmed by staff')
        print("✅ Test 5 passed: Staff can update status")


class UserRegistrationTests(TestCase):
    """Test user registration"""
    
    def test_patient_registration(self):
        """Test patient can register"""
        response = self.client.post('/users/register/patient/', {
            'username': 'newpatient',
            'email': 'newpatient@test.com',
            'first_name': 'New',
            'last_name': 'Patient',
            'phone': '1234567890',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
        })
        
        # Check user was created
        user_exists = User.objects.filter(username='newpatient').exists()
        self.assertTrue(user_exists)
        
        # Check patient profile was created
        if user_exists:
            user = User.objects.get(username='newpatient')
            self.assertEqual(user.user_type, 'patient')
            self.assertTrue(hasattr(user, 'patient'))
            print("✅ Test 6 passed: Patient registration works")
    
    def test_staff_registration(self):
        """Staff registration creates an account request, not a provider record."""
        response = self.client.post('/users/register/staff/', {
            'username': 'newstaff',
            'email': 'newstaff@test.com',
            'first_name': 'New',
            'last_name': 'Staff',
            'phone': '1234567890',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
        })
        
        # Check user was created
        user_exists = User.objects.filter(username='newstaff').exists()
        self.assertTrue(user_exists)
        
        # Staff must be approved and do not receive provider profiles.
        if user_exists:
            user = User.objects.get(username='newstaff')
            self.assertEqual(user.user_type, 'staff')
            self.assertFalse(user.is_active)
            self.assertFalse(hasattr(user, 'doctor'))
            print("✅ Test 7 passed: Staff registration works")

    def test_staff_registration_is_pending_approval_without_provider_profile(self):
        response = self.client.post('/users/register/staff/', {
            'username': 'generalstaff',
            'email': 'generalstaff@test.com',
            'first_name': 'General',
            'last_name': 'Staff',
            'phone': '1234567890',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
        })

        self.assertRedirects(response, '/users/login/')
        user = User.objects.get(username='generalstaff')
        self.assertEqual(user.user_type, 'staff')
        self.assertFalse(user.is_active)
        self.assertFalse(hasattr(user, 'doctor'))
        self.assertNotIn('_auth_user_id', self.client.session)


class SecurityTests(TestCase):
    """Test security features"""
    
    def test_login_required_for_booking(self):
        """Test that booking requires login"""
        response = self.client.get('/appointments/book/')
        
        # Should redirect to login page
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
        print("✅ Test 8 passed: Login required for booking")
    
    def test_csrf_token_present(self):
        """Test that CSRF token is present in forms"""
        # Create and login user
        user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            user_type='patient'
        )
        Patient.objects.create(user=user)
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/appointments/book/')
        
        self.assertContains(response, 'csrfmiddlewaretoken')
        print("✅ Test 9 passed: CSRF token present")


class ModelTests(TestCase):
    """Test model methods and properties"""
    
    def test_appointment_string_representation(self):
        """Test appointment __str__ method"""
        user1 = User.objects.create_user(username='patient1', user_type='patient')
        user2 = User.objects.create_user(username='staff1', user_type='staff')
        
        patient = Patient.objects.create(user=user1)
        doctor = Doctor.objects.create(
            user=user2,
            specialization='Test',
            license_number='TEST123'
        )
        
        appointment = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            appointment_date=date(2025, 12, 25),
            appointment_time=time(10, 0),
            reason='Test'
        )
        
        str_repr = str(appointment)
        self.assertIn('2025-12-25', str_repr)
        self.assertIn('10:00', str_repr)
        print("✅ Test 10 passed: Model string representation works")
