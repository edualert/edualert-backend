from ddt import data, ddt
from django.urls import reverse
from rest_framework import status

from edualert.academic_calendars.factories import AcademicYearCalendarFactory
from edualert.catalogs.factories import StudentCatalogPerYearFactory
from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory


@ddt
class OwnChildStatisticsTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.school_unit = RegisteredSchoolUnitFactory()
        cls.calendar = AcademicYearCalendarFactory()
        cls.parent = UserProfileFactory(user_role=UserProfile.UserRoles.PARENT, school_unit=cls.school_unit)
        cls.student = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=cls.school_unit)
        cls.student.parents.add(cls.parent)
        cls.catalog = StudentCatalogPerYearFactory(student=cls.student)

    @staticmethod
    def build_url(child_id):
        return reverse('statistics:own-child-statistics', kwargs={'id': child_id})

    def test_own_child_statistics_unauthenticated(self):
        response = self.client.get(self.build_url(self.student.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.PRINCIPAL,
        UserProfile.UserRoles.TEACHER,
        UserProfile.UserRoles.STUDENT
    )
    def test_own_child_statistics_wrong_user_type(self, user_role):
        user = UserProfileFactory(
            user_role=user_role,
            school_unit=self.school_unit if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )
        self.client.login(username=user.username, password='passwd')

        response = self.client.get(self.build_url(self.student.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_own_child_statistics_not_own_child(self):
        self.client.login(username=self.parent.username, password='passwd')
        another_child = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=self.school_unit)
        response = self.client.get(self.build_url(another_child.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_own_child_statistics_success(self):
        self.client.login(username=self.parent.username, password='passwd')
        expected_fields = [
            'behavior_grade_sem1', 'behavior_grade_annual', 'behavior_grade_limit', 'abs_count_sem1',
            'abs_count_annual', 'founded_abs_count_sem1', 'founded_abs_count_annual', 'unfounded_abs_count_sem1', 'unfounded_abs_count_annual',
            'school_place_by_avg_sem1', 'school_place_by_avg_annual', 'class_place_by_abs_sem1', 'class_place_by_abs_annual', 'school_place_by_abs_sem1',
            'school_place_by_abs_annual', 'class_place_by_avg_sem1', 'class_place_by_avg_annual', 'avg_sem1', 'avg_annual'
        ]
        response = self.client.get(self.build_url(self.student.id))
        self.assertCountEqual(response.data.keys(), expected_fields)
