from django.db import models


class Students(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    year = models.IntegerField()
    field_of_study = models.CharField(max_length=50)
