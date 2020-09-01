from copy import copy

from ddt import data, ddt
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from edualert.academic_calendars.factories import AcademicYearCalendarFactory
from edualert.common.api_tests import CommonAPITestCase
from edualert.common.constants import WEEKDAYS_MAP
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import SchoolUnitProfileFactory, RegisteredSchoolUnitFactory, SchoolUnitCategoryFactory
from edualert.schools.models import RegisteredSchoolUnit
from edualert.statistics.factories import SchoolUnitEnrollmentStatsFactory
from edualert.statistics.models import SchoolUnitStats, StudentAtRiskCounts


@ddt
class RegisteredSchoolUnitCreateTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = UserProfileFactory(user_role=UserProfile.UserRoles.ADMINISTRATOR)
        cls.calendar = AcademicYearCalendarFactory()
        cls.academic_profile = SchoolUnitProfileFactory()

        cls.url = reverse('schools:school-unit-list')

    def setUp(self):
        self.principal = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL)
        self.request_data = {
            'categories': [self.academic_profile.category.id],
            'academic_profile': self.academic_profile.id,
            'school_principal': self.principal.id,
            'address': 'address',
            'phone_number': '+0799111222',
            'email': 'john.doe@gmail.com',
            'district': 'district',
            'city': 'city',
            'name': 'name'
        }

    def test_registered_school_unit_create_unauthenticated(self):
        response = self.client.post(self.url, self.request_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.TEACHER,
        UserProfile.UserRoles.PRINCIPAL,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_registered_school_unit_create_wrong_user_type(self, user_role):
        school_unit = RegisteredSchoolUnitFactory()
        user = UserProfileFactory(user_role=user_role, school_unit=school_unit)
        self.client.login(username=user.username, password='passwd')

        response = self.client.post(self.url, self.request_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_registered_school_unit_create_missing_fields(self):
        self.client.login(username=self.admin_user.username, password='passwd')
        required_fields = ['categories', 'address', 'phone_number', 'email',
                           'school_principal', 'district', 'city', 'name']

        request_data = copy(self.request_data)

        for field in required_fields:
            del request_data[field]
            response = self.client.post(self.url, request_data)

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data, {field: ['This field is required.']})

            request_data = copy(self.request_data)

    def test_registered_school_unit_create_validate_phone_number(self):
        self.client.login(username=self.admin_user.username, password='passwd')

        invalid_phone_numbers = [
            'abc',
            '+3232',
            '32324',
            '123456789123456789122'
            '++2392321234'
        ]
        for phone_number in invalid_phone_numbers:
            self.request_data['phone_number'] = phone_number

            response = self.client.post(self.url, self.request_data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data, {'phone_number': ['Invalid format. Must be minimum 10, maximum 20 digits or +.']})

    def test_registered_school_unit_create_validate_principal(self):
        self.client.login(username=self.admin_user.username, password='passwd')

        # Inexistent school principal
        self.request_data['school_principal'] = 0
        response = self.client.post(self.url, self.request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'school_principal': ['Invalid pk "0" - object does not exist.']})

        # Inactive principal
        self.principal.is_active = False
        self.principal.save()
        self.request_data['school_principal'] = self.principal.id

        response = self.client.post(self.url, self.request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'school_principal': ['Invalid user.']})

        self.principal.is_active = True
        self.principal.save()

        # The school principal is already assigned to another school
        RegisteredSchoolUnitFactory(school_principal=self.principal)
        response = self.client.post(self.url, self.request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'school_principal': ['This field must be unique.']})

    def test_registered_school_unit_create_validate_categories(self):
        self.client.login(username=self.admin_user.username, password='passwd')

        # Invalid categories
        self.request_data['categories'] = [0]
        response = self.client.post(self.url, self.request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'categories': ['Invalid pk "0" - object does not exist.']})

        # Multiple categories from the same level
        self.request_data['categories'] = [
            self.academic_profile.category.id,
            SchoolUnitCategoryFactory().id
        ]
        response = self.client.post(self.url, self.request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'categories': ['Cannot have multiple categories for the same school level.']})

    def test_registered_school_unit_create_validate_academic_profile(self):
        self.client.login(username=self.admin_user.username, password='passwd')

        academic_profile2 = SchoolUnitProfileFactory()

        self.request_data['academic_profile'] = academic_profile2.id
        response = self.client.post(self.url, self.request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'academic_profile': ['The academic profile does not correspond with the school category.']})

    def test_registered_school_unit_create_duplicate_school(self):
        self.client.login(username=self.admin_user.username, password='passwd')
        RegisteredSchoolUnitFactory(name=self.request_data['name'], district=self.request_data['district'], city=self.request_data['city'])

        response = self.client.post(self.url, self.request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['general_errors'], ['This school is already registered.'])

    def test_registered_school_unit_create_success(self):
        self.client.login(username=self.admin_user.username, password='passwd')
        expected_fields = ['id', 'is_active', 'categories', 'address', 'phone_number', 'email',
                           'school_principal', 'district', 'city', 'name', 'academic_profile']

        response = self.client.post(self.url, self.request_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertCountEqual(response.data.keys(), expected_fields)
        self.assertEqual(list(response.data['categories'][0]), ['id', 'name', 'category_level'])
        self.assertEqual(list(response.data['academic_profile']), ['id', 'name'])
        self.assertEqual(list(response.data['school_principal']), ['id', 'full_name'])

        school_unit = RegisteredSchoolUnit.objects.filter(id=response.data['id']).first()
        self.assertIsNotNone(school_unit)
        self.principal.refresh_from_db()
        self.assertEqual(self.principal.school_unit, school_unit)
        self.assertTrue(SchoolUnitStats.objects.filter(school_unit=school_unit, academic_year=self.calendar.academic_year).exists())
        self.assertTrue(StudentAtRiskCounts.objects.filter(school_unit=school_unit).exists())

    def test_registered_school_unit_create_no_academic_profile(self):
        self.client.login(username=self.admin_user.username, password='passwd')

        del self.request_data['academic_profile']
        response = self.client.post(self.url, self.request_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(response.data['academic_profile'])

    def test_registered_school_unit_create_updates_enrollment_stats(self):
        self.client.login(username=self.admin_user.username, password='passwd')
        today = timezone.now().date()
        stats = SchoolUnitEnrollmentStatsFactory(year=today.year, month=today.month, daily_statistics=[{
            'day': today.day, 'weekday': WEEKDAYS_MAP[today.weekday()], 'count': 0
        }])
        response = self.client.post(self.url, self.request_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        stats.refresh_from_db()
        self.assertEqual(len(stats.daily_statistics), 1)
        self.assertEqual(stats.daily_statistics[0]['count'], 1)
        self.assertEqual(stats.daily_statistics[0]['day'], today.day)
        self.assertEqual(stats.daily_statistics[0]['weekday'], WEEKDAYS_MAP[today.weekday()])

        self.request_data['name'] = 'Other'
        self.request_data['school_principal'] = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL).id
        response = self.client.post(self.url, self.request_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        stats.refresh_from_db()
        self.assertEqual(len(stats.daily_statistics), 1)
        self.assertEqual(stats.daily_statistics[0]['count'], 2)
