from dateutil.relativedelta import relativedelta

from edualert.academic_calendars.factories import AcademicYearCalendarFactory, SchoolEventFactory
from edualert.academic_calendars.models import AcademicYearCalendar, SemesterCalendar, SchoolEvent
from edualert.academic_calendars.utils import generate_next_year_academic_calendar
from edualert.common.api_tests import CommonAPITestCase


class GenerateNextYearAcademicCalendarTestCase(CommonAPITestCase):
    def test_generate_next_year_academic_calendar(self):
        current_calendar = AcademicYearCalendarFactory()
        event1 = SchoolEventFactory(semester=current_calendar.first_semester)
        event2 = SchoolEventFactory(semester=current_calendar.second_semester)
        event3 = SchoolEventFactory(academic_year_calendar=current_calendar)

        generate_next_year_academic_calendar()

        new_calendar = AcademicYearCalendar.objects.filter(academic_year=current_calendar.academic_year + 1).first()
        self.assertIsNotNone(new_calendar)
        self.assertTrue(SemesterCalendar.objects.filter(
            starts_at=current_calendar.first_semester.starts_at + relativedelta(years=1),
            ends_at=current_calendar.first_semester.ends_at + relativedelta(years=1),
            first_semester_academic_year_calendar=new_calendar
        ).exists())
        self.assertTrue(SemesterCalendar.objects.filter(
            starts_at=current_calendar.second_semester.starts_at + relativedelta(years=1),
            ends_at=current_calendar.second_semester.ends_at + relativedelta(years=1),
            second_semester_academic_year_calendar=new_calendar
        ).exists())
        for event in [event1, event2, event3]:
            self.assertTrue(SchoolEvent.objects.filter(
                starts_at=event.starts_at + relativedelta(years=1),
                ends_at=event.ends_at + relativedelta(years=1),
                academic_year_calendar=new_calendar if event.academic_year_calendar else None,
                semester=new_calendar.first_semester if event.semester == current_calendar.first_semester else new_calendar.second_semester if event.semester else None
            ).exists())
