from datetime import timedelta

from ddt import ddt, data
from django.urls import reverse
from django.utils import timezone
from pytz import utc
from rest_framework import status

from edualert.academic_calendars.factories import AcademicYearCalendarFactory
from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.study_classes.factories import StudyClassFactory


@ddt
class InactiveParentsTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.school = RegisteredSchoolUnitFactory()
        cls.teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=cls.school)
        cls.study_class = StudyClassFactory(school_unit=cls.school, class_master=cls.teacher)
        cls.current_academic_year_calendar = AcademicYearCalendarFactory()
        cls.url = reverse('statistics:inactive-parents')

    def test_inactive_parents_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.PRINCIPAL,
        UserProfile.UserRoles.PARENT,
        UserProfile.UserRoles.STUDENT
    )
    def test_inactive_parents_wrong_user_type(self, user_role):
        school = RegisteredSchoolUnitFactory()
        user = UserProfileFactory(
            user_role=user_role,
            school_unit=school if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )
        self.client.login(username=user.username, password='passwd')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_inactive_parents_is_not_class_master_in_current_year(self):
        self.client.login(username=self.teacher.username, password='passwd')
        self.study_class.academic_year = 2000
        self.study_class.save()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_inactive_parents_teacher_is_not_class_master(self):
        self.client.login(username=self.teacher.username, password='passwd')
        self.study_class.delete()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_inactive_parents_success(self):
        self.client.login(username=self.teacher.username, password='passwd')
        expected_fields = ['id', 'full_name', 'last_online', 'children']
        children_expected_fields = ['id', 'full_name']
        today = timezone.now().replace(tzinfo=utc)
        student = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, student_in_class=self.study_class)
        parent1 = UserProfileFactory(last_online=today - timedelta(days=31), school_unit=self.school, user_role=UserProfile.UserRoles.PARENT)
        student.parents.add(parent1)

        student = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, student_in_class=self.study_class)
        parent2 = UserProfileFactory(last_online=today - timedelta(days=30), school_unit=self.school, user_role=UserProfile.UserRoles.PARENT)
        student.parents.add(parent2)

        student = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, student_in_class=self.study_class)
        parent3 = UserProfileFactory(last_online=today - timedelta(days=15), school_unit=self.school, user_role=UserProfile.UserRoles.PARENT)
        student.parents.add(parent3)

        student = UserProfileFactory(
            user_role=UserProfile.UserRoles.STUDENT,
            student_in_class=StudyClassFactory(school_unit=self.school)
        )
        parent4 = UserProfileFactory(last_online=today - timedelta(days=13), school_unit=self.school, user_role=UserProfile.UserRoles.PARENT)
        student.parents.add(parent4)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        self.assertCountEqual(response.data['results'][0].keys(), expected_fields)

        self.assertEqual(response.data['results'][0]['id'], parent2.id)
        self.assertEqual(response.data['results'][1]['id'], parent1.id)

        for parent in response.data['results']:
            self.assertEqual(len(parent['children']), 1)
            for child in parent['children']:
                self.assertCountEqual(child.keys(), children_expected_fields)
