from django.db import models
from django.utils.translation import gettext_lazy as _


class StudentCatalogPerSubject(models.Model):
    student = models.ForeignKey("profiles.UserProfile", on_delete=models.CASCADE, related_name="student_catalogs_per_subject",
                                related_query_name="student_catalog_per_subject")
    teacher = models.ForeignKey("profiles.UserProfile", on_delete=models.PROTECT, related_name="teacher_catalogs_per_subject",
                                related_query_name="teacher_catalog_per_subject")

    study_class = models.ForeignKey("study_classes.StudyClass", on_delete=models.CASCADE, related_name="student_catalogs_per_subject",
                                    related_query_name="student_catalog_per_subject")
    academic_year = models.PositiveSmallIntegerField()

    subject = models.ForeignKey("subjects.Subject", on_delete=models.CASCADE, related_name="student_catalogs_per_subject",
                                related_query_name="student_catalog_per_subject")
    subject_name = models.CharField(max_length=100)
    is_coordination_subject = models.BooleanField(default=False)

    avg_sem1 = models.PositiveSmallIntegerField(null=True, blank=True)
    avg_sem2 = models.PositiveSmallIntegerField(null=True, blank=True)
    avg_annual = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    avg_after_2nd_examination = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    avg_final = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True,
                                    help_text=_("Represents either the average after 2nd examination (if there is one) or the annual average."))

    abs_count_sem1 = models.PositiveSmallIntegerField(default=0)
    abs_count_sem2 = models.PositiveSmallIntegerField(default=0)
    abs_count_annual = models.PositiveSmallIntegerField(default=0)

    unfounded_abs_count_sem1 = models.PositiveSmallIntegerField(default=0)
    unfounded_abs_count_sem2 = models.PositiveSmallIntegerField(default=0)
    unfounded_abs_count_annual = models.PositiveSmallIntegerField(default=0)

    founded_abs_count_sem1 = models.PositiveSmallIntegerField(default=0)
    founded_abs_count_sem2 = models.PositiveSmallIntegerField(default=0)
    founded_abs_count_annual = models.PositiveSmallIntegerField(default=0)

    remarks = models.TextField(null=True, blank=True)
    is_at_risk = models.BooleanField(default=False)

    wants_level_testing_grade = models.BooleanField(default=False)
    wants_thesis = models.BooleanField(default=False)
    wants_simulation = models.BooleanField(default=False)
    is_exempted = models.BooleanField(default=False)
    is_enrolled = models.BooleanField(default=True)

    objects = models.Manager()

    def __str__(self):
        return f"StudentCatalogPerSubject {self.student.id} - {self.subject_name} ({self.academic_year})"
