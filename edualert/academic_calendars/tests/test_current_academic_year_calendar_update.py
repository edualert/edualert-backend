from datetime import datetime

from ddt import data, ddt
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from edualert.academic_calendars.factories import AcademicYearCalendarFactory, SchoolEventFactory
from edualert.academic_calendars.models import SchoolEvent
from edualert.common.api_tests import CommonAPITestCase
from edualert.common.utils import date
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory


@ddt
class CurrentAcademicYearCalendarUpdateTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('academic_calendars:current-academic-year-calendar')
        cls.admin = UserProfileFactory(user_role=UserProfile.UserRoles.ADMINISTRATOR)
        cls.school_unit = RegisteredSchoolUnitFactory()
        cls.next_year = timezone.now().year + 1

    def setUp(self):
        self.academic_year_calendar = AcademicYearCalendarFactory(
            first_semester__starts_at=datetime(self.next_year, 1, 10),
            first_semester__ends_at=datetime(self.next_year, 4, 3),
            second_semester__starts_at=datetime(self.next_year, 9, 9),
            second_semester__ends_at=datetime(self.next_year, 12, 11)
        )
        self.data = {
            'first_semester': {
                'id': self.academic_year_calendar.first_semester.id,
                'starts_at': date(self.next_year, 1, 1),
                'ends_at': date(self.next_year, 4, 4),
                'events': []
            },
            'second_semester': {
                'id': self.academic_year_calendar.second_semester.id,
                'starts_at': date(self.next_year, 9, 9),
                'ends_at': date(self.next_year, 12, 12),
                'events': []
            },
            'events': []
        }

    def test_current_academic_year_calendar_update_unauthenticated(self):
        response = self.client.put(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.PRINCIPAL,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT,
        UserProfile.UserRoles.TEACHER,
    )
    def test_current_academic_year_calendar_update_wrong_user_type(self, user_role):
        profile = UserProfileFactory(user_role=user_role, school_unit=self.school_unit)
        self.client.login(username=profile.username, password='passwd')

        response = self.client.put(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        profile.delete()

    def test_current_academic_year_calendar_update_no_current_calendar(self):
        self.client.login(username=self.admin.username, password='passwd')
        self.academic_year_calendar.delete()
        response = self.client.put(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_current_academic_year_calendar_update_required_fields(self):
        self.client.login(username=self.admin.username, password='passwd')

        # Missing required fields
        required_fields = ['first_semester', 'second_semester', 'events']
        for field in required_fields:
            req_data = {
                required_field: self.data[required_field]
                for required_field in required_fields if required_field != field
            }
            response = self.client.put(self.url, req_data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertCountEqual(response.data.values(), [['This field is required.']])

        semester_required_fields = ['starts_at', 'ends_at', 'events']
        for field in semester_required_fields:
            req_data = {
                'first_semester': {
                    expected_field: self.data['first_semester'][expected_field]
                    for expected_field in semester_required_fields if expected_field != field
                },
                'second_semester': self.data['second_semester']
            }

            response = self.client.put(self.url, req_data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data['first_semester'][field], ['This field is required.'])

        event = SchoolEventFactory(semester=self.academic_year_calendar.first_semester)
        event_expected_fields_and_value = {
            'event_type': event.event_type,
            'starts_at': event.starts_at.strftime(settings.DATE_FORMAT),
            'ends_at': event.ends_at.strftime(settings.DATE_FORMAT)
        }
        for field, value in event_expected_fields_and_value.items():
            req_data = {
                'first_semester': {
                    'id': self.academic_year_calendar.first_semester.id,
                    'starts_at': self.data['first_semester']['starts_at'],
                    'ends_at': self.data['first_semester']['ends_at'],
                    'events': [{
                        expected_field: event_expected_fields_and_value[expected_field]
                        for expected_field in event_expected_fields_and_value.keys() if expected_field != field
                    }]
                },
                'second_semester': self.data['second_semester'],
                'events': []
            }
            response = self.client.put(self.url, req_data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data, {'first_semester': {'events': [{field: ['This field is required.']}]}})

    @data(
        'first_semester', None
    )
    def test_current_academic_year_calendar_update_event_validation(self, event_belongs_to):
        self.client.login(username=self.admin.username, password='passwd')

        # Event ID doesn't exist
        if event_belongs_to:
            data_dict = self.data['first_semester']
            event_type = SchoolEvent.EventTypes.SPRING_HOLIDAY
        else:
            data_dict = self.data
            event_type = SchoolEvent.EventTypes.CORIGENTE

        data_dict['events'] = [{
            'id': 0,
            'starts_at': date(self.next_year, 2, 2),
            'ends_at': date(self.next_year, 2, 3),
            'event_type': event_type
        }]
        response = self.client.put(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.data if not event_belongs_to else response.data['first_semester']
        self.assertEqual(response_data, {'events': {'id': 'The events must belong to this academic year.'}})

        # Start or end date are in the past
        # TODO uncomment this after it's implemented & tested on FE
        # last_year = timezone.now().year - 1
        # data_dict['events'] = [{
        #     'starts_at': date(last_year, 2, 2),
        #     'ends_at': date(last_year, 3, 3),
        #     'event_type': event_type
        # }]
        # response = self.client.put(self.url, self.data)
        # self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # response_data = response.data if not event_type else response.data['first_semester']
        #
        # self.assertEqual(response_data, {'events': [{'starts_at': ['The start date must be in the future.']}]})
        #
        # data_dict['events'][0]['starts_at'] = date(self.next_year, 2, 2)
        # response = self.client.put(self.url, self.data)
        # self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # response_data = response.data if not event_type else response.data['first_semester']
        # self.assertEqual(response_data, {'events': [{'ends_at': ['The end date must be in the future.']}]})

        # End date is before start date
        data_dict['events'] = [{
            'starts_at': date(self.next_year, 10, 10),
            'ends_at': date(self.next_year, 10, 9),
            'event_type': event_type
        }]
        response = self.client.put(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.data if not event_belongs_to else response.data['first_semester']
        self.assertEqual(response_data, {'events': [{'starts_at': ['The start date must be before the end date.']}]})

        # Events are outside the semester
        data_dict['events'] = [{
            'starts_at': date(self.next_year, 5, 5),
            'ends_at': date(self.next_year, 6, 6),
            'event_type': event_type
        }]
        response = self.client.put(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        if event_belongs_to == 'first_semester':
            self.assertEqual(response.data['first_semester'], {'events': {'starts_at': "All events must be between the semester's start and end dates."}})
        else:
            self.assertEqual(response.data, {'events': {'starts_at': f'{event_type.label} must be between the second semester end date and the end of the current year.'}})

        # semester end events must belong to the second semester
        for event in [
            SchoolEvent.EventTypes.SECOND_SEMESTER_END_VIII_GRADE,
            SchoolEvent.EventTypes.SECOND_SEMESTER_END_XII_XIII_GRADE
        ]:
            data_dict['events'] = [{
                'starts_at': date(self.next_year, 2, 2),
                'ends_at': date(self.next_year, 2, 3),
                'event_type': event
            }]

            response = self.client.put(self.url, self.data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            if not event_belongs_to:
                self.assertEqual(
                    response.data,
                    {'events':
                        {'event_type': f"{event.label} must belong to a semester."}}
                )
            else:
                self.assertEqual(
                    response.data['first_semester'],
                    {'events':
                        {'event_type': f"{event.label} must belong to the second semester."}}
                )

    def test_current_academic_year_calendar_update_semester_events_validation(self):
        self.client.login(username=self.admin.username, password='passwd')

        for bad_data in [
            [{
                'starts_at': date(self.next_year, 1, 2),
                'ends_at': date(self.next_year, 3, 3),
                'event_type': SchoolEvent.EventTypes.SPRING_HOLIDAY
            }, {
                'starts_at': date(self.next_year, 2, 5),
                'ends_at': date(self.next_year, 3, 2),
                'event_type': SchoolEvent.EventTypes.LEGAL_PUBLIC_HOLIDAY
            }],
            [{
                'starts_at': date(self.next_year, 2, 2),
                'ends_at': date(self.next_year, 3, 3),
                'event_type': SchoolEvent.EventTypes.SPRING_HOLIDAY
            }, {
                'starts_at': date(self.next_year, 3, 3),
                'ends_at': date(self.next_year, 4, 1),
                'event_type': SchoolEvent.EventTypes.LEGAL_PUBLIC_HOLIDAY
            }],
            [{
                'starts_at': date(self.next_year, 2, 2),
                'ends_at': date(self.next_year, 2, 5),
                'event_type': SchoolEvent.EventTypes.SPRING_HOLIDAY
            }, {
                'starts_at': date(self.next_year, 2, 3),
                'ends_at': date(self.next_year, 2, 4),
                'event_type': SchoolEvent.EventTypes.LEGAL_PUBLIC_HOLIDAY
            }]
        ]:
            self.data['first_semester']['events'] = bad_data
            response = self.client.put(self.url, self.data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data, {'events': ['Events cannot overlap.']})

        # CORIGENTE and DIFERENTE can't be added inside the semester
        for event_type in [
            SchoolEvent.EventTypes.CORIGENTE,
            SchoolEvent.EventTypes.DIFERENTE
        ]:
            self.data['first_semester']['events'] = [{
                'starts_at': date(self.next_year, 3, 3),
                'ends_at': date(self.next_year, 4, 4),
                'event_type': event_type
            }]
            response = self.client.put(self.url, self.data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data, {'first_semester': {'events': [f'{event_type.label} events cannot be inside semesters.']}})

        # SECOND_SEMESTER_END_IX_XI_FILIERA_TEHNOLOGICA must be between second semester start and the end of the school year
        self.data['first_semester']['events'] = []
        self.data['second_semester']['events'] = [{
            'starts_at': date(self.next_year, 5, 5),
            'ends_at': date(self.next_year, 5, 6),
            'event_type': SchoolEvent.EventTypes.SECOND_SEMESTER_END_IX_XI_FILIERA_TEHNOLOGICA
        }]
        response = self.client.put(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data,
            {'events': {'starts_at': "Second semester end for Filiera Tehnologica"
                                     " must be between the second semester's start and the end of"
                                     " the current academic year."}})

    def test_current_academic_year_calendar_update_year_events_validation(self):
        self.client.login(username=self.admin.username, password='passwd')
        for bad_data in [
            [{
                'starts_at': date(self.next_year, 12, 21),
                'ends_at': date(self.next_year, 12, 23),
                'event_type': SchoolEvent.EventTypes.CORIGENTE
            }, {
                'starts_at': date(self.next_year, 12, 22),
                'ends_at': date(self.next_year, 12, 25),
                'event_type': SchoolEvent.EventTypes.CORIGENTE
            }],
            [{
                'starts_at': date(self.next_year, 12, 23),
                'ends_at': date(self.next_year, 12, 25),
                'event_type': SchoolEvent.EventTypes.DIFERENTE
            }, {
                'starts_at': date(self.next_year, 12, 23),
                'ends_at': date(self.next_year, 12, 26),
                'event_type': SchoolEvent.EventTypes.CORIGENTE
            }],
            [{
                'starts_at': date(self.next_year, 12, 22),
                'ends_at': date(self.next_year, 12, 25),
                'event_type': SchoolEvent.EventTypes.DIFERENTE
            }, {
                'starts_at': date(self.next_year, 12, 23),
                'ends_at': date(self.next_year, 12, 24),
                'event_type': SchoolEvent.EventTypes.DIFERENTE
            }]
        ]:
            self.data['events'] = bad_data
            response = self.client.put(self.url, self.data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data, {'events': ['Events cannot overlap.']})

    def test_current_academic_year_calendar_update_semester_validation(self):
        self.client.login(username=self.admin.username, password='passwd')

        other_calendar = AcademicYearCalendarFactory(academic_year=2019)
        self.data['first_semester']['id'] = other_calendar.first_semester.id

        response = self.client.put(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'first_semester': ['The semester must belong to the academic year.']})

        self.data['first_semester']['id'] = self.academic_year_calendar.first_semester.id
        self.data['first_semester']['starts_at'] = self.data['first_semester']['ends_at']
        response = self.client.put(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'first_semester': {'starts_at': ['The start date must be before the end date.']}})

        self.data['first_semester']['starts_at'] = date(self.next_year, 1, 1)
        self.data['first_semester']['ends_at'] = date(self.next_year, 10, 10)
        self.data['second_semester']['starts_at'] = date(self.next_year, 5, 5)
        self.data['second_semester']['ends_at'] = date(self.next_year, 12, 12)
        response = self.client.put(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'second_semester': ['Second semester must start after the end of the first semester.']})

        self.data['first_semester']['starts_at'] = date(self.next_year, 1, 1)
        self.data['first_semester']['ends_at'] = date(self.next_year, 5, 5)
        self.data['second_semester']['starts_at'] = date(self.next_year, 6, 6)
        self.data['second_semester']['ends_at'] = date(self.next_year, 4, 4)
        response = self.client.put(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'second_semester': {'starts_at': ['The start date must be before the end date.']}})

        # TODO uncomment this after it's implemented & tested on FE
        # last_year = timezone.now().year - 1
        # self.data['first_semester']['starts_at'] = date(last_year, 1, 1)
        # self.data['first_semester']['ends_at'] = date(last_year, 6, 6)
        # response = self.client.put(self.url, self.data)
        # self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # self.assertEqual(response.data, {'first_semester': {'starts_at': ['The start date must be in the future.']}})

    def test_current_academic_year_calendar_update_success(self):
        self.client.login(username=self.admin.username, password='passwd')

        response = self.client.put(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.academic_year_calendar.refresh_from_db()

        expected_fields = ['first_semester', 'second_semester', 'academic_year', 'events']
        self.assertCountEqual(expected_fields, response.data.keys())

        semester_expected_fields = ['id', 'starts_at', 'ends_at', 'events']
        self.assertCountEqual(semester_expected_fields, response.data['first_semester'])
        self.assertCountEqual(semester_expected_fields, response.data['second_semester'])
        for semester in ['first_semester', 'second_semester']:
            self.assertEqual(
                getattr(self.academic_year_calendar, semester).starts_at.strftime(settings.DATE_FORMAT),
                self.data[semester]['starts_at']
            )

        # Try to add an event
        self.data['first_semester']['events'] = [{
            'starts_at': date(self.next_year, 2, 2),
            'ends_at': date(self.next_year, 2, 3),
            'event_type': SchoolEvent.EventTypes.LEGAL_PUBLIC_HOLIDAY
        }]
        response = self.client.put(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        event = self.academic_year_calendar.first_semester.school_events.first()
        self.assertEqual(event.starts_at, event.starts_at)

        # Update it
        self.data['first_semester']['events'] = [{
            'id': event.id,
            'starts_at': date(self.next_year, 2, 2),
            'ends_at': date(self.next_year, 2, 3),
            'event_type': SchoolEvent.EventTypes.SPRING_HOLIDAY
        }]
        response = self.client.put(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        event.refresh_from_db()
        self.assertEqual(event.event_type, SchoolEvent.EventTypes.SPRING_HOLIDAY)

        # Add new ones
        self.data['first_semester']['events'] += [
            {
                'starts_at': date(self.next_year, 2, 6),
                'ends_at': date(self.next_year, 2, 10),
                'event_type': SchoolEvent.EventTypes.LEGAL_PUBLIC_HOLIDAY
            },
            {
                'starts_at': date(self.next_year, 3, 2),
                'ends_at': date(self.next_year, 3, 3),
                'event_type': SchoolEvent.EventTypes.LEGAL_PUBLIC_HOLIDAY
            }
        ]
        response = self.client.put(self.url, self.data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.academic_year_calendar.first_semester.school_events.count(), 3)

        # Remove one of them
        self.data['first_semester']['events'].pop()
        response = self.client.put(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.academic_year_calendar.first_semester.school_events.count(), 2)
