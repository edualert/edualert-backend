from django.db import models
from django.db.models.functions import Lower

from edualert.subjects.models import ProgramSubjectThrough


class AcademicProgram(models.Model):
    generic_academic_program = models.ForeignKey("academic_programs.GenericAcademicProgram", related_name="academic_programs",
                                                 on_delete=models.CASCADE)
    school_unit = models.ForeignKey("schools.RegisteredSchoolUnit", related_name="academic_programs",
                                    related_query_name="academic_program", on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    academic_year = models.PositiveSmallIntegerField()
    core_subject = models.ForeignKey("subjects.Subject", null=True, blank=True, on_delete=models.SET_NULL,
                                     related_name="main_academic_programs", related_query_name="main_academic_program")
    optional_subjects = models.ManyToManyField("subjects.Subject", through=ProgramSubjectThrough, blank=True,
                                               related_name="academic_programs", related_query_name="academic_program")

    classes_count = models.PositiveSmallIntegerField(default=0)
    students_at_risk_count = models.PositiveSmallIntegerField(default=0)

    avg_sem1 = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    avg_sem2 = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    avg_annual = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)

    unfounded_abs_avg_sem1 = models.PositiveSmallIntegerField(null=True, blank=True)
    unfounded_abs_avg_sem2 = models.PositiveSmallIntegerField(null=True, blank=True)
    unfounded_abs_avg_annual = models.PositiveSmallIntegerField(null=True, blank=True)

    objects = models.Manager()

    class Meta:
        ordering = (Lower('name'),)

    def __str__(self):
        return f"AcademicProgram {self.id} {self.name} - {self.academic_year}"
