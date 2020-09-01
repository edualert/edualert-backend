from django.db import models
from django_extensions.db.models import TimeStampedModel

from edualert.catalogs.models import StudentCatalogPerSubject


class SubjectAbsence(TimeStampedModel):
    catalog_per_subject = models.ForeignKey(StudentCatalogPerSubject, on_delete=models.CASCADE, related_name="absences", related_query_name="absence")
    student = models.ForeignKey("profiles.UserProfile", on_delete=models.CASCADE, related_name="absences", related_query_name="absence")

    subject_name = models.CharField(max_length=100)
    academic_year = models.PositiveSmallIntegerField()
    semester = models.PositiveSmallIntegerField()
    taken_at = models.DateField()

    is_founded = models.BooleanField(default=False)

    objects = models.Manager()

    def __str__(self):
        return f"Absence {self.id}"

    class Meta:
        ordering = ['-taken_at', '-created']
