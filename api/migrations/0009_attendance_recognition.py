# Generated by Django 4.0.4 on 2022-05-23 07:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0008_attendance_confirmed'),
    ]

    operations = [
        migrations.AddField(
            model_name='attendance',
            name='recognition',
            field=models.BooleanField(default=False, null=True),
        ),
    ]