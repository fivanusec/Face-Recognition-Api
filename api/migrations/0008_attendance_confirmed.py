# Generated by Django 4.0.4 on 2022-05-21 11:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0007_students_email'),
    ]

    operations = [
        migrations.AddField(
            model_name='attendance',
            name='confirmed',
            field=models.BooleanField(default=False, null=True),
        ),
    ]
