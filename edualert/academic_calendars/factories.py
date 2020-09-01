import factory

from datetime import date
from factory.django import DjangoModelFactory

from edualert.academic_calendars.models import AcademicYearCalendar, SemesterCalendar, SchoolEvent


class SemesterCalendarFactory(DjangoModelFactory):
    class Meta:
        model = SemesterCalendar

    starts_at = date(2020, 9, 9)
    ends_at = date(2020, 9, 20)
    working_weeks_count = 15
    working_weeks_count_primary_school = 13
    working_weeks_count_8_grade = 13
    working_weeks_count_12_grade = 13
    working_weeks_count_technological = 17


class AcademicYearCalendarFactory(DjangoModelFactory):
    class Meta:
        model = AcademicYearCalendar

    academic_year = 2020

    first_semester = factory.SubFactory(
        SemesterCalendarFactory,
        starts_at=date(2019, 9, 9),
        ends_at=date(2019, 12, 20)
    )

    second_semester = factory.SubFactory(
        SemesterCalendarFactory,
        starts_at=date(2020, 1, 13),
        ends_at=date(2020, 6, 12)
    )


class SchoolEventFactory(DjangoModelFactory):
    class Meta:
        model = SchoolEvent

    event_type = SchoolEvent.EventTypes.LEGAL_PUBLIC_HOLIDAY
    starts_at = date(2020, 4, 12)
    ends_at = date(2020, 4, 19)
