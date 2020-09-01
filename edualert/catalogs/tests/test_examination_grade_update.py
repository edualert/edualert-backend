import datetime
from copy import copy
from unittest.mock import patch

from ddt import data, ddt, unpack
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from pytz import utc
from rest_framework import status

from edualert.academic_calendars.factories import AcademicYearCalendarFactory, SchoolEventFactory
from edualert.academic_calendars.models import SchoolEvent
from edualert.catalogs.factories import StudentCatalogPerSubjectFactory, ExaminationGradeFactory, StudentCatalogPerYearFactory
from edualert.catalogs.models import ExaminationGrade
from edualert.common.api_tests import CommonAPITestCase
from edualert.common.utils import date
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.statistics.factories import SchoolUnitStatsFactory
from edualert.study_classes.factories import StudyClassFactory, TeacherClassThroughFactory
from edualert.subjects.factories import SubjectFactory, ProgramSubjectThroughFactory


@ddt
class ExaminationGradeUpdateTestCase(CommonAPITestCase):
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

        cls.teacher_class_through = TeacherClassThroughFactory(
            study_class=cls.study_class,
            teacher=cls.teacher,
            subject=cls.subject
        )
        cls.student = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, student_in_class=cls.study_class)
        cls.catalog = StudentCatalogPerSubjectFactory(
            subject=cls.subject,
            teacher=cls.teacher,
            student=cls.student,
            study_class=cls.study_class,
            is_enrolled=True
        )
        cls.catalog_per_year = StudentCatalogPerYearFactory(
            student=cls.student,
            study_class=cls.study_class
        )

    def setUp(self):
        self.catalog.refresh_from_db()
        self.data = {
            'grade1': 8,
            'grade2': 8,
            'taken_at': date(2020, 8, 21)
        }

    def create_2nd_exam_grade(self, examination_type=ExaminationGrade.ExaminationTypes.WRITTEN):
        return ExaminationGradeFactory(
            catalog_per_subject=self.catalog,
            student=self.catalog.student,
            examination_type=examination_type,
            taken_at=datetime.date(2020, 8, 22))

    def create_difference_grade(self, examination_type=ExaminationGrade.ExaminationTypes.WRITTEN):
        return ExaminationGradeFactory(
            catalog_per_subject=self.catalog,
            student=self.catalog.student,
            examination_type=examination_type,
            taken_at=datetime.date(2020, 9, 2),
            grade_type=ExaminationGrade.GradeTypes.DIFFERENCE)

    @staticmethod
    def build_url(grade_id):
        return reverse('catalogs:examination-grade-detail', kwargs={'id': grade_id})

    def test_examination_grade_update_unauthenticated(self):
        response = self.client.put(self.build_url(self.create_2nd_exam_grade().id), self.data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.PRINCIPAL,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_examination_grade_update_wrong_user_type(self, user_role):
        user = UserProfileFactory(
            user_role=user_role,
            school_unit=self.school_unit if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )
        self.client.login(username=user.username, password='passwd')

        response = self.client.put(self.build_url(self.create_2nd_exam_grade().id), self.data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_examination_grade_update_catalog_does_not_exist(self):
        self.client.login(username=self.teacher.username, password='passwd')
        response = self.client.put(self.build_url(0), self.data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_examination_grade_update_teacher_not_assigned(self):
        self.client.login(username=self.teacher.username, password='passwd')
        self.catalog.teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER)
        self.catalog.save()
        response = self.client.put(self.build_url(self.create_2nd_exam_grade().id), self.data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @data(
        datetime.datetime(2020, 8, 22, 8, 59, 59),
        datetime.datetime(2020, 8, 21, 22, 59)
    )
    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 8, 22, 12, 0, 0).replace(tzinfo=utc))
    def test_examination_grade_update_grade_more_than_two_hours_in_the_past(self, created_at, mocked_method):
        self.client.login(username=self.teacher.username, password='passwd')
        grade = self.create_2nd_exam_grade()
        grade.created = created_at.replace(tzinfo=utc)
        grade.save()

        response = self.client.put(self.build_url(grade.id), self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'message': 'Cannot update a grade that was created more than 2 hours ago.'})

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 8, 30).replace(tzinfo=utc))
    def test_examination_grade_update_outside_event(self, mocked_method):
        self.client.login(username=self.teacher.username, password='passwd')

        response = self.client.put(self.build_url(self.create_2nd_exam_grade().id), self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'message': 'Cannot update grades at this time.'})

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 8, 22).replace(tzinfo=utc))
    def test_examination_grade_update_grade_in_the_future(self, mocked_method):
        self.client.login(username=self.teacher.username, password='passwd')
        self.data['taken_at'] = date(2020, 8, 23)

        response = self.client.put(self.build_url(self.create_2nd_exam_grade().id), self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'taken_at': ["Can't set grade dates in the future."]})

    @data(
        (11, ['Grade must be between 1 and 10.']),
        (0, ['Grade must be between 1 and 10.']),
        (-1, ['Ensure this value is greater than or equal to 0.']),
        (None, ['This field may not be null.']),
        ('', ['A valid integer is required.']),
    )
    @unpack
    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 8, 22).replace(tzinfo=utc))
    def test_examination_grade_update_grade_validation(self, grade, expected_response, mocked_method):
        self.client.login(username=self.teacher.username, password='passwd')

        for grade_field in ['grade1', 'grade2']:
            request_data = copy(self.data)
            request_data[grade_field] = grade
            response = self.client.put(self.build_url(self.create_2nd_exam_grade().id), request_data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data[grade_field], expected_response)

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 8, 22).replace(tzinfo=utc))
    def test_examination_grade_update_2nd_exam_grade_success(self, mocked_method):
        self.client.login(username=self.teacher.username, password='passwd')
        for catalog in [self.catalog, self.catalog_per_year]:
            catalog.avg_annual = 5
            catalog.save()

        self.create_2nd_exam_grade()
        grade = self.create_2nd_exam_grade(examination_type=ExaminationGrade.ExaminationTypes.ORAL)

        response = self.client.put(self.build_url(grade.id), self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.check_data(response, grade)

        self.refresh_objects_from_db([self.catalog, self.catalog_per_year, self.study_class, self.study_class.academic_program,
                                      self.school_stats, self.teacher, self.teacher.school_unit])
        for catalog in [self.catalog, self.catalog_per_year]:
            self.assertEqual(catalog.avg_annual, 5)
            self.assertEqual(catalog.avg_final, 9)
        self.assertEqual(self.catalog.avg_after_2nd_examination, 9)
        for obj in [self.study_class, self.study_class.academic_program, self.school_stats]:
            self.assertEqual(obj.avg_annual, 9)

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 9, 3).replace(tzinfo=utc))
    def test_examination_grade_update_difference_grade_success(self, mocked_method):
        self.client.login(username=self.teacher.username, password='passwd')
        self.create_difference_grade()
        grade = self.create_difference_grade(examination_type=ExaminationGrade.ExaminationTypes.ORAL)
        self.data['taken_at'] = date(2020, 9, 3)

        response = self.client.put(self.build_url(grade.id), self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.check_data(response, grade)

        self.refresh_objects_from_db([self.catalog, self.catalog_per_year, self.study_class, self.study_class.academic_program,
                                      self.school_stats, self.teacher, self.teacher.school_unit])
        for catalog in [self.catalog, self.catalog_per_year]:
            self.assertEqual(catalog.avg_annual, 9)
            self.assertEqual(catalog.avg_final, 9)
        for obj in [self.study_class, self.study_class.academic_program, self.school_stats]:
            self.assertEqual(obj.avg_annual, 9)

    def check_data(self, response, grade):
        catalog_expected_fields = [
            'id', 'student', 'avg_sem1', 'avg_sem2', 'avg_annual', 'avg_after_2nd_examination', 'avg_limit', 'abs_count_sem1', 'abs_count_sem2',
            'abs_count_annual', 'founded_abs_count_sem1', 'founded_abs_count_sem2', 'founded_abs_count_annual', 'unfounded_abs_count_sem1',
            'unfounded_abs_count_sem2', 'unfounded_abs_count_annual', 'grades_sem1', 'grades_sem2', 'abs_sem1', 'abs_sem2',
            'second_examination_grades', 'difference_grades_sem1', 'difference_grades_sem2', 'wants_thesis', 'is_exempted',
            'third_of_hours_count_sem1', 'third_of_hours_count_sem2', 'third_of_hours_count_annual', 'is_coordination_subject'
        ]
        examination_grade_fields = ['id', 'examination_type', 'taken_at', 'grade1', 'grade2', 'created']
        self.assertCountEqual(response.data.keys(), catalog_expected_fields)
        for examination_data in response.data['second_examination_grades'] + response.data['difference_grades_sem1'] + response.data['difference_grades_sem2']:
            self.assertCountEqual(examination_data.keys(), examination_grade_fields)

        grade.refresh_from_db()
        self.assertEqual(grade.grade1, self.data['grade1'])
        self.assertEqual(grade.grade2, self.data['grade2'])
        self.assertEqual(grade.taken_at.strftime(settings.DATE_FORMAT), self.data['taken_at'])

        self.teacher.refresh_from_db()
        self.assertEqual(self.teacher.last_change_in_catalog, timezone.now())
        self.assertEqual(self.teacher.school_unit.last_change_in_catalog, timezone.now())
