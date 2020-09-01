from ddt import data, ddt
from django.urls import reverse
from rest_framework import status

from edualert.catalogs.factories import StudentCatalogPerSubjectFactory
from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.study_classes.factories import TeacherClassThroughFactory, StudyClassFactory
from edualert.subjects.factories import SubjectFactory


@ddt
class CatalogPerSubjectRemarksGetTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.school_unit = RegisteredSchoolUnitFactory()
        cls.teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=cls.school_unit)
        cls.student = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=cls.school_unit)
        cls.study_class = StudyClassFactory(school_unit=cls.school_unit)
        cls.subject = SubjectFactory()
        cls.teacher.taught_subjects.add(cls.subject)
        cls.teacher_class_through = TeacherClassThroughFactory(
            study_class=cls.study_class,
            teacher=cls.teacher,
            subject=cls.subject
        )
        cls.catalog = StudentCatalogPerSubjectFactory(
            subject=cls.subject,
            teacher=cls.teacher,
            student=UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, full_name='a'),
            study_class=cls.study_class,
            academic_year=2020,
            is_enrolled=True
        )

    def setUp(self):
        self.catalog.refresh_from_db()

    @staticmethod
    def build_url(catalog_id):
        return reverse('catalogs:catalog-per-subject-remarks', kwargs={'id': catalog_id})

    def test_catalogs_per_subject_remarks_get_unauthenticated(self):
        response = self.client.get(self.build_url(self.catalog.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.PRINCIPAL,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_catalogs_per_subject_remarks_get_wrong_user_type(self, user_role):
        user = UserProfileFactory(
            user_role=user_role,
            school_unit=self.school_unit if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )
        self.client.login(username=user.username, password='passwd')

        response = self.client.get(self.build_url(self.catalog.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_catalogs_per_subject_remarks_get_catalog_does_not_exist(self):
        self.client.login(username=self.teacher.username, password='passwd')
        response = self.client.get(self.build_url(0))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_catalogs_per_subject_remarks_get_not_assigned_teacher(self):
        self.client.login(username=self.teacher.username, password='passwd')
        self.catalog.teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER)
        self.catalog.save()
        response = self.client.get(self.build_url(self.catalog.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_catalogs_per_subject_remarks_success(self):
        self.client.login(username=self.teacher.username, password='passwd')
        self.catalog.remarks = 'remarks'
        self.catalog.save()
        response = self.client.get(self.build_url(self.catalog.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(response.data.keys(), ['remarks'])
        self.assertEqual(response.data['remarks'], self.catalog.remarks)
