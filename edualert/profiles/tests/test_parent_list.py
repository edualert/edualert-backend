from ddt import data, ddt
from django.urls import reverse
from rest_framework import status

from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.study_classes.factories import TeacherClassThroughFactory


@ddt
class ParentListTestCase(CommonAPITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.principal = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL)
        cls.school_unit = RegisteredSchoolUnitFactory(school_principal=cls.principal)

        cls.teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=cls.school_unit)
        cls.teacher_class_through = TeacherClassThroughFactory(teacher=cls.teacher)

        cls.parent1 = UserProfileFactory(user_role=UserProfile.UserRoles.PARENT, full_name='mom', school_unit=cls.school_unit)
        cls.parent2 = UserProfileFactory(user_role=UserProfile.UserRoles.PARENT, full_name='dad', school_unit=cls.school_unit)
        cls.parent3 = UserProfileFactory(user_role=UserProfile.UserRoles.PARENT, full_name='other', school_unit=cls.school_unit)
        cls.parent4 = UserProfileFactory(user_role=UserProfile.UserRoles.PARENT, full_name='other2')
        cls.parent5 = UserProfileFactory(user_role=UserProfile.UserRoles.PARENT, full_name='other3', is_active=False)
        cls.child1 = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, full_name='student', school_unit=cls.school_unit,
                                        student_in_class=cls.teacher_class_through.study_class)
        cls.child1.parents.add(cls.parent1, cls.parent2)

        cls.url = reverse('users:parent-list')
        cls.expected_fields = ['id', 'full_name']

    def test_parent_list_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_parent_list_wrong_user_type(self, user_role):
        profile = UserProfileFactory(
            user_role=user_role,
            school_unit=self.school_unit if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )
        self.client.login(username=profile.username, password='passwd')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        profile.delete()

    def test_parent_list_teacher(self):
        self.client.login(username=self.teacher.username, password='passwd')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['id'], self.parent2.id)
        self.assertEqual(results[1]['id'], self.parent1.id)

        for parent in results:
            self.assertCountEqual(parent.keys(), self.expected_fields)

    def test_parent_list_teacher_search(self):
        self.client.login(username=self.teacher.username, password='passwd')

        response = self.client.get(self.url, {'search': 'other'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        response = self.client.get(self.url, {'search': 'dad'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['full_name'], 'dad')

    def test_parent_list_principal(self):
        self.client.login(username=self.principal.username, password='passwd')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]['id'], self.parent2.id)
        self.assertEqual(results[1]['id'], self.parent1.id)
        self.assertEqual(results[2]['id'], self.parent3.id)

        for parent in results:
            self.assertCountEqual(parent.keys(), self.expected_fields)

    def test_parent_list_principal_search(self):
        self.client.login(username=self.principal.username, password='passwd')

        response = self.client.get(self.url, {'search': 'inexistent'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        response = self.client.get(self.url, {'search': 'mom'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['full_name'], 'mom')
