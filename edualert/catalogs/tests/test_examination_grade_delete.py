import datetime
from unittest.mock import patch

from ddt import data, ddt
from django.urls import reverse
from django.utils import timezone
from pytz import utc
from rest_framework import status

from edualert.academic_calendars.factories import AcademicYearCalendarFactory, SchoolEventFactory
from edualert.academic_calendars.models import SchoolEvent
from edualert.catalogs.factories import StudentCatalogPerSubjectFactory, ExaminationGradeFactory, StudentCatalogPerYearFactory
from edualert.catalogs.models import ExaminationGrade
from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.statistics.factories import SchoolUnitStatsFactory
from edualert.study_classes.factories import StudyClassFactory, TeacherClassThroughFactory
from edualert.subjects.factories import SubjectFactory, ProgramSubjectThroughFactory


@ddt
class ExaminationGradeDeleteTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_calendar = AcademicYearCalendarFactory()
        cls.corigente_event = SchoolEventFactory(event_type=SchoolEvent.EventTypes.CORIGENTE, academic_year_calendar=cls.academic_calendar,
                                                 starts_at=datetime.date(2020, 8, 20), ends_at=datetime.date(2020, 8, 27))
        cls.diferente_event = SchoolEventFactory(event_type=SchoolEvent.EventTypes.DIFERENTE, academic_year_calendar=cls.academic_calendar,
                                                 starts_at=datetime.date(2020, 9, 1), ends_at=datetime.date(2020, 9, 8))

        cls.school_unit = RegisteredSchoolUnitFactory()
        cls.school_stats = SchoolUnitStatsFactory(school_unit=cls.school_unit)

        cls.teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=cls.school_unit)
        cls.study_class = StudyClassFactory(school_unit=cls.school_unit, class_grade='IX', class_grade_arabic=9)
        cls.subject = SubjectFactory()
        ProgramSubjectThroughFactory(academic_program=cls.study_class.academic_program, class_grade='IX',
                                     subject=cls.subject, weekly_hours_count=3)

        cls.student = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, student_in_class=cls.study_class)
        cls.teacher_class_through = TeacherClassThroughFactory(
            study_class=cls.study_class,
            teacher=cls.teacher,
            subject=cls.subject
        )
        cls.catalog = StudentCatalogPerSubjectFactory(
            subject=cls.subject,
            teacher=cls.teacher,
            student=cls.student,
            study_class=cls.study_class
        )
        cls.catalog_per_year = StudentCatalogPerYearFactory(
            student=cls.student,
            study_class=cls.study_class
        )

        cls.expected_fields = [
            'id', 'student', 'avg_sem1', 'avg_sem2', 'avg_annual', 'avg_after_2nd_examination', 'avg_limit', 'abs_count_sem1', 'abs_count_sem2',
            'abs_count_annual', 'founded_abs_count_sem1', 'founded_abs_count_sem2', 'founded_abs_count_annual', 'unfounded_abs_count_sem1',
            'unfounded_abs_count_sem2', 'unfounded_abs_count_annual', 'grades_sem1', 'grades_sem2', 'abs_sem1', 'abs_sem2',
            'second_examination_grades', 'difference_grades_sem1', 'difference_grades_sem2', 'wants_thesis', 'is_exempted',
            'third_of_hours_count_sem1', 'third_of_hours_count_sem2', 'third_of_hours_count_annual', 'is_coordination_subject'
        ]
        cls.examination_grade_fields = ['id', 'examination_type', 'taken_at', 'grade1', 'grade2', 'created']

    def setUp(self):
        self.catalog.refresh_from_db()

    def create_2nd_exam_grade(self):
        return ExaminationGradeFactory(
            catalog_per_subject=self.catalog,
            student=self.catalog.student,
            taken_at=datetime.date(2020, 8, 20))

    def create_difference_grade(self):
        return ExaminationGradeFactory(
            catalog_per_subject=self.catalog,
            student=self.catalog.student,
            taken_at=datetime.date(2020, 9, 1),
            grade_type=ExaminationGrade.GradeTypes.DIFFERENCE)

    @staticmethod
    def build_url(grade_id):
        return reverse('catalogs:examination-grade-detail', kwargs={'id': grade_id})

    def test_examination_grade_delete_unauthenticated(self):
        response = self.client.delete(self.build_url(self.create_difference_grade().id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.PRINCIPAL,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_examination_grade_delete_wrong_user_type(self, user_role):
        user = UserProfileFactory(
            user_role=user_role,
            school_unit=self.school_unit if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )
        self.client.login(username=user.username, password='passwd')

        response = self.client.delete(self.build_url(self.create_difference_grade().id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_examination_grade_delete_grade_does_not_exist(self):
        self.client.login(username=self.teacher.username, password='passwd')
        response = self.client.delete(self.build_url(0))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_examination_grade_delete_teacher_not_assigned(self):
        self.client.login(username=self.teacher.username, password='passwd')
        self.catalog.teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER)
        self.catalog.save()
        response = self.client.delete(self.build_url(self.create_difference_grade().id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @data(
        datetime.datetime(2020, 9, 2, 8, 59, 59),
        datetime.datetime(2020, 9, 1, 22, 59)
    )
    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 9, 2, 12, 0, 0).replace(tzinfo=utc))
    def test_examination_grade_delete_grade_more_than_two_hours_in_the_past(self, created_at, mocked_method):
        self.client.login(username=self.teacher.username, password='passwd')
        grade = self.create_difference_grade()
        grade.created = created_at.replace(tzinfo=utc)
        grade.save()

        response = self.client.delete(self.build_url(grade.id))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'message': 'Cannot delete a grade that was created more than 2 hours ago.'})

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 8, 20).replace(tzinfo=utc))
    def test_examination_grade_delete_2nd_exam_success(self, mocked_method):
        self.client.login(username=self.teacher.username, password='passwd')
        grade = self.create_2nd_exam_grade()
        response = self.client.delete(self.build_url(grade.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(ExaminationGrade.objects.filter(id=grade.id).exists())

        self.assertCountEqual(response.data.keys(), self.expected_fields)
        for examination_data in response.data['second_examination_grades'] + response.data['difference_grades_sem1'] + response.data['difference_grades_sem2']:
            self.assertCountEqual(examination_data.keys(), self.examination_grade_fields)

        self.refresh_objects_from_db([self.catalog, self.catalog_per_year, self.study_class, self.study_class.academic_program,
                                      self.school_stats, self.teacher, self.teacher.school_unit])
        for catalog in [self.catalog, self.catalog_per_year]:
            self.assertIsNone(catalog.avg_annual)
            self.assertIsNone(catalog.avg_final)
        for obj in [self.study_class, self.study_class.academic_program, self.school_stats]:
            self.assertIsNone(obj.avg_annual)

        self.assertEqual(self.teacher.last_change_in_catalog, timezone.now())
        self.assertEqual(self.teacher.school_unit.last_change_in_catalog, timezone.now())

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 9, 1).replace(tzinfo=utc))
    def test_examination_grade_delete_difference_success(self, mocked_method):
        self.client.login(username=self.teacher.username, password='passwd')
        grade = self.create_difference_grade()
        response = self.client.delete(self.build_url(grade.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(ExaminationGrade.objects.filter(id=grade.id).exists())

        self.assertCountEqual(response.data.keys(), self.expected_fields)
        for examination_data in response.data['second_examination_grades'] + response.data['difference_grades_sem1'] + response.data['difference_grades_sem2']:
            self.assertCountEqual(examination_data.keys(), self.examination_grade_fields)

        self.refresh_objects_from_db([self.catalog, self.catalog_per_year, self.study_class, self.study_class.academic_program,
                                      self.school_stats, self.teacher, self.teacher.school_unit])
        for catalog in [self.catalog, self.catalog_per_year]:
            self.assertIsNone(catalog.avg_annual)
            self.assertIsNone(catalog.avg_final)
        for obj in [self.study_class, self.study_class.academic_program, self.school_stats]:
            self.assertIsNone(obj.avg_annual)

        self.assertEqual(self.teacher.last_change_in_catalog, timezone.now())
        self.assertEqual(self.teacher.school_unit.last_change_in_catalog, timezone.now())
