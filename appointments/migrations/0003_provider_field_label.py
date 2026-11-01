import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("appointments", "0002_initial"),
        ("users", "0004_provider_admin_labels"),
    ]

    operations = [
        migrations.AlterField(
            model_name="appointment",
            name="doctor",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="users.doctor",
                verbose_name="provider",
            ),
        ),
    ]
