from ddt import data, ddt
from django.urls import reverse
from rest_framework import status

from edualert.academic_calendars.factories import AcademicYearCalendarFactory
from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.study_classes.factories import StudyClassFactory, TeacherClassThroughFactory
from edualert.schools.factories import RegisteredSchoolUnitFactory


@ddt
class StudyClassesAtRiskTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.calendar = AcademicYearCalendarFactory()
        cls.principal = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL)
        cls.school_unit = RegisteredSchoolUnitFactory(school_principal=cls.principal)
        cls.teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=cls.school_unit)

        cls.url = reverse('statistics:study-classes-at-risk')
        cls.expected_fields = ['id', 'class_grade', 'class_letter', 'students_at_risk_count']

    def test_study_classes_at_risk_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.PARENT,
        UserProfile.UserRoles.STUDENT
    )
    def test_study_classes_at_risk_wrong_user_type(self, user_role):
        user = UserProfileFactory(
            user_role=user_role,
            school_unit=self.school_unit if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )
        self.client.login(username=user.username, password='passwd')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_study_classes_at_risk_principal(self):
        self.client.login(username=self.principal.username, password='passwd')

        study_class1 = StudyClassFactory(school_unit=self.school_unit, students_at_risk_count=1)
        study_class2 = StudyClassFactory(school_unit=self.school_unit, students_at_risk_count=3)
        study_class3 = StudyClassFactory(school_unit=self.school_unit, students_at_risk_count=2)
        StudyClassFactory(school_unit=self.school_unit, students_at_risk_count=0)
        StudyClassFactory(students_at_risk_count=2)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)
        for result in response.data['results']:
            self.assertCountEqual(result.keys(), self.expected_fields)
        self.assertEqual(response.data['results'][0]['id'], study_class2.id)
        self.assertEqual(response.data['results'][1]['id'], study_class3.id)
        self.assertEqual(response.data['results'][2]['id'], study_class1.id)

    def test_study_classes_at_risk_teacher(self):
        self.client.login(username=self.teacher.username, password='passwd')

        study_class1 = StudyClassFactory(school_unit=self.school_unit, students_at_risk_count=1)
        study_class2 = StudyClassFactory(school_unit=self.school_unit, students_at_risk_count=2, class_grade='V', class_grade_arabic=5)
        study_class3 = StudyClassFactory(school_unit=self.school_unit, students_at_risk_count=2, class_grade='IX', class_grade_arabic=9)
        study_class4 = StudyClassFactory(school_unit=self.school_unit, students_at_risk_count=0)
        StudyClassFactory(school_unit=self.school_unit, students_at_risk_count=2)

        for study_class in [study_class1, study_class2, study_class3, study_class4]:
            TeacherClassThroughFactory(teacher=self.teacher, study_class=study_class)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)
        for result in response.data['results']:
            self.assertCountEqual(result.keys(), self.expected_fields)
        self.assertEqual(response.data['results'][0]['id'], study_class2.id)
        self.assertEqual(response.data['results'][1]['id'], study_class3.id)
        self.assertEqual(response.data['results'][2]['id'], study_class1.id)
