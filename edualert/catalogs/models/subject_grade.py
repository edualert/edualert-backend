from django.db import models
from django_extensions.db.models import TimeStampedModel

from edualert.catalogs import constants
from edualert.catalogs.models import StudentCatalogPerSubject


class SubjectGrade(TimeStampedModel):
    catalog_per_subject = models.ForeignKey(StudentCatalogPerSubject, on_delete=models.CASCADE, related_name="grades", related_query_name="grade")
    student = models.ForeignKey("profiles.UserProfile", on_delete=models.CASCADE, related_name="grades", related_query_name="grades")

    subject_name = models.CharField(max_length=100)
    academic_year = models.PositiveSmallIntegerField()
    semester = models.PositiveSmallIntegerField()
    taken_at = models.DateField()

    grade = models.PositiveSmallIntegerField()
    GradeTypes = constants.GradeTypes
    grade_type = models.CharField(max_length=64, choices=GradeTypes.choices)

    objects = models.Manager()

    def __str__(self):
        return f"Grade {self.id}"

    class Meta:
        ordering = ['-taken_at', '-created']
