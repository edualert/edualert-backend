import datetime
from unittest.mock import patch

from ddt import data, ddt
from pytz import utc
from django.urls import reverse
from rest_framework import status

from edualert.academic_calendars.factories import AcademicYearCalendarFactory
from edualert.catalogs.factories import StudentCatalogPerYearFactory
from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.study_classes.factories import StudyClassFactory


@ddt
class OwnStudentsAveragesTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.calendar = AcademicYearCalendarFactory()
        cls.school_unit = RegisteredSchoolUnitFactory()
        cls.teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=cls.school_unit)
        cls.study_class = StudyClassFactory(school_unit=cls.school_unit, class_master=cls.teacher)

        cls.expected_fields = ['id', 'student', 'avg_sem1', 'avg_final']
        cls.student_expected_fields = ['id', 'full_name']

        cls.url = reverse('statistics:own-students-averages')

    def test_own_students_averages_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.PRINCIPAL,
        UserProfile.UserRoles.PARENT,
        UserProfile.UserRoles.STUDENT
    )
    def test_own_students_averages_wrong_user_type(self, user_role):
        user = UserProfileFactory(
            user_role=user_role,
            school_unit=self.school_unit if UserProfile.UserRoles != UserProfile.UserRoles.ADMINISTRATOR else None
        )
        self.client.login(username=user.username, password='passwd')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_own_students_averages_is_not_class_master(self):
        self.client.login(username=self.teacher.username, password='passwd')
        self.study_class.academic_year = 2000
        self.study_class.save()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('django.utils.timezone.now', return_value=datetime.datetime(2019, 12, 10).replace(tzinfo=utc))
    def test_own_students_averages_first_semester(self, mocked_method):
        self.client.login(username=self.teacher.username, password='passwd')

        catalog1 = StudentCatalogPerYearFactory(student=UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=self.school_unit, student_in_class=self.study_class),
                                                study_class=self.study_class, avg_sem1=9, avg_final=8)
        catalog2 = StudentCatalogPerYearFactory(student=UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=self.school_unit, student_in_class=self.study_class),
                                                study_class=self.study_class, avg_sem1=None, avg_final=None)
        catalog3 = StudentCatalogPerYearFactory(student=UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=self.school_unit, student_in_class=self.study_class),
                                                study_class=self.study_class, avg_sem1=8, avg_final=9)

        response = self.client.get(self.url)
        self.assertEqual(len(response.data['results']), 3)
        for catalog in response.data['results']:
            self.assertCountEqual(catalog.keys(), self.expected_fields)
            self.assertCountEqual(catalog['student'].keys(), self.student_expected_fields)

        self.assertEqual(response.data['results'][0]['id'], catalog1.id)
        self.assertEqual(response.data['results'][1]['id'], catalog3.id)
        self.assertEqual(response.data['results'][2]['id'], catalog2.id)

    @patch('django.utils.timezone.now', return_value=datetime.datetime(2020, 8, 8).replace(tzinfo=utc))
    def test_own_students_averages_second_semester(self, mocked_method):
        self.client.login(username=self.teacher.username, password='passwd')

        catalog1 = StudentCatalogPerYearFactory(student=UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=self.school_unit, student_in_class=self.study_class),
                                                study_class=self.study_class, avg_sem1=9, avg_final=8)
        catalog2 = StudentCatalogPerYearFactory(student=UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=self.school_unit, student_in_class=self.study_class),
                                                study_class=self.study_class, avg_sem1=8, avg_final=9)

        response = self.client.get(self.url)
        self.assertEqual(len(response.data['results']), 2)
        for catalog in response.data['results']:
            self.assertCountEqual(catalog.keys(), self.expected_fields)
            self.assertCountEqual(catalog['student'].keys(), self.student_expected_fields)

        self.assertEqual(response.data['results'][0]['id'], catalog2.id)
        self.assertEqual(response.data['results'][1]['id'], catalog1.id)
