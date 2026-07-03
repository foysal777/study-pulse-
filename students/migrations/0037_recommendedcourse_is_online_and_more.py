# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0036_courseenrollment_is_confirm'),
    ]

    operations = [
        migrations.AddField(
            model_name='recommendedcourse',
            name='is_online',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='recommendedcourse',
            name='offline_location',
            field=models.TextField(blank=True, null=True),
        ),
    ]
