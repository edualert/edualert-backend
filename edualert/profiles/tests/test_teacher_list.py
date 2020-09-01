from ddt import ddt, data
from django.urls import reverse
from rest_framework import status

from edualert.academic_calendars.factories import AcademicYearCalendarFactory
from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.study_classes.factories import StudyClassFactory


@ddt
class TeacherListTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        AcademicYearCalendarFactory()
        cls.principal = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL, full_name='School Principal')
        cls.school_unit = RegisteredSchoolUnitFactory(school_principal=cls.principal)
        cls.url = reverse('users:teacher-list')

    def test_teacher_list_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.TEACHER,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_teacher_list_wrong_user_type(self, user_role):
        profile = UserProfileFactory(
            user_role=user_role,
            school_unit=self.school_unit if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )
        self.client.login(username=profile.username, password='passwd')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_teacher_list_success(self):
        self.client.login(username=self.principal.username, password='passwd')

        teacher1 = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, full_name='John Doe', school_unit=self.school_unit)
        teacher2 = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, full_name='Another teacher', school_unit=self.school_unit)
        teacher3 = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, full_name='Jane Doe', school_unit=self.school_unit)
        UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, is_active=False, school_unit=self.school_unit)
        UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=RegisteredSchoolUnitFactory())

        StudyClassFactory(class_master=teacher3)
        StudyClassFactory(class_master=teacher1, academic_year=2018)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([teacher2.id, teacher3.id, teacher1.id], [teacher['id'] for teacher in response.data])

        expected_fields = ['id', 'full_name', 'taught_subjects']
        for teacher in response.data:
            self.assertCountEqual(teacher.keys(), expected_fields)

        response = self.client.get(self.url, {'search': 'Jane'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([teacher3.id, ], [teacher['id'] for teacher in response.data])

        response = self.client.get(self.url, {'is_class_master': 'false'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([teacher2.id, teacher1.id], [teacher['id'] for teacher in response.data])

        response = self.client.get(self.url, {'is_class_master': 'false', 'search': 'Jane'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
