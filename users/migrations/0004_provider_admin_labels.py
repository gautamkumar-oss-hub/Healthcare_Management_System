from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("users", "0003_remove_insurance_prediction_data")]

    operations = [
        migrations.AlterModelOptions(
            name="doctor",
            options={"verbose_name": "provider", "verbose_name_plural": "providers"},
        ),
    ]
