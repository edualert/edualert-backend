from django.db import models
from django_extensions.db.models import TimeStampedModel


class SemesterCalendar(models.Model):
    starts_at = models.DateField()
    ends_at = models.DateField()
    working_weeks_count = models.PositiveSmallIntegerField()
    working_weeks_count_primary_school = models.PositiveSmallIntegerField()
    working_weeks_count_8_grade = models.PositiveSmallIntegerField()
    working_weeks_count_12_grade = models.PositiveSmallIntegerField()
    working_weeks_count_technological = models.PositiveSmallIntegerField()

    objects = models.Manager()

    def __str__(self):
        return f'SemesterCalendar {self.id}'


class AcademicYearCalendar(TimeStampedModel):
    academic_year = models.PositiveSmallIntegerField(unique=True)
    first_semester = models.OneToOneField(SemesterCalendar, on_delete=models.PROTECT, related_name='first_semester_academic_year_calendar')
    second_semester = models.OneToOneField(SemesterCalendar, on_delete=models.PROTECT, related_name='second_semester_academic_year_calendar')

    objects = models.Manager()

    def __str__(self):
        return f'AcademicYearCalendar {self.academic_year}'
