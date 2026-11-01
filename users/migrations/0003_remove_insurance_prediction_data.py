from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("users", "0002_staff_role")]

    operations = [
        migrations.RunSQL(
            sql="DROP TABLE IF EXISTS insurance_insuranceprediction",
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
