from django.db import models
from django.db.models.signals import post_save, post_delete
from django.utils.translation import gettext_lazy as _

from edualert.study_classes.signals import study_class_post_save, study_class_post_delete


class StudyClass(models.Model):
    school_unit = models.ForeignKey("schools.RegisteredSchoolUnit", related_name="study_classes",
                                    related_query_name="study_class", on_delete=models.CASCADE)

    academic_program = models.ForeignKey("academic_programs.AcademicProgram", null=True, blank=True, related_name="study_classes",
                                         related_query_name="study_class", on_delete=models.CASCADE)
    academic_program_name = models.CharField(max_length=128, null=True, blank=True)
    academic_year = models.PositiveSmallIntegerField()

    class_grade = models.CharField(max_length=4, help_text=_("The roman number of the class."))
    class_grade_arabic = models.PositiveSmallIntegerField()
    class_letter = models.CharField(max_length=3)

    class_master = models.ForeignKey("profiles.UserProfile", related_name="mastering_study_classes",
                                     related_query_name="mastering_study_classes", on_delete=models.PROTECT)
    teachers = models.ManyToManyField("profiles.UserProfile", through="study_classes.TeacherClassThrough",
                                      related_name="study_classes", related_query_name="study_class")

    students_at_risk_count = models.PositiveSmallIntegerField(default=0)

    avg_sem1 = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    avg_sem2 = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    avg_annual = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)

    unfounded_abs_avg_sem1 = models.PositiveSmallIntegerField(null=True, blank=True)
    unfounded_abs_avg_sem2 = models.PositiveSmallIntegerField(null=True, blank=True)
    unfounded_abs_avg_annual = models.PositiveSmallIntegerField(null=True, blank=True)

    objects = models.Manager()

    class Meta:
        ordering = ('class_grade_arabic', 'class_letter')
        verbose_name_plural = 'study classes'

    def __str__(self):
        return f"StudyClass {self.class_grade} {self.class_letter} - {self.academic_year}"


post_save.connect(study_class_post_save, sender=StudyClass)
post_delete.connect(study_class_post_delete, sender=StudyClass)
