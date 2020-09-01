from ddt import data, ddt, unpack
from django.urls import reverse
from rest_framework import status

from edualert.catalogs.factories import StudentCatalogPerYearFactory
from edualert.catalogs.models import StudentCatalogPerYear
from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory, LabelFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory, SchoolUnitProfileFactory
from edualert.study_classes.factories import StudyClassFactory, TeacherClassThroughFactory


@ddt
class PupilsStatisticsTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = UserProfileFactory(user_role=UserProfile.UserRoles.ADMINISTRATOR)
        cls.principal = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL)
        cls.school_unit = RegisteredSchoolUnitFactory(school_principal=cls.principal)

        cls.teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=cls.school_unit)
        cls.study_class = StudyClassFactory(school_unit=cls.school_unit)
        cls.teacher_class_through = TeacherClassThroughFactory(
            study_class=cls.study_class,
            teacher=cls.teacher
        )
        another_study_class = StudyClassFactory(school_unit=cls.school_unit, class_grade='IX', class_grade_arabic=9)

        cls.another_school_unit = RegisteredSchoolUnitFactory(academic_profile=SchoolUnitProfileFactory(name='Militar'))
        cls.catalog1 = StudentCatalogPerYearFactory(
            student=UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, full_name='Student a', school_unit=cls.another_school_unit),
            study_class=StudyClassFactory(school_unit=cls.another_school_unit),
            avg_sem1=1,
            avg_sem2=1,
            avg_final=1,
            second_examinations_count=1,
            unfounded_abs_count_sem1=1,
            unfounded_abs_count_sem2=1,
            unfounded_abs_count_annual=1,
            behavior_grade_sem1=1,
            behavior_grade_sem2=1,
            behavior_grade_annual=1,
        )
        cls.catalog2 = StudentCatalogPerYearFactory(
            student=UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, full_name='Student b', school_unit=cls.school_unit),
            study_class=another_study_class,
            avg_sem1=2,
            avg_sem2=2,
            avg_final=2,
            second_examinations_count=2,
            unfounded_abs_count_sem1=2,
            unfounded_abs_count_sem2=2,
            unfounded_abs_count_annual=2,
            behavior_grade_sem1=2,
            behavior_grade_sem2=2,
            behavior_grade_annual=2,
        )
        cls.catalog3 = StudentCatalogPerYearFactory(
            student=UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, full_name='Student c', school_unit=cls.school_unit),
            study_class=cls.study_class,
            avg_sem1=3,
            avg_sem2=3,
            avg_final=3,
            second_examinations_count=3,
            unfounded_abs_count_sem1=3,
            unfounded_abs_count_sem2=3,
            unfounded_abs_count_annual=3,
            behavior_grade_sem1=3,
            behavior_grade_sem2=3,
            behavior_grade_annual=3,
        )
        cls.catalog4 = StudentCatalogPerYearFactory(
            student=UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, full_name='Student d', school_unit=cls.school_unit),
            study_class=cls.study_class,
            avg_sem1=4,
            avg_sem2=4,
            avg_final=4,
            second_examinations_count=4,
            unfounded_abs_count_sem1=4,
            unfounded_abs_count_sem2=4,
            unfounded_abs_count_annual=4,
            behavior_grade_sem1=4,
            behavior_grade_sem2=4,
            behavior_grade_annual=4,
        )

        cls.url = reverse('statistics:pupils-statistics')

    def test_pupils_statistics_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_pupils_statistics_wrong_user_type(self, user_role):
        user = UserProfileFactory(user_role=user_role, school_unit=self.school_unit)
        self.client.login(username=user.username, password='passwd')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_pupils_statistics_admin_success(self):
        self.client.login(username=self.admin.username, password='passwd')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 4)

        catalog_expected_fields = [
            'id', 'student', 'school_unit', 'avg_sem1', 'avg_sem2', 'avg_final', 'second_examinations_count',
            'unfounded_abs_count_sem1', 'unfounded_abs_count_sem2', 'unfounded_abs_count_annual',
            'behavior_grade_sem1', 'behavior_grade_sem2', 'behavior_grade_annual', 'behavior_grade_limit',
            'labels', 'risk_description', 'student_in_class', 'academic_program_name'
        ]
        school_unit_expected_fields = ['id', 'name']
        label_expected_fields = ['id', 'text']
        study_class_expected_fields = ['id', 'class_grade', 'class_letter']
        for catalog_data in response.data['results']:
            self.assertCountEqual(catalog_data.keys(), catalog_expected_fields)
            self.assertCountEqual(catalog_data['school_unit'].keys(), school_unit_expected_fields)
            self.assertCountEqual(catalog_data['student_in_class'].keys(), study_class_expected_fields)
            for label_data in catalog_data['labels']:
                self.assertCountEqual(label_data.keys(), label_expected_fields)

        # Search
        student = self.catalog2.student
        student.labels.add(LabelFactory(text='Label 1'))

        response = self.client.get(self.url, {'search': 'Label 1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.catalog2.id)
        self.assertEqual(response.data['results'][0]['behavior_grade_limit'], 6)

        response = self.client.get(self.url, {'search': self.another_school_unit.name})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.catalog1.id)
        self.assertEqual(response.data['results'][0]['behavior_grade_limit'], 8)

        # Filters
        response = self.client.get(self.url, {'academic_program': self.study_class.academic_program.generic_academic_program.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(response.data['results'][0]['id'], self.catalog3.id)
        self.assertEqual(response.data['results'][1]['id'], self.catalog4.id)

        response = self.client.get(self.url, {'study_class_grade': 'IX'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.catalog2.id)

        catalog = StudentCatalogPerYearFactory(academic_year=2018, student=UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT,
                                                                                              school_unit=self.school_unit))
        response = self.client.get(self.url, {'academic_year': '2018'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], catalog.id)

    @data(
        ('principal', 3),
        ('teacher', 2)
    )
    @unpack
    def test_pupils_statistics_school_employee_success(self, profile_param, results_count):
        self.client.login(username=getattr(self, profile_param).username, password='passwd')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], results_count)

        catalog_expected_fields = [
            'id', 'student', 'avg_sem1', 'avg_sem2', 'avg_final', 'second_examinations_count',
            'unfounded_abs_count_sem1', 'unfounded_abs_count_sem2', 'unfounded_abs_count_annual',
            'behavior_grade_sem1', 'behavior_grade_sem2', 'behavior_grade_annual', 'behavior_grade_limit',
            'labels', 'risk_description', 'student_in_class', 'academic_program_name'
        ]
        student_expected_fields = ['id', 'full_name']
        label_expected_fields = ['id', 'text']
        study_class_expected_fields = ['id', 'class_grade', 'class_letter']
        for catalog_data in response.data['results']:
            self.assertCountEqual(catalog_data.keys(), catalog_expected_fields)
            self.assertCountEqual(catalog_data['student'].keys(), student_expected_fields)
            self.assertCountEqual(catalog_data['student_in_class'].keys(), study_class_expected_fields)
            for label_data in catalog_data['labels']:
                self.assertCountEqual(label_data.keys(), label_expected_fields)

        # Search
        response = self.client.get(self.url, {'search': 'Student d'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.catalog4.id)

        student = self.catalog3.student
        student.labels.add(LabelFactory(text='Label 1'))
        response = self.client.get(self.url, {'search': 'Label 1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.catalog3.id)

        # Filters
        response = self.client.get(self.url, {'academic_program': self.study_class.academic_program.generic_academic_program.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(response.data['results'][0]['id'], self.catalog3.id)
        self.assertEqual(response.data['results'][1]['id'], self.catalog4.id)

        response = self.client.get(self.url, {'study_class_grade': 'VI'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(response.data['results'][0]['id'], self.catalog3.id)
        self.assertEqual(response.data['results'][1]['id'], self.catalog4.id)

        response = self.client.get(self.url, {'academic_year': '2018'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    @data(
        None, 'avg_sem1', 'avg_sem2', 'avg_final', 'unfounded_abs_count_sem1',
        'unfounded_abs_count_sem2', 'unfounded_abs_count_annual', 'second_examinations_count',
        'behavior_grade_sem1', 'behavior_grade_sem2', 'behavior_grade_annual',
        '-avg_sem1', '-avg_sem2', '-avg_final', '-unfounded_abs_count_sem1',
        '-unfounded_abs_count_sem2', '-unfounded_abs_count_annual', '-second_examinations_count',
        '-behavior_grade_sem1', '-behavior_grade_sem2', '-behavior_grade_annual',
    )
    def test_pupils_statistics_admin_ordering(self, order_by):
        # Default ordering should be by student's id ASC
        self.client.login(username=self.admin.username, password='passwd')
        response = self.client.get(self.url, {'ordering': order_by} if order_by else None)

        if not order_by:
            order_by = 'student__id'

        for catalog_data, catalog in zip(response.data['results'], StudentCatalogPerYear.objects.order_by(order_by)):
            self.assertEqual(catalog_data['id'], catalog.id)

    @data(
        None, 'student_name', 'avg_sem1', 'avg_sem2', 'avg_final', 'unfounded_abs_count_sem1',
        'unfounded_abs_count_sem2', 'unfounded_abs_count_annual', 'second_examinations_count',
        'behavior_grade_sem1', 'behavior_grade_sem2', 'behavior_grade_annual',
        '-student_name', '-avg_sem1', '-avg_sem2', '-avg_final', '-unfounded_abs_count_sem1',
        '-unfounded_abs_count_sem2', '-unfounded_abs_count_annual', '-second_examinations_count',
        '-behavior_grade_sem1', '-behavior_grade_sem2', '-behavior_grade_annual',
    )
    def test_pupils_statistics_principal_ordering(self, order_by):
        # Default ordering should be by student's name ASC
        self.client.login(username=self.principal.username, password='passwd')
        response = self.client.get(self.url, {'ordering': order_by} if order_by else None)

        if not order_by or order_by == 'student_name':
            order_by = 'student__full_name'

        if order_by == '-student_name':
            order_by = '-student__full_name'

        for catalog_data, catalog in zip(response.data['results'], StudentCatalogPerYear.objects
                .filter(id__in=[self.catalog2.id, self.catalog3.id, self.catalog4.id]).order_by(order_by)):
            self.assertEqual(catalog_data['id'], catalog.id)
