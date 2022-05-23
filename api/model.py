from django.db import models
from django.utils.timezone import now


class Students(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.CharField(max_length=50, null=True)
    year = models.IntegerField()
    verified = models.BooleanField(null=True, default=False)
    field_of_study = models.CharField(max_length=50)


class Attendance(models.Model):
    student = models.ForeignKey(Students, on_delete=models.CASCADE)
    subject = models.CharField(max_length=50, null=False)
    token = models.CharField(max_length=60, null=False)
    confirmed = models.BooleanField(null=True, default=False)
    recognition = models.BooleanField(null=True, default=False)
    attendance_date = models.DateTimeField(default=now)
