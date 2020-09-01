from ddt import data, ddt
from django.urls import reverse
from rest_framework import status

from edualert.academic_calendars.factories import AcademicYearCalendarFactory
from edualert.catalogs.factories import StudentCatalogPerSubjectFactory, StudentCatalogPerYearFactory
from edualert.catalogs.models import StudentCatalogPerSubject
from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.study_classes.factories import StudyClassFactory, TeacherClassThroughFactory
from edualert.subjects.factories import SubjectFactory


@ddt
class MoveStudentTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year_calendar = AcademicYearCalendarFactory()
        cls.school_unit = RegisteredSchoolUnitFactory()
        cls.principal = cls.school_unit.school_principal
        cls.subject1 = SubjectFactory()
        cls.subject2 = SubjectFactory()
        cls.subject3 = SubjectFactory()

        cls.study_class = StudyClassFactory(
            school_unit=cls.school_unit,
            class_grade_arabic=10,
            class_grade='X',
            class_letter='B'
        )
        TeacherClassThroughFactory(study_class=cls.study_class, teacher=cls.study_class.class_master, subject=cls.subject1, is_class_master=True)
        TeacherClassThroughFactory(study_class=cls.study_class, teacher=cls.study_class.class_master, subject=cls.subject2, is_class_master=True)

        cls.source_study_class = StudyClassFactory(class_grade='X', class_grade_arabic=10, school_unit=cls.school_unit)
        cls.student = UserProfileFactory(
            user_role=UserProfile.UserRoles.STUDENT,
            school_unit=cls.school_unit,
            student_in_class=cls.source_study_class
        )

        cls.expected_fields = ['id', 'class_grade', 'class_letter', 'academic_year', 'academic_program', 'academic_program_name',
                               'class_master', 'teachers_class_through', 'students', 'has_previous_catalog_data']

    def setUp(self):
        self.refresh_objects_from_db([self.source_study_class, self.study_class])

    @staticmethod
    def build_url(student_id, study_class_id):
        return reverse('study_classes:move-student', kwargs={'student_id': student_id, 'study_class_id': study_class_id})

    def test_move_student_unauthenticated(self):
        response = self.client.post(self.build_url(self.student.id, self.study_class.id), {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.TEACHER,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_move_student_wrong_user_type(self, user_role):
        user = UserProfileFactory(
            user_role=user_role,
            school_unit=self.school_unit if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )
        self.client.login(username=user.username, password='passwd')

        response = self.client.post(self.build_url(self.student.id, self.study_class.id), {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_move_student_study_class_does_not_belong_to_school(self):
        self.client.login(username=self.principal.username, password='passwd')
        self.study_class.school_unit = RegisteredSchoolUnitFactory()
        self.study_class.save()
        response = self.client.post(self.build_url(self.student.id, self.study_class.id), {})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_move_student_student_does_not_exist(self):
        self.client.login(username=self.principal.username, password='passwd')
        response = self.client.post(self.build_url(0, self.study_class.id), {})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_move_student_study_class_does_not_exist(self):
        self.client.login(username=self.principal.username, password='passwd')
        response = self.client.post(self.build_url(self.student.id, 0), {})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_move_student_same_class(self):
        self.client.login(username=self.principal.username, password='passwd')
        response = self.client.post(self.build_url(self.student.id, self.source_study_class.id), {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], 'The student is already in this study class.')

    def test_move_student_different_grade(self):
        self.client.login(username=self.principal.username, password='passwd')
        self.study_class.class_grade = 'IX'
        self.study_class.save()

        response = self.client.post(self.build_url(self.student.id, self.study_class.id), {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], 'Cannot move students to a class from another grade.')

    def test_move_student_different_academic_year(self):
        self.client.login(username=self.principal.username, password='passwd')
        self.study_class.academic_year = 2000
        self.study_class.save()

        response = self.client.post(self.build_url(self.student.id, self.study_class.id), {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], 'Cannot move students to a class from another year.')

    def test_move_student_not_having_required_avg(self):
        self.client.login(username=self.principal.username, password='passwd')
        previous_year = self.study_class.academic_year - 1
        StudentCatalogPerYearFactory(student=self.student, academic_year=previous_year, avg_final=7)
        previous_study_class = StudyClassFactory(school_unit=self.school_unit, academic_year=previous_year,
                                                 class_grade='IX', class_grade_arabic=9)
        StudentCatalogPerYearFactory(study_class=previous_study_class, avg_final=8)

        response = self.client.post(self.build_url(self.student.id, self.study_class.id), {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], "This student doesn't have the required average for this study class.")

    def test_move_student_ninth_grade(self):
        self.client.login(username=self.principal.username, password='passwd')
        for study_class in [self.study_class, self.source_study_class]:
            study_class.class_grade = 'IX'
            study_class.class_grade_arabic = 9
            study_class.save()
        catalog_per_year = StudentCatalogPerYearFactory(student=self.student, study_class=self.source_study_class)
        catalog_per_subject1 = StudentCatalogPerSubjectFactory(student=self.student, teacher=self.source_study_class.class_master,
                                                               study_class=self.source_study_class, subject=self.subject1)
        catalog_per_subject2 = StudentCatalogPerSubjectFactory(student=self.student, teacher=self.source_study_class.class_master,
                                                               study_class=self.source_study_class, subject=self.subject3)

        response = self.client.post(self.build_url(self.student.id, self.study_class.id), {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(response.data.keys(), self.expected_fields)
        self.assertEqual(response.data['id'], self.source_study_class.id)

        self.refresh_objects_from_db([self.student, self.principal, self.school_unit, catalog_per_year,
                                      catalog_per_subject1, catalog_per_subject2])
        self.assertEqual(self.student.student_in_class, self.study_class)
        self.assertEqual(catalog_per_year.study_class, self.study_class)

        self.assertTrue(catalog_per_subject1.is_enrolled)
        self.assertEqual(catalog_per_subject1.teacher, self.study_class.class_master)
        self.assertEqual(catalog_per_subject1.study_class, self.study_class)

        self.assertFalse(catalog_per_subject2.is_enrolled)
        self.assertEqual(catalog_per_subject2.teacher, self.source_study_class.class_master)
        self.assertEqual(catalog_per_subject2.study_class, self.source_study_class)

        self.assertTrue(StudentCatalogPerSubject.objects.filter(student=self.student, teacher=self.study_class.class_master,
                                                                study_class=self.study_class, subject=self.subject2).exists())

        self.assertIsNotNone(self.principal.last_change_in_catalog)
        self.assertIsNotNone(self.school_unit.last_change_in_catalog)

    def test_move_student_success(self):
        self.client.login(username=self.principal.username, password='passwd')

        catalog_per_year1 = StudentCatalogPerYearFactory(student=self.student, study_class=self.source_study_class)
        catalog_per_subject1 = StudentCatalogPerSubjectFactory(student=self.student, teacher=self.source_study_class.class_master,
                                                               study_class=self.source_study_class, subject=self.subject1)
        catalog_per_subject2 = StudentCatalogPerSubjectFactory(student=self.student, teacher=self.source_study_class.class_master,
                                                               study_class=self.source_study_class, subject=self.subject3)

        previous_study_class = StudyClassFactory(school_unit=self.school_unit, academic_year=self.study_class.academic_year - 1,
                                                 class_grade_arabic=9, class_grade='IX', class_letter='B', class_master=self.study_class.class_master)
        TeacherClassThroughFactory(study_class=previous_study_class, teacher=self.study_class.class_master,
                                   subject=self.subject1, is_class_master=True)
        TeacherClassThroughFactory(study_class=previous_study_class, teacher=self.study_class.class_master,
                                   subject=self.subject2, is_class_master=True)
        optional_subject = SubjectFactory()
        TeacherClassThroughFactory(study_class=previous_study_class, teacher=self.study_class.class_master,
                                   subject=optional_subject, is_class_master=True, is_optional_subject=True)

        own_previous_study_class = StudyClassFactory(school_unit=self.school_unit, academic_year=self.source_study_class.academic_year - 1,
                                                     class_grade='IX', class_grade_arabic=9, class_master=self.source_study_class.class_master)
        catalog_per_year2 = StudentCatalogPerYearFactory(student=self.student, study_class=own_previous_study_class)
        catalog_per_subject3 = StudentCatalogPerSubjectFactory(student=self.student, teacher=self.source_study_class.class_master,
                                                               study_class=own_previous_study_class, subject=self.subject1)
        catalog_per_subject4 = StudentCatalogPerSubjectFactory(student=self.student, teacher=self.source_study_class.class_master,
                                                               study_class=own_previous_study_class, subject=self.subject3)

        response = self.client.post(self.build_url(self.student.id, self.study_class.id), {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(response.data.keys(), self.expected_fields)
        self.assertEqual(response.data['id'], self.source_study_class.id)

        self.refresh_objects_from_db([self.student, self.principal, self.school_unit, catalog_per_year1, catalog_per_year2,
                                      catalog_per_subject1, catalog_per_subject2, catalog_per_subject3, catalog_per_subject4])
        self.assertEqual(self.student.student_in_class, self.study_class)

        self.assertEqual(catalog_per_year1.study_class, self.study_class)
        self.assertEqual(catalog_per_year2.study_class, previous_study_class)

        self.assertTrue(catalog_per_subject1.is_enrolled)
        self.assertEqual(catalog_per_subject1.teacher, self.study_class.class_master)
        self.assertEqual(catalog_per_subject1.study_class, self.study_class)

        self.assertFalse(catalog_per_subject2.is_enrolled)
        self.assertEqual(catalog_per_subject2.teacher, self.source_study_class.class_master)
        self.assertEqual(catalog_per_subject2.study_class, self.source_study_class)

        self.assertTrue(catalog_per_subject3.is_enrolled)
        self.assertEqual(catalog_per_subject3.teacher, own_previous_study_class.class_master)
        self.assertEqual(catalog_per_subject3.study_class, previous_study_class)

        self.assertFalse(catalog_per_subject4.is_enrolled)
        self.assertEqual(catalog_per_subject4.teacher, own_previous_study_class.class_master)
        self.assertEqual(catalog_per_subject4.study_class, own_previous_study_class)

        self.assertTrue(StudentCatalogPerSubject.objects.filter(student=self.student, teacher=self.study_class.class_master,
                                                                study_class=self.study_class, subject=self.subject2).exists())
        self.assertTrue(StudentCatalogPerSubject.objects.filter(student=self.student, teacher=previous_study_class.class_master,
                                                                study_class=previous_study_class, subject=self.subject2).exists())
        self.assertTrue(StudentCatalogPerSubject.objects.filter(student=self.student, subject=optional_subject, is_enrolled=False).exists())
