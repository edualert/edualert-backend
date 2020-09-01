from ddt import ddt, data
from django.urls import reverse
from rest_framework import status

from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.study_classes.factories import StudyClassFactory, TeacherClassThroughFactory


@ddt
class StudentListTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.principal = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL)
        cls.school_unit = RegisteredSchoolUnitFactory(school_principal=cls.principal)
        cls.teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=cls.school_unit)
        cls.url = reverse('users:student-list')

    def test_student_list_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_student_list_wrong_user_type(self, user_role):
        profile = UserProfileFactory(
            user_role=user_role,
            school_unit=self.school_unit if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )
        self.client.login(username=profile.username, password='passwd')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_list_principal(self):
        self.client.login(username=self.principal.username, password='passwd')

        student1 = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, full_name='John Doe', school_unit=self.school_unit,
                                      student_in_class=StudyClassFactory(school_unit=self.school_unit))
        student2 = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, full_name='Another student', school_unit=self.school_unit)
        student3 = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, full_name='Jane Doe', school_unit=self.school_unit)
        UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, is_active=False, school_unit=self.school_unit)
        UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=RegisteredSchoolUnitFactory())

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([student2.id, student3.id, student1.id], [student['id'] for student in response.data])

        expected_fields = ['id', 'full_name']
        for student in response.data:
            self.assertCountEqual(student.keys(), expected_fields)

        response = self.client.get(self.url, {'search': 'Jane'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([student3.id, ], [student['id'] for student in response.data])

        response = self.client.get(self.url, {'has_class': 'false'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([student2.id, student3.id], [student['id'] for student in response.data])

        response = self.client.get(self.url, {'has_class': 'false', 'search': 'John'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_student_list_teacher(self):
        self.client.login(username=self.teacher.username, password='passwd')

        study_class = StudyClassFactory(school_unit=self.school_unit)
        TeacherClassThroughFactory(study_class=study_class, teacher=self.teacher)

        student1 = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, full_name='John Doe', school_unit=self.school_unit, student_in_class=study_class)
        student2 = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, full_name='Another student', school_unit=self.school_unit, student_in_class=study_class)
        student3 = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, full_name='Jane Doe', school_unit=self.school_unit, student_in_class=study_class)
        UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=self.school_unit)
        UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, is_active=False, school_unit=self.school_unit)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([student2.id, student3.id, student1.id], [student['id'] for student in response.data])

        expected_fields = ['id', 'full_name']
        for student in response.data:
            self.assertCountEqual(student.keys(), expected_fields)

        response = self.client.get(self.url, {'search': 'Jane'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([student3.id, ], [student['id'] for student in response.data])

        response = self.client.get(self.url, {'has_class': 'false'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        response = self.client.get(self.url, {'has_class': 'false', 'search': 'John'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
