from ddt import data, ddt
from django.urls import reverse
from rest_framework import status

from edualert.catalogs.factories import StudentCatalogPerSubjectFactory
from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.study_classes.factories import StudyClassFactory, TeacherClassThroughFactory
from edualert.subjects.factories import SubjectFactory


@ddt
class CatalogSettingsTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.school_unit = RegisteredSchoolUnitFactory()
        cls.teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=cls.school_unit)
        cls.study_class = StudyClassFactory(school_unit=cls.school_unit)
        cls.subject = SubjectFactory()
        cls.teacher_class_through = TeacherClassThroughFactory(
            study_class=cls.study_class,
            teacher=cls.teacher,
            subject=cls.subject
        )

    @staticmethod
    def build_url(study_class_id, subject_id):
        return reverse('catalogs:catalog-settings', kwargs={'study_class_id': study_class_id, 'subject_id': subject_id})

    def test_catalog_settings_unauthenticated(self):
        response = self.client.get(self.build_url(self.study_class.id, self.subject.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.PRINCIPAL,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_catalog_settings_wrong_user_type(self, user_role):
        user = UserProfileFactory(
            user_role=user_role,
            school_unit=self.school_unit if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )
        self.client.login(username=user.username, password='passwd')

        response = self.client.get(self.build_url(self.study_class.id, self.subject.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_catalog_settings_study_class_does_not_exist(self):
        self.client.login(username=self.teacher.username, password='passwd')
        response = self.client.get(self.build_url(0, self.subject.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_catalog_settings_subject_does_not_exist(self):
        self.client.login(username=self.teacher.username, password='passwd')
        response = self.client.get(self.build_url(self.study_class.id, 0))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_catalog_settings_not_assigned_teacher(self):
        self.client.login(username=self.teacher.username, password='passwd')
        study_class = StudyClassFactory(school_unit=self.school_unit)

        response = self.client.get(self.build_url(study_class.id, self.subject.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_catalog_settings_not_teaching_subject(self):
        self.client.login(username=self.teacher.username, password='passwd')

        response = self.client.get(self.build_url(self.study_class.id, SubjectFactory().id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_catalog_settings_success(self):
        self.client.login(username=self.teacher.username, password='passwd')
        catalog1 = StudentCatalogPerSubjectFactory(
            subject=self.subject,
            teacher=self.teacher,
            student=UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, full_name='c'),
            study_class=self.study_class
        )

        catalog2 = StudentCatalogPerSubjectFactory(
            subject=self.subject,
            teacher=self.teacher,
            student=UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, full_name='a'),
            study_class=self.study_class
        )

        catalog3 = StudentCatalogPerSubjectFactory(
            subject=self.subject,
            teacher=self.teacher,
            student=UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, full_name='b'),
            study_class=self.study_class
        )
        StudentCatalogPerSubjectFactory(
            subject=self.subject,
            teacher=self.teacher,
            student=UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, full_name='d', is_active=False),
            study_class=self.study_class
        )

        response = self.client.get(self.build_url(self.study_class.id, self.subject.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

        catalog_expected_fields = ['id', 'student', 'wants_level_testing_grade', 'wants_thesis',
                                   'wants_simulation', 'is_exempted', 'is_enrolled']
        student_expected_fields = ['id', 'full_name']

        for catalog_data in response.data:
            self.assertCountEqual(catalog_data.keys(), catalog_expected_fields)
            self.assertCountEqual(catalog_data['student'].keys(), student_expected_fields)

        self.assertEqual(response.data[0]['id'], catalog2.id)
        self.assertEqual(response.data[1]['id'], catalog3.id)
        self.assertEqual(response.data[2]['id'], catalog1.id)
