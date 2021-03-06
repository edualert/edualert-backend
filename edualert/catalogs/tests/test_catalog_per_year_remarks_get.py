from ddt import ddt, data
from django.urls import reverse
from rest_framework import status

from edualert.catalogs.factories import StudentCatalogPerYearFactory
from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.study_classes.factories import StudyClassFactory, TeacherClassThroughFactory
from edualert.subjects.factories import SubjectFactory


@ddt
class CatalogPerYearRemarksGetTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.school_unit = RegisteredSchoolUnitFactory()
        cls.teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=cls.school_unit)
        cls.student = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=cls.school_unit)
        cls.study_class = StudyClassFactory(school_unit=cls.school_unit, class_master=cls.teacher)
        cls.subject = SubjectFactory()
        cls.teacher.taught_subjects.add(cls.subject)
        cls.teacher_class_through = TeacherClassThroughFactory(
            study_class=cls.study_class,
            teacher=cls.teacher,
            subject=cls.subject,
        )
        cls.catalog = StudentCatalogPerYearFactory(
            student=UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, full_name='a'),
            study_class=cls.study_class,
            academic_year=2020
        )

    def setUp(self):
        self.catalog.refresh_from_db()

    @staticmethod
    def build_url(catalog_id):
        return reverse('catalogs:catalog-per-year-remarks', kwargs={'id': catalog_id})

    def test_catalogs_per_year_remarks_get_unauthenticated(self):
        response = self.client.get(self.build_url(self.catalog.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.PRINCIPAL,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_catalogs_per_year_remarks_get_wrong_user_type(self, user_role):
        user = UserProfileFactory(
            user_role=user_role,
            school_unit=self.school_unit if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )
        self.client.login(username=user.username, password='passwd')

        response = self.client.get(self.build_url(self.catalog.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_catalogs_per_year_remarks_get_catalog_does_not_exist(self):
        self.client.login(username=self.teacher.username, password='passwd')
        response = self.client.get(self.build_url(0))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_catalogs_per_year_remarks_is_not_class_master(self):
        self.client.login(username=self.teacher.username, password='passwd')
        self.study_class.class_master = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER)
        self.study_class.save()
        response = self.client.get(self.build_url(self.catalog.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_catalogs_per_year_remarks_success(self):
        self.client.login(username=self.teacher.username, password='passwd')
        self.catalog.remarks = 'remarks'
        self.catalog.save()
        response = self.client.get(self.build_url(self.catalog.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(response.data.keys(), ['remarks'])
        self.assertEqual(response.data['remarks'], self.catalog.remarks)
