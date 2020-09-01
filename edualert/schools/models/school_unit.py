from django.db import models
from django_extensions.db.models import TimeStampedModel

from edualert.schools.models import SchoolUnitCategory, SchoolUnitProfile


class SchoolUnit(models.Model):
    name = models.CharField(max_length=64)
    district = models.CharField(max_length=20, db_index=True)
    city = models.CharField(max_length=64, db_index=True)

    objects = models.Manager()

    def __str__(self):
        return f"SchoolUnit {self.id} {self.name}"


class RegisteredSchoolUnit(TimeStampedModel):
    name = models.CharField(max_length=64)
    categories = models.ManyToManyField(SchoolUnitCategory, blank=False,
                                        related_name="registered_school_units", related_query_name="registered_school_unit")
    academic_profile = models.ForeignKey(SchoolUnitProfile, null=True, blank=True, on_delete=models.SET_NULL,
                                         related_name="registered_school_units", related_query_name="registered_school_unit")
    is_active = models.BooleanField(default=True)
    district = models.CharField(max_length=20, db_index=True)
    city = models.CharField(max_length=64, db_index=True)
    address = models.CharField(max_length=100)
    email = models.EmailField(max_length=150)
    phone_number = models.CharField(max_length=20)
    school_principal = models.OneToOneField("profiles.UserProfile", related_name="registered_school_unit", on_delete=models.PROTECT)
    students_at_risk_count = models.PositiveSmallIntegerField(default=0)
    last_change_in_catalog = models.DateTimeField(null=True, blank=True)

    objects = models.Manager()

    def __str__(self):
        return f"RegisteredSchoolUnit {self.id} {self.name}"
