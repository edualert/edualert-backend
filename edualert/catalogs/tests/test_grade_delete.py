import datetime
from unittest.mock import patch

from ddt import data, ddt
from django.urls import reverse
from django.utils import timezone
from pytz import utc
from rest_framework import status

from edualert.academic_calendars.factories import AcademicYearCalendarFactory
from edualert.catalogs.factories import StudentCatalogPerSubjectFactory, SubjectGradeFactory, StudentCatalogPerYearFactory
from edualert.catalogs.models import SubjectGrade
from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.statistics.factories import SchoolUnitStatsFactory
from edualert.study_classes.factories import StudyClassFactory, TeacherClassThroughFactory
from edualert.subjects.factories import SubjectFactory, ProgramSubjectThroughFactory


@ddt
class GradeDeleteTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_calendar = AcademicYearCalendarFactory()
        cls.school_unit = RegisteredSchoolUnitFactory()
        cls.school_stats = SchoolUnitStatsFactory(school_unit=cls.school_unit)

        cls.teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=cls.school_unit)
        cls.study_class = StudyClassFactory(school_unit=cls.school_unit)
        cls.subject = SubjectFactory()
        cls.teacher_class_through = TeacherClassThroughFactory(study_class=cls.study_class, teacher=cls.teacher, subject=cls.subject)
        ProgramSubjectThroughFactory(academic_program=cls.study_class.academic_program,
                                     subject=cls.subject, weekly_hours_count=1, class_grade=cls.study_class.class_grade,
                                     class_grade_arabic=cls.study_class.class_grade_arabic)

        cls.student = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, student_in_class=cls.study_class)
        cls.catalog = StudentCatalogPerSubjectFactory(
            subject=cls.subject,
            teacher=cls.teacher,
            student=cls.student,
            study_class=cls.study_class,
            academic_year=2020,
            is_enrolled=True
        )
        cls.catalog_per_year = StudentCatalogPerYearFactory(
            student=cls.student,
            study_class=cls.study_class
        )

    def setUp(self):
        self.catalog.refresh_from_db()

    def create_grade(self):
        return SubjectGradeFactory(
            catalog_per_subject=self.catalog,
            student=self.catalog.student,
            taken_at=datetime.date(2020, 4, 4),
            semester=2
        )

    @staticmethod
    def build_url(grade_id):
        return reverse('catalogs:grade-detail', kwargs={'id': grade_id})

    def test_grade_delete_unauthenticated(self):
        response = self.client.delete(self.build_url(self.create_grade().id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.PRINCIPAL,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_grade_delete_wrong_user_type(self, user_role):
        user = UserProfileFactory(
            user_role=user_role,
            school_unit=self.school_unit if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )
        self.client.login(username=user.username, password='passwd')

        response = self.client.delete(self.build_url(self.create_grade().id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_grade_delete_grade_does_not_exist(self):
        self.client.login(username=self.teacher.username, password='passwd')
        response = self.client.delete(self.build_url(0))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_grade_delete_teacher_not_assigned(self):
        self.client.login(username=self.teacher.username, password='passwd')
        self.catalog.teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER)
        self.catalog.save()
        response = self.client.delete(self.build_url(self.create_grade().id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_grade_delete_coordination_subject(self):
        self.client.login(username=self.teacher.username, password='passwd')
        self.catalog.is_coordination_subject = True
        self.catalog.save()
        response = self.client.delete(self.build_url(self.create_grade().id))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], "Can't delete coordination subject grade.")

    @data(
        datetime.datetime(2020, 4, 4, 7, 59, 59),
        datetime.datetime(2020, 4, 3, 22, 59),
    )
    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 4, 4, 12, 0, 0).replace(tzinfo=utc))
    def test_grade_delete_grade_more_than_two_hours_in_the_past(self, created_at, mocked_method):
        self.client.login(username=self.teacher.username, password='passwd')
        grade = self.create_grade()
        grade.created = created_at.replace(tzinfo=utc)
        grade.save()

        response = self.client.delete(self.build_url(grade.id))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'message': 'Cannot delete a grade that was created more than 2 hours ago.'})

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 4, 4, 12, 0, 0).replace(tzinfo=utc))
    def test_grade_delete_success(self, mocked_method):
        self.client.login(username=self.teacher.username, password='passwd')
        grade = self.create_grade()
        response = self.client.delete(self.build_url(grade.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(SubjectGrade.objects.filter(id=grade.id).exists())

        catalog_expected_fields = [
            'id', 'student', 'avg_sem1', 'avg_sem2', 'avg_annual', 'avg_after_2nd_examination', 'avg_limit', 'abs_count_sem1', 'abs_count_sem2',
            'abs_count_annual', 'founded_abs_count_sem1', 'founded_abs_count_sem2', 'founded_abs_count_annual', 'unfounded_abs_count_sem1',
            'unfounded_abs_count_sem2', 'unfounded_abs_count_annual', 'grades_sem1', 'grades_sem2', 'abs_sem1', 'abs_sem2',
            'second_examination_grades', 'difference_grades_sem1', 'difference_grades_sem2', 'wants_thesis', 'is_exempted',
            'third_of_hours_count_sem1', 'third_of_hours_count_sem2', 'third_of_hours_count_annual', 'is_coordination_subject'
        ]
        grade_fields = ['id', 'grade', 'taken_at', 'grade_type', 'created']
        self.assertCountEqual(response.data.keys(), catalog_expected_fields)
        for grade_data in response.data['grades_sem1'] + response.data['grades_sem2']:
            self.assertCountEqual(grade_data.keys(), grade_fields)

        self.teacher.refresh_from_db()
        self.assertEqual(self.teacher.last_change_in_catalog, timezone.datetime(2020, 4, 4, 12, 0, 0).replace(tzinfo=utc))
        self.assertEqual(self.teacher.school_unit.last_change_in_catalog, timezone.datetime(2020, 4, 4, 12, 0, 0).replace(tzinfo=utc))

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2019, 11, 10).replace(tzinfo=utc))
    def test_grade_delete_secondary_school_averages(self, mocked_method):
        # This is for a subject with weekly hours count = 1 and no thesis (1st semester)
        self.client.login(username=self.teacher.username, password='passwd')

        SubjectGradeFactory(student=self.student, catalog_per_subject=self.catalog, semester=1, grade=8)
        grade1 = SubjectGradeFactory(student=self.student, catalog_per_subject=self.catalog, semester=1, grade=8)
        grade2 = SubjectGradeFactory(student=self.student, catalog_per_subject=self.catalog, semester=1, grade=10)
        self.catalog.avg_sem1 = 9
        self.catalog.save()

        response = self.client.delete(self.build_url(grade2.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.refresh_objects_from_db([self.catalog, self.catalog_per_year, self.study_class, self.school_stats])
        for obj in [self.catalog, self.catalog_per_year, self.study_class, self.school_stats]:
            self.assertEqual(obj.avg_sem1, 8)
            self.assertIsNone(obj.avg_sem2)
            self.assertIsNone(obj.avg_annual)
        self.assertIsNone(self.catalog.avg_final)
        self.assertIsNone(self.catalog_per_year.avg_final)

        response = self.client.delete(self.build_url(grade1.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.refresh_objects_from_db([self.catalog, self.catalog_per_year, self.study_class, self.school_stats])
        for obj in [self.catalog, self.catalog_per_year, self.study_class, self.school_stats]:
            self.assertIsNone(obj.avg_sem1)
            self.assertIsNone(obj.avg_sem2)
            self.assertIsNone(obj.avg_annual)
        self.assertIsNone(self.catalog.avg_final)
        self.assertIsNone(self.catalog_per_year.avg_final)

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 3, 3).replace(tzinfo=utc))
    def test_grade_delete_highschool_school_averages(self, mocked_method):
        # This is for an optional subject with weekly hours count = 3 and with thesis (2nd semester)
        self.client.login(username=self.teacher.username, password='passwd')

        self.study_class.class_grade = 'IX'
        self.study_class.class_grade_arabic = 9
        self.study_class.save()
        ProgramSubjectThroughFactory(academic_program=self.study_class.academic_program, subject=self.subject,
                                     weekly_hours_count=3)
        for i in range(3):
            SubjectGradeFactory(student=self.student, catalog_per_subject=self.catalog, semester=2, grade=9)
        grade1 = SubjectGradeFactory(student=self.student, catalog_per_subject=self.catalog, semester=2,
                                     grade=6, grade_type=SubjectGrade.GradeTypes.THESIS)
        grade2 = SubjectGradeFactory(student=self.student, catalog_per_subject=self.catalog, semester=2, grade=10)
        SubjectGradeFactory(student=self.student, catalog_per_subject=self.catalog, semester=2, grade=10)

        self.catalog.avg_sem1 = 9
        self.catalog.avg_sem2 = 9
        self.catalog.avg_annual = 9
        self.catalog.avg_final = 9
        self.catalog.wants_thesis = True
        self.catalog.save()

        response = self.client.delete(self.build_url(grade2.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.refresh_objects_from_db([self.catalog, self.catalog_per_year, self.study_class,
                                      self.study_class.academic_program, self.school_stats])
        for obj in [self.catalog, self.catalog_per_year, self.study_class, self.study_class.academic_program, self.school_stats]:
            self.assertEqual(obj.avg_sem1, 9)
            self.assertEqual(obj.avg_sem2, 8)
            self.assertEqual(obj.avg_annual, 8.5)
        self.assertEqual(self.catalog.avg_final, 8.5)
        self.assertEqual(self.catalog_per_year.avg_final, 8.5)

        response = self.client.delete(self.build_url(grade1.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.catalog.refresh_from_db()
        self.assertEqual(self.catalog.avg_sem1, 9)
        self.assertIsNone(self.catalog.avg_sem2)
        self.assertIsNone(self.catalog.avg_annual)
        self.assertIsNone(self.catalog.avg_final)
        self.refresh_objects_from_db([self.catalog, self.catalog_per_year, self.study_class,
                                      self.study_class.academic_program, self.school_stats])
        for obj in [self.catalog, self.catalog_per_year, self.study_class, self.study_class.academic_program, self.school_stats]:
            self.assertEqual(obj.avg_sem1, 9)
            self.assertIsNone(obj.avg_sem2)
            self.assertIsNone(obj.avg_annual)
        self.assertIsNone(self.catalog.avg_final)
        self.assertIsNone(self.catalog_per_year.avg_final)
