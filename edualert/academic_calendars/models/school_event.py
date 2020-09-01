from django.db import models

from edualert.academic_calendars import constants


class SchoolEvent(models.Model):
    EventTypes = constants.EventTypes
    event_type = models.CharField(choices=EventTypes.choices, max_length=64)

    starts_at = models.DateField()
    ends_at = models.DateField()
    semester = models.ForeignKey('SemesterCalendar', on_delete=models.CASCADE, related_name='school_events', null=True, blank=True)
    academic_year_calendar = models.ForeignKey('AcademicYearCalendar', on_delete=models.CASCADE, related_name='school_events', null=True, blank=True)

    objects = models.Manager()

    def __str__(self):
        return f'SchoolEvent {self.id} {self.event_type}'

    class Meta:
        ordering = ['starts_at']
