from ddt import ddt, data
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from edualert.academic_calendars.factories import AcademicYearCalendarFactory
from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.study_classes.factories import StudyClassFactory, TeacherClassThroughFactory
from edualert.subjects.factories import SubjectFactory


@ddt
class UserProfileListTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        AcademicYearCalendarFactory()

        # Administrators
        cls.admin1 = UserProfileFactory(user_role=UserProfile.UserRoles.ADMINISTRATOR, full_name='B name')
        cls.admin2 = UserProfileFactory(user_role=UserProfile.UserRoles.ADMINISTRATOR, full_name='B name',
                                        is_active=False)
        cls.admin3 = UserProfileFactory(user_role=UserProfile.UserRoles.ADMINISTRATOR, full_name='D name',
                                        last_online=timezone.now())

        # School principals
        cls.principal1 = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL, full_name='C name',
                                            last_online=timezone.now())
        cls.school_unit1 = RegisteredSchoolUnitFactory(school_principal=cls.principal1)
        cls.principal2 = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL, full_name='A name',
                                            is_active=False)
        cls.school_unit2 = RegisteredSchoolUnitFactory(school_principal=cls.principal2)
        cls.principal3 = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL, full_name='A name')

        # Teachers
        cls.teacher1 = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, full_name='C name',
                                          last_online=timezone.now(), school_unit=cls.school_unit1)
        cls.teacher2 = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, full_name='C name',
                                          is_active=False, school_unit=cls.school_unit1)
        UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, full_name='name', school_unit=cls.school_unit2)

        # Parents
        cls.parent1 = UserProfileFactory(user_role=UserProfile.UserRoles.PARENT, full_name='B name',
                                         school_unit=cls.school_unit1)
        cls.parent2 = UserProfileFactory(user_role=UserProfile.UserRoles.PARENT, full_name='A name',
                                         is_active=False, school_unit=cls.school_unit1)
        UserProfileFactory(user_role=UserProfile.UserRoles.PARENT, full_name='name', school_unit=cls.school_unit2)

        # Students
        cls.student1 = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, full_name='A name',
                                          school_unit=cls.school_unit1)
        cls.student2 = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, full_name='B name',
                                          is_active=False, school_unit=cls.school_unit1)
        UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, full_name='name', school_unit=cls.school_unit2)

        cls.url = reverse('users:user-profile-list')
        cls.expected_fields = ['id', 'full_name', 'user_role', 'is_active', 'last_online',
                               'labels', 'risk_description', 'school_unit', 'assigned_study_classes']

    def test_user_profile_list_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.TEACHER,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_user_profile_list_wrong_user_type(self, user_role):
        profile = UserProfileFactory(user_role=user_role, school_unit=self.school_unit1)
        self.client.login(username=profile.username, password='passwd')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_profile_list_admin(self):
        self.client.login(username=self.admin1.username, password='passwd')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 5)
        results = response.data['results']
        for profile in results:
            self.assertCountEqual(profile.keys(), self.expected_fields)

        self.assertEqual(results[0]['id'], self.principal1.id)
        self.assertCountEqual(results[0]['school_unit'].keys(), ['id', 'name'])
        self.assertEqual(results[0]['school_unit']['id'], self.school_unit1.id)
        self.assertEqual(results[0]['assigned_study_classes'], [])
        self.assertEqual(results[1]['id'], self.admin3.id)
        self.assertIsNone(results[1]['school_unit'])
        self.assertEqual(results[2]['id'], self.principal3.id)
        self.assertIsNone(results[2]['school_unit'])
        self.assertEqual(results[3]['id'], self.principal2.id)
        self.assertEqual(results[3]['school_unit']['id'], self.school_unit2.id)
        self.assertEqual(results[4]['id'], self.admin2.id)
        self.assertIsNone(results[4]['school_unit'])

        # Search
        response = self.client.get(self.url, {'search': 'B'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        results = response.data['results']
        self.assertEqual(results[0]['id'], self.admin2.id)

        # Filter by user role
        response = self.client.get(self.url, {'user_role': UserProfile.UserRoles.ADMINISTRATOR})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        results = response.data['results']
        self.assertEqual(results[0]['id'], self.admin3.id)
        self.assertEqual(results[1]['id'], self.admin2.id)

        # Filter by is_active
        response = self.client.get(self.url, {'is_active': 'false'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        results = response.data['results']
        self.assertEqual(results[0]['id'], self.principal2.id)
        self.assertEqual(results[1]['id'], self.admin2.id)

    def test_user_profile_list_principal(self):
        self.client.login(username=self.principal1.username, password='passwd')

        study_class1 = StudyClassFactory(school_unit=self.school_unit1, class_master=self.teacher2, class_grade='IX', class_grade_arabic=9)
        teacher_class_through1 = TeacherClassThroughFactory(study_class=study_class1, teacher=self.teacher2, is_class_master=True,
                                                            subject=SubjectFactory(name='A subject'))
        teacher_class_through2 = TeacherClassThroughFactory(study_class=study_class1, teacher=self.teacher2, is_class_master=True,
                                                            subject=SubjectFactory(name='Dirigentie', is_coordination=True))
        study_class2 = StudyClassFactory(school_unit=self.school_unit1, class_master=self.teacher1)
        teacher_class_through3 = TeacherClassThroughFactory(study_class=study_class2, teacher=self.teacher2)
        study_class3 = StudyClassFactory(school_unit=self.school_unit1, academic_year=2019, class_master=self.teacher1)
        TeacherClassThroughFactory(study_class=study_class3, teacher=self.teacher2)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 6)
        results = response.data['results']
        for profile in results:
            self.assertCountEqual(profile.keys(), self.expected_fields)

        self.assertEqual(results[0]['id'], self.teacher1.id)
        self.assertEqual(results[0]['assigned_study_classes'], [])
        self.assertEqual(results[1]['id'], self.student1.id)
        self.assertEqual(results[1]['assigned_study_classes'], [])
        self.assertEqual(results[2]['id'], self.parent1.id)
        self.assertEqual(results[2]['assigned_study_classes'], [])
        self.assertEqual(results[3]['id'], self.parent2.id)
        self.assertEqual(results[3]['assigned_study_classes'], [])
        self.assertEqual(results[4]['id'], self.student2.id)
        self.assertEqual(results[4]['assigned_study_classes'], [])
        self.assertEqual(results[5]['id'], self.teacher2.id)
        self.assertEqual(len(results[5]['assigned_study_classes']), 3)
        self.assertCountEqual(results[5]['assigned_study_classes'][0].keys(), ['id', 'study_class_id', 'class_grade', 'class_letter',
                                                                               'subject_id', 'subject_name', 'is_optional_subject'])
        self.assertEqual(results[5]['assigned_study_classes'][0]['id'], teacher_class_through3.id)
        self.assertEqual(results[5]['assigned_study_classes'][1]['id'], teacher_class_through1.id)
        self.assertEqual(results[5]['assigned_study_classes'][2]['id'], teacher_class_through2.id)

        # Search
        response = self.client.get(self.url, {'search': 'C'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        results = response.data['results']
        self.assertEqual(results[0]['id'], self.teacher1.id)
        self.assertEqual(results[1]['id'], self.teacher2.id)

        # Filter by user role
        response = self.client.get(self.url, {'user_role': UserProfile.UserRoles.PARENT})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        results = response.data['results']
        self.assertEqual(results[0]['id'], self.parent1.id)
        self.assertEqual(results[1]['id'], self.parent2.id)

        # Filter by is_active
        response = self.client.get(self.url, {'is_active': 'true'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
        results = response.data['results']
        self.assertEqual(results[0]['id'], self.teacher1.id)
        self.assertEqual(results[1]['id'], self.student1.id)
        self.assertEqual(results[2]['id'], self.parent1.id)
