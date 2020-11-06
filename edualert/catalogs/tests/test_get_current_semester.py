from datetime import date
from unittest.mock import patch

from ddt import ddt
from django.utils import timezone
from pytz import utc

from edualert.academic_calendars.factories import AcademicYearCalendarFactory, SchoolEventFactory
from edualert.academic_calendars.models import SchoolEvent
from edualert.academic_calendars.utils import get_second_semester_end_events
from edualert.catalogs.utils import get_current_semester
from edualert.common.api_tests import CommonAPITestCase


@ddt
class GetCurrentSemesterTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year_calendar = AcademicYearCalendarFactory()
        cls.create_semester_end_events(cls.academic_year_calendar)
        cls.second_semester_end_events = get_second_semester_end_events(cls.academic_year_calendar)

    @staticmethod
    def create_semester_end_events(calendar):
        SchoolEventFactory(
            academic_year_calendar=calendar,
            semester=calendar.second_semester,
            event_type=SchoolEvent.EventTypes.SECOND_SEMESTER_END_XII_XIII_GRADE,
            starts_at=date(2020, 5, 29),
            ends_at=date(2020, 5, 29)
        )
        SchoolEventFactory(
            academic_year_calendar=calendar,
            semester=calendar.second_semester,
            event_type=SchoolEvent.EventTypes.SECOND_SEMESTER_END_VIII_GRADE,
            starts_at=date(2020, 6, 5),
            ends_at=date(2020, 6, 5)
        )
        SchoolEventFactory(
            academic_year_calendar=calendar,
            semester=calendar.second_semester,
            event_type=SchoolEvent.EventTypes.SECOND_SEMESTER_END_IX_XI_FILIERA_TEHNOLOGICA,
            starts_at=date(2020, 6, 26),
            ends_at=date(2020, 6, 26)
        )

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2019, 9, 10).replace(tzinfo=utc))
    def test_get_current_semester_during_first_semester(self, mocked_method):
        self.assertEqual(get_current_semester(timezone.now().date(), self.academic_year_calendar, self.second_semester_end_events, 7, False), 1)
        self.assertEqual(get_current_semester(timezone.now().date(), self.academic_year_calendar, self.second_semester_end_events, 8, False), 1)
        self.assertEqual(get_current_semester(timezone.now().date(), self.academic_year_calendar, self.second_semester_end_events, 9, False), 1)
        self.assertEqual(get_current_semester(timezone.now().date(), self.academic_year_calendar, self.second_semester_end_events, 10, True), 1)
        self.assertEqual(get_current_semester(timezone.now().date(), self.academic_year_calendar, self.second_semester_end_events, 12, False), 1)

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 1, 14).replace(tzinfo=utc))
    def test_get_current_semester_during_second_semester(self, mocked_method):
        self.assertEqual(get_current_semester(timezone.now().date(), self.academic_year_calendar, self.second_semester_end_events, 7, False), 2)
        self.assertEqual(get_current_semester(timezone.now().date(), self.academic_year_calendar, self.second_semester_end_events, 8, False), 2)
        self.assertEqual(get_current_semester(timezone.now().date(), self.academic_year_calendar, self.second_semester_end_events, 9, False), 2)
        self.assertEqual(get_current_semester(timezone.now().date(), self.academic_year_calendar, self.second_semester_end_events, 10, True), 2)
        self.assertEqual(get_current_semester(timezone.now().date(), self.academic_year_calendar, self.second_semester_end_events, 12, False), 2)

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 5, 30).replace(tzinfo=utc))
    def test_get_current_semester_second_semester_after_12_grade_end(self, mocked_method):
        self.assertEqual(get_current_semester(timezone.now().date(), self.academic_year_calendar, self.second_semester_end_events, 7, False), 2)
        self.assertEqual(get_current_semester(timezone.now().date(), self.academic_year_calendar, self.second_semester_end_events, 8, False), 2)
        self.assertEqual(get_current_semester(timezone.now().date(), self.academic_year_calendar, self.second_semester_end_events, 9, False), 2)
        self.assertEqual(get_current_semester(timezone.now().date(), self.academic_year_calendar, self.second_semester_end_events, 10, True), 2)
        self.assertEqual(get_current_semester(timezone.now().date(), self.academic_year_calendar, self.second_semester_end_events, 12, False), None)

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 6, 6).replace(tzinfo=utc))
    def test_get_current_semester_second_semester_after_8_grade_end(self, mocked_method):
        self.assertEqual(get_current_semester(timezone.now().date(), self.academic_year_calendar, self.second_semester_end_events, 7, False), 2)
        self.assertEqual(get_current_semester(timezone.now().date(), self.academic_year_calendar, self.second_semester_end_events, 8, False), None)
        self.assertEqual(get_current_semester(timezone.now().date(), self.academic_year_calendar, self.second_semester_end_events, 9, False), 2)
        self.assertEqual(get_current_semester(timezone.now().date(), self.academic_year_calendar, self.second_semester_end_events, 10, True), 2)
        self.assertEqual(get_current_semester(timezone.now().date(), self.academic_year_calendar, self.second_semester_end_events, 12, False), None)

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 6, 12).replace(tzinfo=utc))
    def test_get_current_semester_second_semester_after_regular_end(self, mocked_method):
        self.assertEqual(get_current_semester(timezone.now().date(), self.academic_year_calendar, self.second_semester_end_events, 7, False), None)
        self.assertEqual(get_current_semester(timezone.now().date(), self.academic_year_calendar, self.second_semester_end_events, 8, False), None)
        self.assertEqual(get_current_semester(timezone.now().date(), self.academic_year_calendar, self.second_semester_end_events, 9, False), None)
        self.assertEqual(get_current_semester(timezone.now().date(), self.academic_year_calendar, self.second_semester_end_events, 10, True), 2)
        self.assertEqual(get_current_semester(timezone.now().date(), self.academic_year_calendar, self.second_semester_end_events, 12, False), None)

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 6, 27).replace(tzinfo=utc))
    def test_get_current_semester_second_semester_after_technological_end(self, mocked_method):
        self.assertEqual(get_current_semester(timezone.now().date(), self.academic_year_calendar, self.second_semester_end_events, 7, False), None)
        self.assertEqual(get_current_semester(timezone.now().date(), self.academic_year_calendar, self.second_semester_end_events, 8, False), None)
        self.assertEqual(get_current_semester(timezone.now().date(), self.academic_year_calendar, self.second_semester_end_events, 9, False), None)
        self.assertEqual(get_current_semester(timezone.now().date(), self.academic_year_calendar, self.second_semester_end_events, 10, True), None)
        self.assertEqual(get_current_semester(timezone.now().date(), self.academic_year_calendar, self.second_semester_end_events, 12, False), None)
