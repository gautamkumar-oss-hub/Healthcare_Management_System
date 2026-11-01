from datetime import date, time

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase

from appointments.models import Appointment
from users.models import Doctor, Patient
from .services import PATIENT_TOOLS, STAFF_TOOLS, _execute

User = get_user_model()


class ChatToolAuthorizationTests(TestCase):
    def setUp(self):
        self.patient_user = User.objects.create_user(username="patient-tools", user_type="patient")
        self.other_patient_user = User.objects.create_user(username="other-patient", user_type="patient")
        self.staff_user = User.objects.create_user(username="staff-tools", user_type="staff")
        self.other_staff_user = User.objects.create_user(username="other-staff", user_type="staff")
        self.patient = Patient.objects.create(user=self.patient_user)
        self.other_patient = Patient.objects.create(user=self.other_patient_user)
        self.provider = Doctor.objects.create(
            user=self.staff_user,
            specialization="Cardiology",
            license_number="CHAT-STAFF-1",
        )
        self.other_provider = Doctor.objects.create(
            user=self.other_staff_user,
            specialization="Neurology",
            license_number="CHAT-STAFF-2",
        )
        self.own_appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.provider,
            appointment_date=date(2099, 1, 1),
            appointment_time=time(10, 0),
            reason="Routine visit",
        )
        self.other_appointment = Appointment.objects.create(
            patient=self.other_patient,
            doctor=self.other_provider,
            appointment_date=date(2099, 1, 2),
            appointment_time=time(11, 0),
            reason="Private visit",
        )

    def test_role_tool_sets_have_exact_sizes(self):
        self.assertEqual(len(PATIENT_TOOLS), 5)
        self.assertEqual(len(STAFF_TOOLS), 8)

    def test_patient_appointment_list_is_scoped_to_patient(self):
        result = _execute("list_my_appointments", {}, self.patient_user)
        self.assertEqual([item["id"] for item in result], [self.own_appointment.pk])

    def test_patient_cannot_cancel_another_patients_appointment(self):
        result = _execute(
            "cancel_my_appointment",
            {"appointment_id": self.other_appointment.pk},
            self.patient_user,
        )
        self.assertIn("error", result)
        self.other_appointment.refresh_from_db()
        self.assertEqual(self.other_appointment.status, "pending")

    def test_staff_cannot_read_another_providers_appointment(self):
        result = _execute(
            "get_appointment_details",
            {"appointment_id": self.other_appointment.pk},
            self.staff_user,
        )
        self.assertIn("error", result)

    def test_guest_cannot_execute_account_tools(self):
        result = _execute("list_my_appointments", {}, AnonymousUser())
        self.assertIn("error", result)

    def test_boolean_is_not_accepted_as_appointment_id(self):
        result = _execute(
            "cancel_my_appointment",
            {"appointment_id": True},
            self.patient_user,
        )
        self.assertIn("error", result)
