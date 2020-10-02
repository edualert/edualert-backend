from django.db import models
from django.utils.translation import gettext_lazy as _


class TeacherClassThrough(models.Model):
    study_class = models.ForeignKey("study_classes.StudyClass", related_name="teacher_class_through", on_delete=models.CASCADE)
    teacher = models.ForeignKey("profiles.UserProfile", related_name="teacher_class_through", on_delete=models.PROTECT)
    subject = models.ForeignKey("subjects.Subject", related_name="teacher_class_through", on_delete=models.CASCADE)

    is_class_master = models.BooleanField(default=False)
    academic_year = models.PositiveSmallIntegerField()

    class_grade = models.CharField(max_length=4, help_text=_("The roman number of the class."))
    class_letter = models.CharField(max_length=3)
    academic_program_name = models.CharField(max_length=128, null=True, blank=True)

    subject_name = models.CharField(max_length=100)
    is_optional_subject = models.BooleanField(default=False)
    is_coordination_subject = models.BooleanField(default=False)

    objects = models.Manager()

    def __str__(self):
        return f"TeacherClassThrough {self.class_grade} {self.class_letter} - {self.teacher.full_name} ({self.subject_name})"
