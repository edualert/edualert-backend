from datetime import datetime

from ddt import data, ddt
from django.urls import reverse
from rest_framework import status

from edualert.academic_calendars.factories import AcademicYearCalendarFactory, SchoolEventFactory
from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory


@ddt
class CurrentAcademicYearCalendarRetrieveTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('academic_calendars:current-academic-year-calendar')
        cls.school_unit = RegisteredSchoolUnitFactory()

    def test_current_academic_year_calendar_retrieve_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_current_academic_year_calendar_retrieve_no_calendar(self):
        profile = UserProfileFactory(user_role=UserProfile.UserRoles.ADMINISTRATOR)
        self.client.login(username=profile.username, password='passwd')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.PRINCIPAL,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT,
        UserProfile.UserRoles.TEACHER,
    )
    def test_current_academic_year_calendar_retrieve(self, user_role):
        profile = UserProfileFactory(
            user_role=user_role,
            school_unit=self.school_unit if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )
        self.client.login(username=profile.username, password='passwd')

        # Create another academic year calendar in the past
        academic_year_calendar_past = AcademicYearCalendarFactory(academic_year=2019)
        academic_year_calendar_past.first_semester.starts_at = datetime(2019, 1, 1)
        academic_year_calendar_past.first_semester.save()

        academic_year_calendar = AcademicYearCalendarFactory()
        first_semester_event = SchoolEventFactory(
            semester=academic_year_calendar.first_semester,
            starts_at=datetime(2020, 1, 10)
        )
        first_semester_event.save()
        SchoolEventFactory(semester=academic_year_calendar.first_semester)
        SchoolEventFactory(semester=academic_year_calendar.second_semester)

        SchoolEventFactory(
            academic_year_calendar=academic_year_calendar,
            starts_at=datetime(2020, 2, 20),
            ends_at=datetime(2020, 3, 10)
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        current_year_data = response.data
        self.assertEqual(current_year_data['academic_year'], academic_year_calendar.academic_year)
        expected_fields = ['first_semester', 'second_semester', 'academic_year', 'events']
        self.assertCountEqual(expected_fields, current_year_data.keys())
        self.assertEqual(len(current_year_data['events']), 1)

        semester_expected_fields = ['id', 'starts_at', 'ends_at', 'events']
        self.assertCountEqual(current_year_data['first_semester'].keys(), semester_expected_fields)
        self.assertCountEqual(current_year_data['second_semester'].keys(), semester_expected_fields)

        first_semester_events = current_year_data['first_semester']['events']
        second_semester_events = current_year_data['second_semester']['events']

        # Test ordering
        self.assertGreater(first_semester_events[1]['starts_at'], first_semester_events[0]['starts_at'])

        event_expected_fields = ['id', 'event_type', 'starts_at', 'ends_at']
        for event in first_semester_events:
            self.assertCountEqual(event.keys(), event_expected_fields)
        for event in second_semester_events:
            self.assertCountEqual(event.keys(), event_expected_fields)
