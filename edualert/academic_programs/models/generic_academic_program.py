from django.db import models
from django.contrib.postgres.fields import JSONField
from django.db.models.functions import Lower

from edualert.subjects.models import ProgramSubjectThrough


class GenericAcademicProgram(models.Model):
    name = models.CharField(max_length=128)
    category = models.ForeignKey("schools.SchoolUnitCategory", null=True, blank=True, on_delete=models.SET_NULL,
                                 related_name="generic_academic_programs", related_query_name="generic_academic_program")
    academic_profile = models.ForeignKey("schools.SchoolUnitProfile", null=True, blank=True, on_delete=models.SET_NULL,
                                         related_name="generic_academic_programs", related_query_name="generic_academic_program")
    mandatory_subjects = models.ManyToManyField("subjects.Subject", through=ProgramSubjectThrough,
                                                related_name="generic_academic_programs", related_query_name="generic_academic_program")

    optional_subjects_weekly_hours = JSONField(default=dict)

    objects = models.Manager()

    class Meta:
        ordering = (Lower('name'),)

    def __str__(self):
        return f"GenericAcademicProgram {self.id} {self.name}"
