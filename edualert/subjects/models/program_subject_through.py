from django.db import models


class ProgramSubjectThrough(models.Model):
    generic_academic_program = models.ForeignKey("academic_programs.GenericAcademicProgram",
                                                 null=True, blank=True, on_delete=models.CASCADE,
                                                 related_name="program_subjects_through",
                                                 related_query_name="program_subject_through")
    academic_program = models.ForeignKey("academic_programs.AcademicProgram",
                                         null=True, blank=True, on_delete=models.CASCADE,
                                         related_name="program_subjects_through",
                                         related_query_name="program_subject_through")

    subject = models.ForeignKey("subjects.Subject", on_delete=models.CASCADE,
                                related_name="program_subjects_through",
                                related_query_name="program_subject_through")
    subject_name = models.CharField(max_length=100)

    class_grade = models.CharField(max_length=4)
    class_grade_arabic = models.PositiveSmallIntegerField()

    weekly_hours_count = models.PositiveSmallIntegerField()
    is_mandatory = models.BooleanField(default=True)

    objects = models.Manager()

    def __str__(self):
        if self.generic_academic_program:
            return f"ProgramSubjectThrough {self.id} {self.generic_academic_program.name} - {self.subject_name}"

        return f"ProgramSubjectThrough {self.id} {self.academic_program.name} - {self.subject_name}"
