import datetime
from unittest.mock import patch

from ddt import data, ddt
from django.urls import reverse
from pytz import utc
from rest_framework import status

from edualert.academic_calendars.factories import AcademicYearCalendarFactory
from edualert.catalogs.factories import SubjectAbsenceFactory, StudentCatalogPerSubjectFactory
from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory


@ddt
class OwnChildAbsencesEvolutionTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        AcademicYearCalendarFactory()
        cls.school_unit = RegisteredSchoolUnitFactory()
        cls.parent = UserProfileFactory(user_role=UserProfile.UserRoles.PARENT, school_unit=cls.school_unit)
        cls.student = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=cls.school_unit)
        cls.student.parents.add(cls.parent)

    @staticmethod
    def build_url(child_id):
        return reverse('statistics:own-child-absences-evolution', kwargs={'id': child_id})

    def test_own_child_absences_evolution_unauthenticated(self):
        response = self.client.get(self.build_url(self.student.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.PRINCIPAL,
        UserProfile.UserRoles.TEACHER,
        UserProfile.UserRoles.STUDENT
    )
    def test_own_child_absences_evolution_wrong_user_type(self, user_role):
        user = UserProfileFactory(
            user_role=user_role,
            school_unit=self.school_unit if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )
        self.client.login(username=user.username, password='passwd')

        response = self.client.get(self.build_url(self.student.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_own_child_absences_evolution_not_own_child(self):
        self.client.login(username=self.parent.username, password='passwd')
        another_child = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=self.school_unit)
        response = self.client.get(self.build_url(another_child.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('django.utils.timezone.now', return_value=datetime.datetime(2020, 6, 16).replace(tzinfo=utc))
    def test_own_child_absences_evolution_success(self, mocked_method):
        self.client.login(username=self.parent.username, password='passwd')

        catalog1 = StudentCatalogPerSubjectFactory(student=self.student)
        for day in [5, 10]:
            absence = SubjectAbsenceFactory(student=self.student, catalog_per_subject=catalog1, is_founded=True, taken_at=datetime.date(2020, 6, day))
            absence.created = datetime.datetime(2020, 6, day).replace(tzinfo=utc)
            absence.save()
        catalog2 = StudentCatalogPerSubjectFactory(student=self.student)
        for day in [5, 11]:
            absence = SubjectAbsenceFactory(student=self.student, catalog_per_subject=catalog2, is_founded=False, taken_at=datetime.date(2020, 6, day))
            absence.created = datetime.datetime(2020, 6, day).replace(tzinfo=utc)
            absence.save()
        SubjectAbsenceFactory(student=self.student, catalog_per_subject=catalog2, is_founded=True, taken_at=datetime.date(2020, 6, 16))

        response = self.client.get(self.build_url(self.student.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 30)

        self.assertEqual(response.data[4]['day'], 5)
        self.assertEqual(response.data[4]['weekday'], 'Vi')
        self.assertEqual(response.data[4]['total_count'], 2)

        self.assertEqual(response.data[9]['day'], 10)
        self.assertEqual(response.data[9]['weekday'], 'Mi')
        self.assertEqual(response.data[9]['total_count'], 1)

        self.assertEqual(response.data[10]['day'], 11)
        self.assertEqual(response.data[10]['weekday'], 'Jo')
        self.assertEqual(response.data[10]['total_count'], 1)

        response = self.client.get(self.build_url(self.student.id), {'by_category': 'true'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 30)

        self.assertEqual(response.data[4]['day'], 5)
        self.assertEqual(response.data[4]['weekday'], 'Vi')
        self.assertEqual(response.data[4]['founded_count'], 1)
        self.assertEqual(response.data[4]['unfounded_count'], 1)

        self.assertEqual(response.data[9]['day'], 10)
        self.assertEqual(response.data[9]['weekday'], 'Mi')
        self.assertEqual(response.data[9]['founded_count'], 1)
        self.assertEqual(response.data[9]['unfounded_count'], 0)

        self.assertEqual(response.data[10]['day'], 11)
        self.assertEqual(response.data[10]['weekday'], 'Jo')
        self.assertEqual(response.data[10]['founded_count'], 0)
        self.assertEqual(response.data[10]['unfounded_count'], 1)

    @patch('django.utils.timezone.now', return_value=datetime.datetime(2020, 6, 16).replace(tzinfo=utc))
    def test_own_child_absences_evolution_month_filter(self, mocked_method):
        self.client.login(username=self.parent.username, password='passwd')

        catalog1 = StudentCatalogPerSubjectFactory(student=self.student)
        for day in [5, 11]:
            absence = SubjectAbsenceFactory(student=self.student, catalog_per_subject=catalog1, is_founded=True, taken_at=datetime.date(2020, 5, day))
            absence.created = datetime.datetime(2020, 5, day).replace(tzinfo=utc)
            absence.save()
        catalog2 = StudentCatalogPerSubjectFactory(student=self.student)
        for day in [5, 13]:
            absence = SubjectAbsenceFactory(student=self.student, catalog_per_subject=catalog2, is_founded=False, taken_at=datetime.date(2020, 5, day))
            absence.created = datetime.datetime(2020, 5, day).replace(tzinfo=utc)
            absence.save()

        response = self.client.get(self.build_url(self.student.id), {'month': 5})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 31)

        self.assertEqual(response.data[4]['day'], 5)
        self.assertEqual(response.data[4]['weekday'], 'Ma')
        self.assertEqual(response.data[4]['total_count'], 2)

        self.assertEqual(response.data[10]['day'], 11)
        self.assertEqual(response.data[10]['weekday'], 'Lu')
        self.assertEqual(response.data[10]['total_count'], 1)

        self.assertEqual(response.data[12]['day'], 13)
        self.assertEqual(response.data[12]['weekday'], 'Mi')
        self.assertEqual(response.data[12]['total_count'], 1)

        response = self.client.get(self.build_url(self.student.id), {'month': 5, 'by_category': 'true'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 31)

        self.assertEqual(response.data[4]['day'], 5)
        self.assertEqual(response.data[4]['weekday'], 'Ma')
        self.assertEqual(response.data[4]['founded_count'], 1)
        self.assertEqual(response.data[4]['unfounded_count'], 1)

        self.assertEqual(response.data[10]['day'], 11)
        self.assertEqual(response.data[10]['weekday'], 'Lu')
        self.assertEqual(response.data[10]['founded_count'], 1)
        self.assertEqual(response.data[10]['unfounded_count'], 0)

        self.assertEqual(response.data[12]['day'], 13)
        self.assertEqual(response.data[12]['weekday'], 'Mi')
        self.assertEqual(response.data[12]['founded_count'], 0)
        self.assertEqual(response.data[12]['unfounded_count'], 1)
