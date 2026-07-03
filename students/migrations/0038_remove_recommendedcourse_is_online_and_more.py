# Generated manually

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0037_recommendedcourse_is_online_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='recommendedcourse',
            name='is_online',
        ),
        migrations.RemoveField(
            model_name='recommendedcourse',
            name='offline_location',
        ),
    ]
