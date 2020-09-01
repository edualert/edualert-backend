from ddt import ddt, data
from django.urls import reverse
from rest_framework import status

from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.study_classes.factories import StudyClassFactory


@ddt
class StudyClassListTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.principal = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL)
        cls.school_unit = RegisteredSchoolUnitFactory(school_principal=cls.principal)
        cls.url = reverse('study_classes:study-class-list', kwargs={'academic_year': 2020})

    def test_study_class_list_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.TEACHER,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_study_class_list_wrong_user_type(self, user_role):
        if user_role == UserProfile.UserRoles.ADMINISTRATOR:
            user = UserProfileFactory(user_role=user_role)
        else:
            user = UserProfileFactory(user_role=user_role, school_unit=self.school_unit)
        self.client.login(username=user.username, password='passwd')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_study_class_list_success(self):
        self.client.login(username=self.principal.username, password='passwd')

        class1 = StudyClassFactory(class_grade='VII', class_grade_arabic=7, class_letter='A', school_unit=self.school_unit)
        class2 = StudyClassFactory(class_grade='P', class_grade_arabic=0, class_letter='A', school_unit=self.school_unit)
        class3 = StudyClassFactory(class_grade='IX', class_grade_arabic=9, class_letter='B', school_unit=self.school_unit)
        class4 = StudyClassFactory(class_grade='IX', class_grade_arabic=9, class_letter='A', school_unit=self.school_unit)
        # A class from another school unit
        StudyClassFactory()
        # A class from another year
        StudyClassFactory(school_unit=self.school_unit, academic_year=2018)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(list(response.data), ['P', 'VII', 'IX'])

        self.assertEqual(len(response.data['P']), 1)
        self.assertEqual(response.data['P'][0]['id'], class2.id)
        self.assertCountEqual(response.data['P'][0].keys(), ['id', 'class_grade', 'class_letter', 'academic_program_name', 'has_previous_catalog_data'])
        self.assertEqual(len(response.data['VII']), 1)
        self.assertEqual(response.data['VII'][0]['id'], class1.id)
        self.assertEqual(len(response.data['IX']), 2)
        self.assertEqual(response.data['IX'][0]['id'], class4.id)
        self.assertEqual(response.data['IX'][1]['id'], class3.id)
