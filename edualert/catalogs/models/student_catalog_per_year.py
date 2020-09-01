from django.db import models
from django.utils.translation import gettext_lazy as _


class StudentCatalogPerYear(models.Model):
    student = models.ForeignKey("profiles.UserProfile", on_delete=models.CASCADE, related_name="student_catalogs_per_year",
                                related_query_name="student_catalog_per_year")
    study_class = models.ForeignKey("study_classes.StudyClass", on_delete=models.CASCADE, related_name="student_catalogs_per_year",
                                    related_query_name="student_catalog_per_year")
    academic_year = models.PositiveSmallIntegerField()

    avg_sem1 = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    avg_sem2 = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    avg_annual = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    avg_final = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True,
                                    help_text=_("Represents either the average after 2nd examinations (if any) or the annual average."))

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
    second_examinations_count = models.PositiveSmallIntegerField(default=0)

    behavior_grade_sem1 = models.PositiveSmallIntegerField(default=10)
    behavior_grade_sem2 = models.PositiveSmallIntegerField(default=10)
    behavior_grade_annual = models.DecimalField(max_digits=4, decimal_places=2, default=10)

    class_place_by_avg_sem1 = models.PositiveSmallIntegerField(null=True, blank=True)
    class_place_by_avg_sem2 = models.PositiveSmallIntegerField(null=True, blank=True)
    class_place_by_avg_annual = models.PositiveSmallIntegerField(null=True, blank=True)

    school_place_by_avg_sem1 = models.PositiveSmallIntegerField(null=True, blank=True)
    school_place_by_avg_sem2 = models.PositiveSmallIntegerField(null=True, blank=True)
    school_place_by_avg_annual = models.PositiveSmallIntegerField(null=True, blank=True)

    class_place_by_abs_sem1 = models.PositiveSmallIntegerField(null=True, blank=True)
    class_place_by_abs_sem2 = models.PositiveSmallIntegerField(null=True, blank=True)
    class_place_by_abs_annual = models.PositiveSmallIntegerField(null=True, blank=True)

    school_place_by_abs_sem1 = models.PositiveSmallIntegerField(null=True, blank=True)
    school_place_by_abs_sem2 = models.PositiveSmallIntegerField(null=True, blank=True)
    school_place_by_abs_annual = models.PositiveSmallIntegerField(null=True, blank=True)

    objects = models.Manager()

    def __str__(self):
        return f"StudentCatalogPerYear {self.student.id} ({self.academic_year})"
