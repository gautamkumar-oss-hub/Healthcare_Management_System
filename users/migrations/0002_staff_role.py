from django.db import migrations, models


def migrate_doctors_to_staff(apps, schema_editor):
    User = apps.get_model("users", "User")
    User.objects.filter(user_type="doctor").update(user_type="staff")


def migrate_staff_to_doctors(apps, schema_editor):
    User = apps.get_model("users", "User")
    Doctor = apps.get_model("users", "Doctor")
    provider_user_ids = Doctor.objects.values_list("user_id", flat=True)
    User.objects.filter(user_type="staff", id__in=provider_user_ids).update(user_type="doctor")


class Migration(migrations.Migration):
    dependencies = [("users", "0001_initial")]

    operations = [
        migrations.RunPython(migrate_doctors_to_staff, migrate_staff_to_doctors),
        migrations.AlterField(
            model_name="user",
            name="user_type",
            field=models.CharField(
                choices=[("patient", "Patient"), ("staff", "Staff")],
                default="patient",
                max_length=10,
            ),
        ),
    ]
