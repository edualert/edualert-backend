from django.db import models
from django.db.models.functions import Lower


class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True)
    allows_exemption = models.BooleanField(default=False)
    is_coordination = models.BooleanField(default=False)
    should_be_in_taught_subjects = models.BooleanField(default=True)

    objects = models.Manager()

    class Meta:
        ordering = (Lower('name'),)

    def __str__(self):
        return f'{self.id} {self.name}'
