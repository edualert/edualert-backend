from decimal import Decimal
from unittest.mock import patch

from ddt import data, ddt, unpack
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from pytz import utc
from rest_framework import status

from edualert.academic_calendars.factories import AcademicYearCalendarFactory
from edualert.catalogs.factories import StudentCatalogPerSubjectFactory, SubjectGradeFactory, StudentCatalogPerYearFactory
from edualert.catalogs.models import SubjectGrade
from edualert.common.api_tests import CommonAPITestCase
from edualert.common.utils import date
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.statistics.factories import SchoolUnitStatsFactory
from edualert.study_classes.factories import StudyClassFactory, TeacherClassThroughFactory
from edualert.subjects.factories import SubjectFactory, ProgramSubjectThroughFactory


@ddt
class GradeBulkCreateTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.calendar = AcademicYearCalendarFactory()
        cls.school_unit = RegisteredSchoolUnitFactory()
        cls.school_stats = SchoolUnitStatsFactory(school_unit=cls.school_unit)

        cls.teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=cls.school_unit)
        cls.study_class = StudyClassFactory(school_unit=cls.school_unit, class_master=cls.teacher)
        cls.subject = SubjectFactory()
        TeacherClassThroughFactory(teacher=cls.teacher, study_class=cls.study_class, is_class_master=True, subject=cls.subject)
        ProgramSubjectThroughFactory(academic_program=cls.study_class.academic_program, subject=cls.subject,
                                     weekly_hours_count=1, class_grade=cls.study_class.class_grade,
                                     class_grade_arabic=cls.study_class.class_grade_arabic)

        cls.student1 = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=cls.school_unit, student_in_class=cls.study_class)
        cls.catalog1 = StudentCatalogPerSubjectFactory(student=cls.student1, study_class=cls.study_class, teacher=cls.teacher, subject=cls.subject)
        cls.student2 = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=cls.school_unit, student_in_class=cls.study_class)
        cls.catalog2 = StudentCatalogPerSubjectFactory(student=cls.student2, study_class=cls.study_class, teacher=cls.teacher, subject=cls.subject)

        cls.catalog_per_year1 = StudentCatalogPerYearFactory(
            student=cls.student1,
            study_class=cls.study_class
        )
        cls.catalog_per_year2 = StudentCatalogPerYearFactory(
            student=cls.student2,
            study_class=cls.study_class
        )

        cls.expected_fields = [
            'id', 'student', 'avg_sem1', 'avg_sem2', 'avg_annual', 'avg_after_2nd_examination', 'avg_limit', 'abs_count_sem1', 'abs_count_sem2',
            'abs_count_annual', 'founded_abs_count_sem1', 'founded_abs_count_sem2', 'founded_abs_count_annual', 'unfounded_abs_count_sem1',
            'unfounded_abs_count_sem2', 'unfounded_abs_count_annual', 'grades_sem1', 'grades_sem2', 'abs_sem1', 'abs_sem2',
            'second_examination_grades', 'difference_grades_sem1', 'difference_grades_sem2', 'wants_thesis', 'is_exempted',
            'third_of_hours_count_sem1', 'third_of_hours_count_sem2', 'third_of_hours_count_annual', 'is_coordination_subject'
        ]

    def setUp(self):
        self.refresh_objects_from_db([self.catalog1, self.catalog2, self.catalog_per_year1, self.catalog_per_year2])
        self.today = timezone.now().date()
        self.request_data = {
            "taken_at": self.today.strftime(settings.DATE_FORMAT),
            "student_grades": [
                {
                    "student": self.student1.id,
                    "grade": 5
                },
                {
                    "student": self.student1.id,
                    "grade": 6
                },
                {
                    "student": self.student2.id,
                    "grade": 10
                }
            ]
        }

    @staticmethod
    def build_url(study_class_id, subject_id):
        return reverse('catalogs:add-grades-in-bulk', kwargs={'study_class_id': study_class_id, 'subject_id': subject_id})

    def test_bulk_create_grade_unauthenticated(self):
        response = self.client.post(self.build_url(self.study_class.id, self.subject.id), data=self.request_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.PRINCIPAL,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_bulk_create_grade_wrong_user_type(self, user_role):
        user = UserProfileFactory(
            user_role=user_role,
            school_unit=self.school_unit if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )
        self.client.login(username=user.username, password='passwd')

        response = self.client.post(self.build_url(self.study_class.id, self.subject.id), data=self.request_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_bulk_create_grade_no_study_class(self):
        self.client.login(username=self.teacher.username, password='passwd')

        response = self.client.post(self.build_url(0, self.subject.id), data=self.request_data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_bulk_create_grade_no_subject(self):
        self.client.login(username=self.teacher.username, password='passwd')

        response = self.client.post(self.build_url(self.study_class.id, 0), data=self.request_data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_bulk_create_grade_not_class_teacher(self):
        teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=self.school_unit)
        self.client.login(username=teacher.username, password='passwd')

        response = self.client.post(self.build_url(self.study_class.id, self.subject.id), data=self.request_data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_bulk_create_grade_not_teaching_subject(self):
        self.client.login(username=self.teacher.username, password='passwd')

        response = self.client.post(self.build_url(self.study_class.id, SubjectFactory().id), data=self.request_data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_bulk_create_grade_coordination_subject(self):
        self.client.login(username=self.teacher.username, password='passwd')
        subject = SubjectFactory(is_coordination=True)
        TeacherClassThroughFactory(teacher=self.teacher, study_class=self.study_class, is_class_master=True, subject=subject)

        response = self.client.post(self.build_url(self.study_class.id, subject.id), data=self.request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], "Can't add grades for coordination subject.")

    # def test_bulk_create_grade_no_calendar(self):
    #     self.client.login(username=self.teacher.username, password='passwd')
    #     self.calendar.delete()
    #
    #     response = self.client.post(self.build_url(self.study_class.id, self.subject.id), data=self.request_data)
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertEqual(response.data['message'], "Can't add grades at this time.")
    #
    # @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 8, 5).replace(tzinfo=utc))
    # def test_bulk_create_grade_outside_semester(self, timezone_mock):
    #     self.client.login(username=self.teacher.username, password='passwd')
    #
    #     response = self.client.post(self.build_url(self.study_class.id, self.subject.id), data=self.request_data)
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertEqual(response.data['message'], "Can't add grades at this time.")

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2019, 9, 20).replace(tzinfo=utc))
    def test_bulk_create_grade_future_date(self, timezone_mock):
        self.client.login(username=self.teacher.username, password='passwd')

        self.request_data['taken_at'] = date(2019, 9, 21)

        response = self.client.post(self.build_url(self.study_class.id, self.subject.id), data=self.request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['taken_at'], ['The date cannot be in the future.'])

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 2, 1).replace(tzinfo=utc))
    def test_bulk_create_grade_wrong_semester(self, timezone_mock):
        self.client.login(username=self.teacher.username, password='passwd')

        self.request_data['taken_at'] = date(2019, 9, 21)

        response = self.client.post(self.build_url(self.study_class.id, self.subject.id), data=self.request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['taken_at'], ['The date cannot be in the first semester.'])

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2019, 9, 20).replace(tzinfo=utc))
    def test_bulk_create_grade_validate_student(self, timezone_mock):
        self.client.login(username=self.teacher.username, password='passwd')

        self.request_data['taken_at'] = date(2019, 9, 20)
        self.request_data['student_grades'][0]['student'] = 0

        response = self.client.post(self.build_url(self.study_class.id, self.subject.id), data=self.request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['student_grades'][0]['student'], ['Invalid pk "0" - object does not exist.'])

        # Not student in class
        student1 = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=self.school_unit)
        # Not enrolled
        student2 = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=self.school_unit, student_in_class=self.study_class)
        StudentCatalogPerSubjectFactory(student=student2, study_class=self.study_class, teacher=self.teacher, subject=self.subject, is_enrolled=False)
        # Not active
        student3 = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=self.school_unit,
                                      student_in_class=self.study_class, is_active=False)
        StudentCatalogPerSubjectFactory(student=student3, study_class=self.study_class, teacher=self.teacher, subject=self.subject)

        for student in [student1, student2, student3]:
            self.request_data['student_grades'][0]['student'] = student.id

            response = self.client.post(self.build_url(self.study_class.id, self.subject.id), data=self.request_data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data['student'], [f'Invalid pk "{student.id}" - object does not exist.'])

        # Exempted
        student = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=self.school_unit, student_in_class=self.study_class)
        StudentCatalogPerSubjectFactory(student=student, study_class=self.study_class, teacher=self.teacher, subject=self.subject, is_exempted=True)
        self.request_data['student_grades'][0]['student'] = student.id

        response = self.client.post(self.build_url(self.study_class.id, self.subject.id), data=self.request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['student'], [f'Invalid pk "{student.id}" - student is exempted and cannot have grades.'])

    @data(
        (11, {'grade': ['Grade must be between 1 and 10.']}),
        (0, {'grade': ['Grade must be between 1 and 10.']}),
        (-1, {'grade': ['Ensure this value is greater than or equal to 0.']}),
        (None, {'grade': ['This field may not be null.']}),
        ('', {'grade': ['A valid integer is required.']}),
    )
    @unpack
    @patch('django.utils.timezone.now', return_value=timezone.datetime(2019, 9, 20).replace(tzinfo=utc))
    def test_bulk_create_grade_validate_grade(self, grade, expected_error, mocked_method):
        self.client.login(username=self.teacher.username, password='passwd')
        self.request_data['student_grades'][0]['grade'] = grade
        response = self.client.post(self.build_url(self.study_class.id, self.subject.id), self.request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'student_grades': [expected_error, {}, {}]})

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2019, 9, 20).replace(tzinfo=utc))
    def test_bulk_create_grade_first_semester_success(self, timezone_mock):
        self.client.login(username=self.teacher.username, password='passwd')
        self.request_data['taken_at'] = date(2019, 9, 20)

        response = self.client.post(self.build_url(self.study_class.id, self.subject.id), data=self.request_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertCountEqual(response.data.keys(), ['catalogs'])
        for catalogs in response.data['catalogs']:
            self.assertCountEqual(catalogs.keys(), self.expected_fields)

        self.check_data(1)

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 5, 1).replace(tzinfo=utc))
    def test_bulk_create_grade_second_semester_success(self, timezone_mock):
        self.client.login(username=self.teacher.username, password='passwd')
        self.request_data['taken_at'] = date(2020, 4, 20)

        response = self.client.post(self.build_url(self.study_class.id, self.subject.id), data=self.request_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertCountEqual(response.data.keys(), ['catalogs'])
        for catalogs in response.data['catalogs']:
            self.assertCountEqual(catalogs.keys(), self.expected_fields)

        self.check_data(2)

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2019, 9, 20).replace(tzinfo=utc))
    def test_bulk_create_grade_secondary_school_averages(self, timezone_mock):
        # This is for a subject with weekly hours count = 1 and no thesis (1st semester)
        self.client.login(username=self.teacher.username, password='passwd')
        self.request_data['taken_at'] = date(2019, 9, 20)

        response = self.client.post(self.build_url(self.study_class.id, self.subject.id), data=self.request_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.refresh_objects_from_db([self.catalog1, self.catalog2, self.catalog_per_year1, self.catalog_per_year2,
                                      self.study_class, self.school_stats])
        for catalog in [self.catalog1, self.catalog_per_year1]:
            self.assertEqual(catalog.avg_sem1, 6)
            self.assertIsNone(catalog.avg_sem2)
            self.assertIsNone(catalog.avg_annual)
            self.assertIsNone(catalog.avg_final)
        for catalog in [self.catalog2, self.catalog_per_year2]:
            self.assertIsNone(catalog.avg_sem1)
            self.assertIsNone(catalog.avg_sem2)
            self.assertIsNone(catalog.avg_annual)
            self.assertIsNone(catalog.avg_final)
        for obj in [self.study_class, self.school_stats]:
            self.assertEqual(obj.avg_sem1, 6)
            self.assertIsNone(obj.avg_sem2)
            self.assertIsNone(obj.avg_annual)

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 4, 5).replace(tzinfo=utc))
    def test_bulk_create_grade_highschool_averages(self, timezone_mock):
        # This is for a required subject with weekly hours count = 3 and with thesis (2nd semester)
        self.study_class.class_grade = 'IX'
        self.study_class.class_grade_arabic = 9
        self.study_class.save()
        ProgramSubjectThroughFactory(generic_academic_program=self.study_class.academic_program.generic_academic_program, subject=self.subject,
                                     weekly_hours_count=3)
        for catalog in [self.catalog1, self.catalog2]:
            catalog.avg_sem1 = 10
            catalog.wants_thesis = True
            catalog.save()
        SubjectGradeFactory(student=self.student1, catalog_per_subject=self.catalog1, semester=2, grade=10, grade_type=SubjectGrade.GradeTypes.THESIS)
        SubjectGradeFactory(student=self.student2, catalog_per_subject=self.catalog2, semester=2, grade=10, grade_type=SubjectGrade.GradeTypes.THESIS)

        self.client.login(username=self.teacher.username, password='passwd')
        self.request_data = {
            "taken_at": date(2020, 4, 5),
            "student_grades": [
                {
                    "student": self.student1.id,
                    "grade": 10
                },
                {
                    "student": self.student1.id,
                    "grade": 9
                },
                {
                    "student": self.student1.id,
                    "grade": 9
                },
                {
                    "student": self.student2.id,
                    "grade": 10
                }
            ]
        }

        response = self.client.post(self.build_url(self.study_class.id, self.subject.id), data=self.request_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.refresh_objects_from_db([self.catalog1, self.catalog2, self.catalog_per_year1, self.catalog_per_year2,
                                      self.study_class, self.study_class.academic_program, self.school_stats])
        for catalog in [self.catalog1, self.catalog_per_year1]:
            self.assertEqual(catalog.avg_sem1, 10)
            # This is a 9.49 situation
            self.assertEqual(catalog.avg_sem2, 9)
            self.assertEqual(catalog.avg_annual, 9.5)
            self.assertEqual(catalog.avg_final, 9.5)
        for catalog in [self.catalog2, self.catalog_per_year2]:
            self.assertEqual(catalog.avg_sem1, 10)
            self.assertIsNone(catalog.avg_sem2)
            self.assertIsNone(catalog.avg_annual)
            self.assertIsNone(catalog.avg_final)
        for obj in [self.study_class, self.study_class.academic_program, self.school_stats]:
            self.assertEqual(obj.avg_sem1, Decimal('10'))
            self.assertEqual(obj.avg_sem2, Decimal('9'))
            self.assertEqual(obj.avg_annual, Decimal('9.5'))

    def check_data(self, semester):
        grades = SubjectGrade.objects.filter(student=self.student1)
        self.assertEqual(len(grades), 2)
        for grade in grades:
            self.assertEqual(grade.catalog_per_subject, self.catalog1)
            self.assertEqual(grade.subject_name, self.subject.name)
            self.assertEqual(grade.semester, semester)

        grades = SubjectGrade.objects.filter(student=self.student2)
        self.assertEqual(len(grades), 1)
        grade = grades.first()
        self.assertEqual(grade.catalog_per_subject, self.catalog2)
        self.assertEqual(grade.subject_name, self.subject.name)
        self.assertEqual(grade.semester, semester)

        self.refresh_objects_from_db([self.teacher, self.school_unit])
        self.assertIsNotNone(self.teacher.last_change_in_catalog)
        self.assertIsNotNone(self.school_unit.last_change_in_catalog)
