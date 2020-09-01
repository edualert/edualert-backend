from ddt import data, ddt
from django.urls import reverse
from rest_framework import status

from edualert.catalogs.factories import StudentCatalogPerYearFactory
from edualert.catalogs.models import StudentCatalogPerYear
from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.study_classes.factories import StudyClassFactory, TeacherClassThroughFactory


@ddt
class OwnStudyClassPupilListTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.school_unit = RegisteredSchoolUnitFactory()
        cls.teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=cls.school_unit)
        cls.study_class = StudyClassFactory(school_unit=cls.school_unit, class_master=cls.teacher)
        cls.teacher_class_through = TeacherClassThroughFactory(
            study_class=cls.study_class,
            teacher=cls.teacher,
            is_class_master=True,
        )
        cls.catalog1 = StudentCatalogPerYearFactory(
            student=UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, full_name='a'),
            study_class=cls.study_class,
            academic_year=2020,
            avg_sem1=1,
            avg_sem2=1,
            avg_final=1,
            abs_count_sem1=1,
            abs_count_sem2=1,
            abs_count_annual=1
        )
        cls.catalog2 = StudentCatalogPerYearFactory(
            student=UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, full_name='b'),
            study_class=cls.study_class,
            academic_year=2020,
            avg_sem1=2,
            avg_sem2=2,
            avg_final=2,
            abs_count_sem1=2,
            abs_count_sem2=2,
            abs_count_annual=2
        )
        cls.catalog3 = StudentCatalogPerYearFactory(
            student=UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, full_name='c'),
            study_class=cls.study_class,
            academic_year=2020,
            avg_sem1=3,
            avg_sem2=3,
            avg_final=3,
            abs_count_sem1=3,
            abs_count_sem2=3,
            abs_count_annual=3
        )
        cls.catalog4 = StudentCatalogPerYearFactory(
            student=UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, full_name='d'),
            study_class=cls.study_class,
            academic_year=2020,
            avg_sem1=4,
            avg_sem2=4,
            avg_final=4,
            abs_count_sem1=4,
            abs_count_sem2=4,
            abs_count_annual=4
        )

    @staticmethod
    def build_url(study_class_id):
        return reverse('catalogs:own-study-class-pupil-list', kwargs={'id': study_class_id})

    def test_own_study_class_pupil_list_unauthenticated(self):
        response = self.client.get(self.build_url(self.study_class.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.PRINCIPAL,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_own_study_class_pupil_list_wrong_user_type(self, user_role):
        user = UserProfileFactory(
            user_role=user_role,
            school_unit=self.school_unit if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )
        self.client.login(username=user.username, password='passwd')

        response = self.client.get(self.build_url(self.study_class.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_own_study_class_pupil_list_study_class_does_not_exist(self):
        self.client.login(username=self.teacher.username, password='passwd')
        response = self.client.get(self.build_url(0))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_own_study_class_pupil_list_is_not_class_master(self):
        self.client.login(username=self.teacher.username, password='passwd')
        self.study_class.class_master = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER)
        self.study_class.save()
        response = self.client.get(self.build_url(self.study_class.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_own_study_class_pupil_list_success(self):
        self.client.login(username=self.teacher.username, password='passwd')
        response = self.client.get(self.build_url(self.study_class.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

        catalog_expected_fields = [
            'id', 'student', 'avg_sem1', 'avg_sem2', 'avg_annual', 'avg_final', 'abs_count_sem1', 'abs_count_sem2',
            'abs_count_annual', 'founded_abs_count_sem1', 'founded_abs_count_sem2', 'founded_abs_count_annual', 'unfounded_abs_count_sem1',
            'unfounded_abs_count_sem2', 'unfounded_abs_count_annual'
        ]
        student_expected_fields = ['id', 'full_name', 'labels', 'risk_description']
        label_expected_fields = ['id', 'text']
        for catalog_data in response.data:
            self.assertCountEqual(catalog_data.keys(), catalog_expected_fields)
            self.assertCountEqual(catalog_data['student'].keys(), student_expected_fields)
            for label_data in catalog_data['student']['labels']:
                self.assertCountEqual(label_data.keys(), label_expected_fields)

    @data(
        None, 'student_name', 'avg_sem1', 'avg_sem2', 'avg_final', 'abs_count_sem1', 'abs_count_sem2', 'abs_count_annual',
        '-student_name', '-avg_sem1', '-avg_sem2', '-avg_final', '-abs_count_sem1', '-abs_count_sem2', '-abs_count_annual'
    )
    def test_own_study_class_pupil_list_ordering(self, order_by):
        # Default ordering should be by student's name ASC
        self.client.login(username=self.teacher.username, password='passwd')
        response = self.client.get(self.build_url(self.study_class.id), {'ordering': order_by} if order_by else None)

        if not order_by or order_by == 'student_name':
            order_by = 'student__full_name'

        if order_by == '-student_name':
            order_by = '-student__full_name'

        for catalog_data, catalog in zip(response.data, StudentCatalogPerYear.objects.order_by(order_by)):
            self.assertEqual(catalog_data['id'], catalog.id)
