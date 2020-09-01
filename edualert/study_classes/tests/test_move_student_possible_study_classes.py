from ddt import data, ddt
from django.urls import reverse
from rest_framework import status

from edualert.catalogs.factories import StudentCatalogPerYearFactory
from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.study_classes.factories import StudyClassFactory


@ddt
class MoveStudentPossibleStudyClassesTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.principal = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL)
        cls.school_unit = RegisteredSchoolUnitFactory(school_principal=cls.principal)
        cls.student = UserProfileFactory(
            user_role=UserProfile.UserRoles.STUDENT,
            student_in_class=StudyClassFactory(class_grade='X', class_grade_arabic=10, academic_year=2020),
            school_unit=cls.school_unit
        )
        cls.current_class = cls.student.student_in_class
        cls.previous_catalog = StudentCatalogPerYearFactory(
            student=cls.student,
            study_class=cls.current_class,
            academic_year=cls.current_class.academic_year - 1,
            avg_final=5.0,
        )

    def setUp(self):
        self.student.refresh_from_db()

    @staticmethod
    def build_url(student_id):
        return reverse('study_classes:move-student-possible-study-classes', kwargs={'id': student_id})

    def test_move_student_possible_study_classes_unauthenticated(self):
        response = self.client.get(self.build_url(self.student.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.TEACHER,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_move_student_possible_study_classes_wrong_user_type(self, user_role):
        user = UserProfileFactory(
            user_role=user_role,
            school_unit=self.school_unit if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )
        self.client.login(username=user.username, password='passwd')

        response = self.client.get(self.build_url(self.student.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_move_student_possible_study_classes_student_does_not_exist(self):
        self.client.login(username=self.principal.username, password='passwd')

        response = self.client.get(self.build_url(0))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_move_student_possible_study_classes_no_possible_classes(self):
        self.client.login(username=self.principal.username, password='passwd')

        # No study classes in the current year
        study_class = StudyClassFactory(
            school_unit=self.school_unit,
            class_grade='IX',
            class_grade_arabic=9,
            academic_year=self.current_class.academic_year - 1
        )

        response = self.client.get(self.build_url(self.student.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

        # No study classes with a low enough entry grade
        StudentCatalogPerYearFactory(
            study_class=study_class,
            academic_year=study_class.academic_year - 1,
            avg_final=5.1
        )

        response = self.client.get(self.build_url(self.student.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_move_student_possible_study_classes_ninth_grade(self):
        self.client.login(username=self.principal.username, password='passwd')
        self.student.student_in_class = StudyClassFactory(
            class_grade_arabic=9,
            class_grade='IX',
            class_letter='B'
        )
        self.student.save()

        study_class = StudyClassFactory(
            school_unit=self.school_unit,
            class_grade='IX',
            class_grade_arabic=9,
            class_letter='C'
        )

        other_study_class = StudyClassFactory(
            school_unit=self.school_unit,
            class_grade='IX',
            class_grade_arabic=9,
            class_letter='D'
        )

        response = self.client.get(self.build_url(self.student.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual([study_class['id'] for study_class in response.data], [study_class.id, other_study_class.id])
        expected_fields = ['id', 'class_grade', 'class_letter']
        for study_class in response.data:
            self.assertCountEqual(study_class.keys(), expected_fields)

    def test_move_student_possible_study_classes_success(self):
        self.client.login(username=self.principal.username, password='passwd')

        study_class = StudyClassFactory(school_unit=self.school_unit, class_grade='X', class_letter='B', class_grade_arabic=10)
        past_class = StudyClassFactory(school_unit=self.school_unit, class_grade='IX', class_letter='B', class_grade_arabic=9, academic_year=2019)
        StudentCatalogPerYearFactory(study_class=past_class, avg_final=4.8, academic_year=2019)
        StudentCatalogPerYearFactory(study_class=past_class, avg_final=5.1, academic_year=2019)

        other_study_class = StudyClassFactory(school_unit=self.school_unit, class_grade='X', class_letter='C', class_grade_arabic=10)
        past_class = StudyClassFactory(school_unit=self.school_unit, class_grade='IX', class_letter='C', class_grade_arabic=9, academic_year=2019)
        StudentCatalogPerYearFactory(study_class=past_class, avg_final=4.8, academic_year=2019)

        other_study_class1 = StudyClassFactory(school_unit=self.school_unit, class_grade='X', class_letter='D', class_grade_arabic=10)
        past_class = StudyClassFactory(school_unit=self.school_unit, class_grade='IX', class_letter='D', class_grade_arabic=9, academic_year=2019)
        StudentCatalogPerYearFactory(study_class=past_class, avg_final=5.1, academic_year=2019)

        other_study_class2 = StudyClassFactory(school_unit=self.school_unit, class_grade='X', class_letter='E', class_grade_arabic=10)
        past_class = StudyClassFactory(school_unit=self.school_unit, class_grade='IX', class_letter='E', class_grade_arabic=9, academic_year=2019)
        StudentCatalogPerYearFactory(study_class=past_class, avg_final=4.8, academic_year=2019)

        other_study_class3 = StudyClassFactory(school_unit=self.school_unit, class_grade='XI', class_letter='A', class_grade_arabic=11)
        past_class = StudyClassFactory(school_unit=self.school_unit, class_grade='X', class_letter='A', class_grade_arabic=10, academic_year=2019)
        StudentCatalogPerYearFactory(study_class=past_class, avg_final=4.8, academic_year=2019)

        response = self.client.get(self.build_url(self.student.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertCountEqual([study_class['id'] for study_class in response.data], [study_class.id, other_study_class.id, other_study_class2.id])
        expected_fields = ['id', 'class_grade', 'class_letter']
        for study_class_data in response.data:
            self.assertCountEqual(study_class_data.keys(), expected_fields)

        self.assertEqual(response.data[0]['id'], study_class.id)
        self.assertEqual(response.data[1]['id'], other_study_class.id)
        self.assertEqual(response.data[2]['id'], other_study_class2.id)
