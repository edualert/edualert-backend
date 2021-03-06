from django.db import models
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel

from edualert.catalogs import constants
from edualert.catalogs.models import StudentCatalogPerSubject


class ExaminationGrade(TimeStampedModel):
    catalog_per_subject = models.ForeignKey(StudentCatalogPerSubject, on_delete=models.CASCADE, related_name="examination_grades", related_query_name="examination_grade")
    student = models.ForeignKey("profiles.UserProfile", on_delete=models.CASCADE, related_name="examination_grades", related_query_name="examination_grade")

    subject_name = models.CharField(max_length=100)
    academic_year = models.PositiveSmallIntegerField()
    taken_at = models.DateField()

    ExaminationTypes = constants.ExaminationTypes
    examination_type = models.CharField(max_length=64, choices=ExaminationTypes.choices)
    GradeTypes = constants.ExaminationGradeTypes
    grade_type = models.CharField(max_length=64, choices=GradeTypes.choices)
    grade1 = models.PositiveSmallIntegerField()
    grade2 = models.PositiveSmallIntegerField()

    semester = models.PositiveSmallIntegerField(null=True, blank=True, help_text=_('Only for Difference grades.'))

    objects = models.Manager()

    def __str__(self):
        return f"Examination grade {self.id}"

    class Meta:
        ordering = ['-taken_at', '-created']
