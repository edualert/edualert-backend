from unittest.mock import patch

from ddt import data, ddt
from django.urls import reverse
from django.utils import timezone
from pytz import utc
from rest_framework import status

from edualert.academic_calendars.factories import AcademicYearCalendarFactory
from edualert.catalogs.factories import StudentCatalogPerSubjectFactory
from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.study_classes.factories import StudyClassFactory
from edualert.subjects.factories import SubjectFactory, ProgramSubjectThroughFactory


@ddt
class DifferenceSubjectListTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.school_unit = RegisteredSchoolUnitFactory()
        cls.principal = cls.school_unit.school_principal
        cls.study_class = StudyClassFactory(
            school_unit=cls.school_unit,
            class_grade_arabic=11,
            class_grade='XI'
        )
        cls.generic_academic_program = cls.study_class.academic_program.generic_academic_program
        cls.academic_year_calendar = AcademicYearCalendarFactory()
        cls.student = UserProfileFactory(
            user_role=UserProfile.UserRoles.STUDENT,
            school_unit=cls.school_unit,
            student_in_class=StudyClassFactory(class_grade='XI', class_grade_arabic=11)
        )

    @staticmethod
    def build_url(student_id, study_class_id):
        return reverse('study_classes:difference-subject-list', kwargs={'student_id': student_id, 'study_class_id': study_class_id})

    def test_difference_subject_list_unauthenticated(self):
        response = self.client.get(self.build_url(self.student.id, self.study_class.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.TEACHER,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_difference_subject_list_wrong_user_type(self, user_role):
        user = UserProfileFactory(
            user_role=user_role,
            school_unit=self.school_unit if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )
        self.client.login(username=user.username, password='passwd')

        response = self.client.get(self.build_url(self.student.id, self.study_class.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_difference_subject_list_study_class_does_not_belong_to_school(self):
        self.client.login(username=self.principal.username, password='passwd')
        self.study_class.school_unit = RegisteredSchoolUnitFactory()
        self.study_class.save()
        response = self.client.get(self.build_url(self.student.id, self.study_class.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_difference_subject_list_student_does_not_exist(self):
        self.client.login(username=self.principal.username, password='passwd')
        response = self.client.get(self.build_url(0, self.study_class.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_difference_subject_list_study_class_does_not_exist(self):
        self.client.login(username=self.principal.username, password='passwd')
        response = self.client.get(self.build_url(self.student.id, 0))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_difference_subject_list_student_moves_to_the_same_program(self):
        self.client.login(username=self.principal.username, password='passwd')
        study_class = self.student.student_in_class
        study_class.academic_program = self.study_class.academic_program
        study_class.save()
        response = self.client.get(self.build_url(self.student.id, self.study_class.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {})

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 4, 4).replace(tzinfo=utc))
    def test_difference_subject_list_secondary_school(self, mocked_method):
        self.client.login(username=self.principal.username, password='passwd')
        student = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=self.school_unit)
        student.student_in_class = StudyClassFactory(
            school_unit=self.school_unit,
            class_grade_arabic=7,
            class_grade='VII'
        )
        student.save()

        study_class = StudyClassFactory(
            school_unit=self.school_unit,
            class_grade_arabic=7,
            class_grade='VII'
        )

        subject1 = SubjectFactory()
        response = self.client.get(self.build_url(student.id, study_class.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {})

    @data(
        timezone.datetime(2019, 12, 1),
        timezone.datetime(2020, 4, 4)
    )
    def test_difference_subject_list_success(self, today):
        self.client.login(username=self.principal.username, password='passwd')
        semester = 1 if today == timezone.datetime(2019, 12, 1) else 2

        subject1 = SubjectFactory()
        ProgramSubjectThroughFactory(
            generic_academic_program=self.generic_academic_program,
            subject=subject1,
            class_grade_arabic=9,
            class_grade='IX'
        )

        subject2 = SubjectFactory()
        ProgramSubjectThroughFactory(
            generic_academic_program=self.generic_academic_program,
            subject=subject2,
            class_grade_arabic=9,
            class_grade='IX'
        )
        StudentCatalogPerSubjectFactory(
            student=self.student,
            study_class=StudyClassFactory(class_grade='IX', class_grade_arabic=9),
            subject=subject2
        )

        ProgramSubjectThroughFactory(
            generic_academic_program=self.generic_academic_program,
            subject=subject2,
            class_grade_arabic=10,
            class_grade='X'
        )

        subject4 = SubjectFactory()
        ProgramSubjectThroughFactory(
            generic_academic_program=self.generic_academic_program,
            subject=subject4,
            class_grade_arabic=10,
            class_grade='X'
        )

        subject5 = SubjectFactory()
        ProgramSubjectThroughFactory(
            subject=subject5,
            generic_academic_program=self.generic_academic_program,
            class_grade_arabic=11,
            class_grade='XI'
        )

        subject6 = SubjectFactory()
        ProgramSubjectThroughFactory(
            subject=subject6,
            generic_academic_program=self.generic_academic_program,
            class_grade_arabic=12,
            class_grade='XII'
        )

        with patch('django.utils.timezone.now', return_value=today.replace(tzinfo=utc)) as mocked_method:
            response = self.client.get(self.build_url(self.student.id, self.study_class.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        if semester == 1:
            expected_grades = ['IX', 'X']
            self.assertCountEqual([subject['id'] for subject in response.data['IX']], [subject1.id])
            self.assertCountEqual([subject['id'] for subject in response.data['X']], [subject2.id, subject4.id])
        else:
            expected_grades = ['IX', 'X', 'XI']
            self.assertCountEqual([subject['id'] for subject in response.data['IX']], [subject1.id])
            self.assertCountEqual([subject['id'] for subject in response.data['X']], [subject2.id, subject4.id])
            self.assertCountEqual([subject['id'] for subject in response.data['XI']], [subject5.id])

        self.assertCountEqual(response.data.keys(), expected_grades)
        subject_expected_fields = ['id', 'name']
        for subject_list in response.data.values():
            for subject in subject_list:
                self.assertCountEqual(subject.keys(), subject_expected_fields)

        StudentCatalogPerSubjectFactory(
            student=self.student,
            study_class=StudyClassFactory(class_grade='X', class_grade_arabic=10),
            subject=subject4
        )

        with patch('django.utils.timezone.now', return_value=today.replace(tzinfo=utc)) as mocked_method:
            response = self.client.get(self.build_url(self.student.id, self.study_class.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        if semester == 1:
            expected_grades = ['IX', 'X']
        else:
            expected_grades = ['IX', 'X', 'XI']

        self.assertCountEqual([subject['id'] for subject in response.data['X']], [subject2.id])
        self.assertCountEqual(response.data.keys(), expected_grades)
