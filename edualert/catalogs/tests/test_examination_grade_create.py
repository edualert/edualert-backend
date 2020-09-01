import datetime
from copy import copy
from decimal import Decimal
from unittest.mock import patch

from ddt import data, ddt, unpack
from django.urls import reverse
from django.utils import timezone
from pytz import utc
from rest_framework import status

from edualert.academic_calendars.factories import AcademicYearCalendarFactory, SchoolEventFactory
from edualert.academic_calendars.models import SchoolEvent
from edualert.catalogs.factories import StudentCatalogPerSubjectFactory, ExaminationGradeFactory, SubjectGradeFactory, StudentCatalogPerYearFactory
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
class ExaminationGradeCreateTestCase(CommonAPITestCase):
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
        self.refresh_objects_from_db([self.student, self.catalog])
        self.data = {
            'taken_at': date(2020, 8, 23),
            'grade1': 10,
            'grade2': 9,
            'examination_type': ExaminationGrade.ExaminationTypes.WRITTEN,
            'grade_type': ExaminationGrade.GradeTypes.SECOND_EXAMINATION,
        }

    @staticmethod
    def build_url(catalog_id):
        return reverse('catalogs:examination-grade-create', kwargs={'id': catalog_id})

    def test_examination_grade_create_unauthenticated(self):
        response = self.client.post(self.build_url(self.catalog.id), self.data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.PRINCIPAL,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_examination_grade_create_wrong_user_type(self, user_role):
        user = UserProfileFactory(
            user_role=user_role,
            school_unit=self.school_unit if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )
        self.client.login(username=user.username, password='passwd')

        response = self.client.post(self.build_url(self.catalog.id), self.data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_examination_grade_create_catalog_does_not_exist(self):
        self.client.login(username=self.teacher.username, password='passwd')
        response = self.client.post(self.build_url(0), self.data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_examination_grade_create_teacher_not_assigned(self):
        self.client.login(username=self.teacher.username, password='passwd')
        self.catalog.teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER)
        self.catalog.save()
        response = self.client.post(self.build_url(self.catalog.id), self.data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_examination_grade_create_is_not_enrolled(self):
        self.client.login(username=self.teacher.username, password='passwd')
        self.catalog.is_enrolled = False
        self.catalog.save()
        response = self.client.post(self.build_url(self.catalog.id), self.data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_examination_grade_create_is_not_active(self):
        self.client.login(username=self.teacher.username, password='passwd')
        self.student.is_active = False
        self.student.save()
        response = self.client.post(self.build_url(self.catalog.id), self.data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @data(
        'taken_at', 'grade1', 'grade2', 'examination_type', 'grade_type'
    )
    def test_examination_grade_create_grade_missing_required_field(self, field):
        self.client.login(username=self.teacher.username, password='passwd')
        del self.data[field]

        response = self.client.post(self.build_url(self.catalog.id), self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {field: ["This field is required."]})

    @data(
        (ExaminationGrade.GradeTypes.SECOND_EXAMINATION, timezone.datetime(2020, 8, 19).replace(tzinfo=utc)),
        (ExaminationGrade.GradeTypes.DIFFERENCE, timezone.datetime(2020, 9, 9).replace(tzinfo=utc)),
    )
    @unpack
    def test_examination_grade_create_grade_outside_event(self, grade_type, timezone_now):
        self.data['grade_type'] = grade_type

        with patch('django.utils.timezone.now', return_value=timezone_now) as mocked_method:
            self.client.login(username=self.teacher.username, password='passwd')
            response = self.client.post(self.build_url(self.catalog.id), self.data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'general_errors': ["Can't create grades at this time."]})

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 9, 2).replace(tzinfo=utc))
    def test_examination_grade_create_difference_with_regular_grades(self, mocked_method):
        self.client.login(username=self.teacher.username, password='passwd')
        SubjectGradeFactory(student=self.student, catalog_per_subject=self.catalog)

        self.data['grade_type'] = ExaminationGrade.GradeTypes.DIFFERENCE

        response = self.client.post(self.build_url(self.catalog.id), self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'general_errors': ["Can't add difference grades in catalogs where there are regular grades."]})

        self.data['semester'] = 1

        response = self.client.post(self.build_url(self.catalog.id), self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'general_errors': ["Can't add difference grades in semesters where there are regular grades."]})

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 8, 23).replace(tzinfo=utc))
    def test_examination_grade_create_grade_in_the_future(self, mocked_method):
        self.client.login(username=self.teacher.username, password='passwd')
        self.data['taken_at'] = date(2020, 8, 24)
        response = self.client.post(self.build_url(self.catalog.id), self.data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'taken_at': ["Can't add grades in the future."]})

    @data(
        (11, ['Grade must be between 1 and 10.']),
        (0, ['Grade must be between 1 and 10.']),
        (-1, ['Ensure this value is greater than or equal to 0.']),
        (None, ['This field may not be null.']),
        ('', ['A valid integer is required.']),
    )
    @unpack
    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 8, 23).replace(tzinfo=utc))
    def test_examination_grade_create_grade_validation(self, grade, expected_response, mocked_method):
        self.client.login(username=self.teacher.username, password='passwd')

        for grade_field in ['grade1', 'grade2']:
            request_data = copy(self.data)
            request_data[grade_field] = grade
            response = self.client.post(self.build_url(self.catalog.id), request_data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data[grade_field], expected_response)

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 8, 23).replace(tzinfo=utc))
    def test_examination_grade_create_semester_for_2nd_exam(self, mocked_method):
        self.client.login(username=self.teacher.username, password='passwd')
        self.data['semester'] = 1

        response = self.client.post(self.build_url(self.catalog.id), self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['semester'], ["This field can be added only to difference grades."])

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 8, 23).replace(tzinfo=utc))
    def test_examination_grade_create_2nd_exam_validations(self, mocked_method):
        self.client.login(username=self.teacher.username, password='passwd')
        ExaminationGradeFactory(catalog_per_subject=self.catalog, student=self.catalog.student, )

        response = self.client.post(self.build_url(self.catalog.id), self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['examination_type'], ["You already added a grade with this examination type."])

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 9, 7).replace(tzinfo=utc))
    def test_examination_grade_create_difference_validations(self, mocked_method):
        self.client.login(username=self.teacher.username, password='passwd')
        self.data['grade_type'] = ExaminationGrade.GradeTypes.DIFFERENCE
        self.data['taken_at'] = date(2020, 9, 7)
        diff_grade = ExaminationGradeFactory(catalog_per_subject=self.catalog, student=self.catalog.student, grade_type=ExaminationGrade.GradeTypes.DIFFERENCE, semester=1)

        response = self.client.post(self.build_url(self.catalog.id), self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['semester'], ["You cannot add difference grades for the whole year because "
                                                     "you have difference grades for a semester in this catalog."])

        diff_grade.semester = None
        diff_grade.save()

        response = self.client.post(self.build_url(self.catalog.id), self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['examination_type'], ["You already added a grade with this examination type."])

        self.data['semester'] = 1
        response = self.client.post(self.build_url(self.catalog.id), self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['semester'], ["You cannot add difference grades for a semester because "
                                                     "you have difference grades for the whole year in this catalog."])

        diff_grade.semester = 1
        diff_grade.save()

        response = self.client.post(self.build_url(self.catalog.id), self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['examination_type'], ["You already added a grade with this examination type."])

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 8, 23).replace(tzinfo=utc))
    def test_examination_grade_create_2nd_exam_success(self, mocked_method):
        self.client.login(username=self.teacher.username, password='passwd')
        self.catalog.avg_annual = 4
        self.catalog.save()

        response = self.client.post(self.build_url(self.catalog.id), self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.catalog.refresh_from_db()
        self.assertEqual(self.catalog.avg_annual, 4)
        self.assertEqual(self.catalog.avg_final, 4)
        self.assertIsNone(self.catalog.avg_after_2nd_examination)

        self.data['examination_type'] = ExaminationGrade.ExaminationTypes.ORAL
        response = self.client.post(self.build_url(self.catalog.id), self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertCountEqual(response.data.keys(), self.expected_fields)
        self.assertEqual(len(response.data['second_examination_grades']), 2)
        self.assertEqual(len(response.data['difference_grades_sem1']), 0)
        self.assertEqual(len(response.data['difference_grades_sem2']), 0)
        for examination_data in response.data['second_examination_grades'] + response.data['difference_grades_sem1'] + response.data['difference_grades_sem2']:
            self.assertCountEqual(examination_data.keys(), self.examination_grade_fields)

        self.refresh_objects_from_db([self.catalog, self.catalog_per_year, self.study_class, self.study_class.academic_program,
                                      self.school_stats, self.teacher, self.teacher.school_unit])
        for catalog in [self.catalog, self.catalog_per_year]:
            self.assertEqual(catalog.avg_annual, 4)
            self.assertEqual(catalog.avg_final, Decimal('9.5'))
        self.assertEqual(self.catalog.avg_after_2nd_examination, Decimal('9.5'))
        for obj in [self.study_class, self.study_class.academic_program, self.school_stats]:
            self.assertEqual(obj.avg_annual, Decimal('9.5'))

        self.assertEqual(self.teacher.last_change_in_catalog, timezone.now())
        self.assertEqual(self.teacher.school_unit.last_change_in_catalog, timezone.now())

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 9, 7).replace(tzinfo=utc))
    def test_examination_grade_create_differences_per_year_success(self, mocked_method):
        self.client.login(username=self.teacher.username, password='passwd')
        self.data['grade_type'] = ExaminationGrade.GradeTypes.DIFFERENCE
        self.data['taken_at'] = date(2020, 9, 7)

        response = self.client.post(self.build_url(self.catalog.id), self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.catalog.refresh_from_db()
        self.assertIsNone(self.catalog.avg_annual)
        self.assertIsNone(self.catalog.avg_final)

        self.data['examination_type'] = ExaminationGrade.ExaminationTypes.ORAL
        response = self.client.post(self.build_url(self.catalog.id), self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertCountEqual(response.data.keys(), self.expected_fields)
        self.assertEqual(len(response.data['second_examination_grades']), 0)
        self.assertEqual(len(response.data['difference_grades_sem1']), 0)
        self.assertEqual(len(response.data['difference_grades_sem2']), 2)
        for examination_data in response.data['second_examination_grades'] + response.data['difference_grades_sem1'] + response.data['difference_grades_sem2']:
            self.assertCountEqual(examination_data.keys(), self.examination_grade_fields)

        self.refresh_objects_from_db([self.catalog, self.catalog_per_year, self.study_class, self.study_class.academic_program,
                                      self.school_stats, self.teacher, self.teacher.school_unit])
        for catalog in [self.catalog, self.catalog_per_year]:
            self.assertEqual(catalog.avg_annual, Decimal('9.5'))
            self.assertEqual(catalog.avg_final, Decimal('9.5'))
        for obj in [self.study_class, self.study_class.academic_program, self.school_stats]:
            self.assertEqual(obj.avg_annual, Decimal('9.5'))

        self.assertEqual(self.teacher.last_change_in_catalog, timezone.now())
        self.assertEqual(self.teacher.school_unit.last_change_in_catalog, timezone.now())

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 9, 7).replace(tzinfo=utc))
    def test_examination_grade_create_differences_per_semester_success(self, mocked_method):
        self.client.login(username=self.teacher.username, password='passwd')
        self.data['grade_type'] = ExaminationGrade.GradeTypes.DIFFERENCE
        self.data['taken_at'] = date(2020, 9, 7)

        for examination_type in [ExaminationGrade.ExaminationTypes.WRITTEN, ExaminationGrade.ExaminationTypes.ORAL]:
            self.data['examination_type'] = examination_type
            for semester in [1, 2]:
                self.data['semester'] = semester
                response = self.client.post(self.build_url(self.catalog.id), self.data)
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertCountEqual(response.data.keys(), self.expected_fields)
        self.assertEqual(len(response.data['second_examination_grades']), 0)
        self.assertEqual(len(response.data['difference_grades_sem1']), 2)
        self.assertEqual(len(response.data['difference_grades_sem2']), 2)
        for examination_data in response.data['second_examination_grades'] + response.data['difference_grades_sem1'] + response.data['difference_grades_sem2']:
            self.assertCountEqual(examination_data.keys(), self.examination_grade_fields)

        self.refresh_objects_from_db([self.catalog, self.catalog_per_year, self.study_class, self.study_class.academic_program,
                                      self.school_stats, self.teacher, self.teacher.school_unit])
        for catalog in [self.catalog, self.catalog_per_year]:
            self.assertEqual(catalog.avg_sem1, 10)
            self.assertEqual(catalog.avg_sem2, 10)
            self.assertEqual(catalog.avg_annual, 10)
            self.assertEqual(catalog.avg_final, 10)
        for obj in [self.study_class, self.study_class.academic_program, self.school_stats]:
            self.assertEqual(obj.avg_annual, 10)

        self.assertEqual(self.teacher.last_change_in_catalog, timezone.now())
        self.assertEqual(self.teacher.school_unit.last_change_in_catalog, timezone.now())

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 9, 7).replace(tzinfo=utc))
    def test_examination_grade_create_differences_per_previous_year_success(self, mocked_method):
        self.client.login(username=self.teacher.username, password='passwd')
        study_class = StudyClassFactory(school_unit=self.school_unit, class_grade='IX', class_grade_arabic=9, academic_year=2019)
        catalog = StudentCatalogPerSubjectFactory(
            subject=self.subject,
            teacher=self.teacher,
            student=self.student,
            study_class=study_class
        )
        catalog_per_year = StudentCatalogPerYearFactory(
            student=self.student,
            study_class=study_class
        )
        school_stats = SchoolUnitStatsFactory(school_unit=self.school_unit, academic_year=2019)

        self.data['grade_type'] = ExaminationGrade.GradeTypes.DIFFERENCE
        self.data['taken_at'] = date(2020, 9, 7)

        response = self.client.post(self.build_url(catalog.id), self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.data['examination_type'] = ExaminationGrade.ExaminationTypes.ORAL
        response = self.client.post(self.build_url(catalog.id), self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(len(response.data['second_examination_grades']), 0)
        self.assertEqual(len(response.data['difference_grades_sem1']), 0)
        self.assertEqual(len(response.data['difference_grades_sem2']), 2)

        self.refresh_objects_from_db([catalog, catalog_per_year, study_class, study_class.academic_program,
                                      school_stats, self.teacher, self.teacher.school_unit])
        for catalog in [catalog, catalog_per_year]:
            self.assertEqual(catalog.avg_annual, Decimal('9.5'))
            self.assertEqual(catalog.avg_final, Decimal('9.5'))
        for obj in [study_class, study_class.academic_program, school_stats]:
            self.assertEqual(obj.avg_annual, Decimal('9.5'))

        self.assertEqual(self.teacher.last_change_in_catalog, timezone.now())
        self.assertEqual(self.teacher.school_unit.last_change_in_catalog, timezone.now())
