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
class StudyClassDetailTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.principal = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL)
        cls.school_unit = RegisteredSchoolUnitFactory(school_principal=cls.principal)
        cls.study_class = StudyClassFactory(school_unit=cls.school_unit)

    @staticmethod
    def build_url(study_class_id):
        return reverse('study_classes:study-class-detail', kwargs={'id': study_class_id})

    def test_study_class_detail_unauthenticated(self):
        response = self.client.get(self.build_url(self.study_class.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.TEACHER,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_study_class_detail_wrong_user_type(self, user_role):
        if user_role == UserProfile.UserRoles.ADMINISTRATOR:
            user = UserProfileFactory(user_role=user_role)
        else:
            user = UserProfileFactory(user_role=user_role, school_unit=self.school_unit)
        self.client.login(username=user.username, password='passwd')

        response = self.client.get(self.build_url(self.study_class.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_study_class_detail_not_found(self):
        self.client.login(username=self.principal.username, password='passwd')

        response = self.client.get(self.build_url(0))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_study_class_detail_another_school_unit(self):
        self.client.login(username=self.principal.username, password='passwd')
        study_class2 = StudyClassFactory(class_grade='V', class_grade_arabic=5)

        response = self.client.get(self.build_url(study_class2.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_study_class_detail_success(self):
        self.client.login(username=self.principal.username, password='passwd')
        student1 = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, full_name='Student B', student_in_class=self.study_class)
        StudentCatalogPerYearFactory(student=student1, study_class=self.study_class)
        student2 = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, full_name='Student C', student_in_class=self.study_class)
        StudentCatalogPerYearFactory(student=student2, study_class=self.study_class)
        student3 = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, full_name='Student A', student_in_class=self.study_class)
        StudentCatalogPerYearFactory(student=student3, study_class=self.study_class)

        teacher1 = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER)
        teacher2 = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER)
        teacher3 = self.study_class.class_master
        subject1 = SubjectFactory(name='Subject B')
        subject2 = SubjectFactory(name='Subject C')
        subject3 = SubjectFactory(name='Subject A')
        subject4 = SubjectFactory(name='Dirigentie', is_coordination=True)
        teacher_class_through1 = TeacherClassThroughFactory(study_class=self.study_class, teacher=teacher1, subject=subject1)
        teacher_class_through2 = TeacherClassThroughFactory(study_class=self.study_class, teacher=teacher2, subject=subject2)
        teacher_class_through3 = TeacherClassThroughFactory(study_class=self.study_class, teacher=teacher3, subject=subject3)
        TeacherClassThroughFactory(study_class=self.study_class, teacher=teacher3, subject=subject4)

        response = self.client.get(self.build_url(self.study_class.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertCountEqual(response.data.keys(), ['id', 'class_grade', 'class_letter', 'academic_year', 'academic_program', 'academic_program_name',
                                                     'class_master', 'teachers_class_through', 'students', 'has_previous_catalog_data'])
        self.assertCountEqual(response.data['class_master'].keys(), ['id', 'full_name'])

        teachers_class_through_response = response.data['teachers_class_through']
        self.assertEqual(len(teachers_class_through_response), 3)
        self.assertCountEqual(teachers_class_through_response[0].keys(), ['id', 'teacher', 'subject_id', 'subject_name'])
        self.assertCountEqual(teachers_class_through_response[0]['teacher'].keys(), ['id', 'full_name'])
        self.assertEqual(teachers_class_through_response[0]['id'], teacher_class_through3.id)
        self.assertEqual(teachers_class_through_response[1]['id'], teacher_class_through1.id)
        self.assertEqual(teachers_class_through_response[2]['id'], teacher_class_through2.id)

        students_response = response.data['students']
        self.assertEqual(len(students_response), 3)
        self.assertCountEqual(students_response[0].keys(), ['id', 'full_name'])
        self.assertEqual(students_response[0]['id'], student3.id)
        self.assertEqual(students_response[1]['id'], student1.id)
        self.assertEqual(students_response[2]['id'], student2.id)
