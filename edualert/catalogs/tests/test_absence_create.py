from unittest.mock import patch

from ddt import data, ddt
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from pytz import utc
from rest_framework import status

from edualert.academic_calendars.factories import AcademicYearCalendarFactory
from edualert.catalogs.factories import StudentCatalogPerSubjectFactory, StudentCatalogPerYearFactory
from edualert.catalogs.models import SubjectAbsence
from edualert.common.api_tests import CommonAPITestCase
from edualert.common.utils import date
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.statistics.factories import SchoolUnitStatsFactory
from edualert.study_classes.factories import StudyClassFactory, TeacherClassThroughFactory
from edualert.subjects.factories import SubjectFactory, ProgramSubjectThroughFactory


@ddt
class AbsenceCreateTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.calendar = AcademicYearCalendarFactory()
        cls.school_unit = RegisteredSchoolUnitFactory()
        cls.school_stats = SchoolUnitStatsFactory(school_unit=cls.school_unit)

        cls.teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=cls.school_unit)
        cls.study_class = StudyClassFactory(school_unit=cls.school_unit, class_master=cls.teacher)
        cls.subject = SubjectFactory()
        ProgramSubjectThroughFactory(academic_program=cls.study_class.academic_program, subject=cls.subject, weekly_hours_count=1,
                                     class_grade=cls.study_class.class_grade, class_grade_arabic=cls.study_class.class_grade_arabic)
        TeacherClassThroughFactory(teacher=cls.teacher, study_class=cls.study_class, is_class_master=True, subject=cls.subject)

        cls.student = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=cls.school_unit, student_in_class=cls.study_class)
        cls.catalog = StudentCatalogPerSubjectFactory(student=cls.student, study_class=cls.study_class, teacher=cls.teacher, subject=cls.subject)
        cls.catalog_per_year = StudentCatalogPerYearFactory(student=cls.student, study_class=cls.study_class)
        cls.expected_fields = ['id', 'student', 'avg_sem1', 'avg_sem2', 'avg_annual', 'avg_after_2nd_examination', 'abs_count_sem1', 'abs_count_sem2',
                               'abs_count_annual', 'avg_limit', 'founded_abs_count_sem1', 'founded_abs_count_sem2', 'founded_abs_count_annual', 'unfounded_abs_count_sem1',
                               'unfounded_abs_count_sem2', 'unfounded_abs_count_annual', 'grades_sem1', 'grades_sem2', 'second_examination_grades',
                               'difference_grades_sem1', 'difference_grades_sem2', 'abs_sem1', 'abs_sem2', 'wants_thesis', 'is_exempted',
                               'third_of_hours_count_sem1', 'third_of_hours_count_sem2', 'third_of_hours_count_annual', 'is_coordination_subject']

    def setUp(self):
        self.refresh_objects_from_db([self.student, self.study_class, self.study_class.academic_program, self.catalog_per_year])
        self.today = timezone.now().date()
        self.request_data = {
            "taken_at": self.today.strftime(settings.DATE_FORMAT),
            "is_founded": True
        }

    @staticmethod
    def build_url(catalog_id):
        return reverse('catalogs:add-absence', kwargs={'id': catalog_id})

    def test_create_absence_unauthenticated(self):
        response = self.client.post(self.build_url(self.catalog.id), data=self.request_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.PRINCIPAL,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_create_absence_wrong_user_type(self, user_role):
        user = UserProfileFactory(
            user_role=user_role,
            school_unit=self.school_unit if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )
        self.client.login(username=user.username, password='passwd')

        response = self.client.post(self.build_url(self.catalog.id), data=self.request_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_absence_catalog_not_existent(self):
        self.client.login(username=self.teacher.username, password='passwd')

        response = self.client.post(self.build_url(0), data=self.request_data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_absence_not_class_teacher(self):
        teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=self.school_unit)
        self.client.login(username=teacher.username, password='passwd')

        response = self.client.post(self.build_url(self.catalog.id), data=self.request_data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_absence_student_not_enrolled(self):
        self.client.login(username=self.teacher.username, password='passwd')
        catalog = StudentCatalogPerSubjectFactory(student=self.student, study_class=self.study_class, teacher=self.teacher, is_enrolled=False)

        response = self.client.post(self.build_url(catalog.id), data=self.request_data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_absence_student_inactive(self):
        self.client.login(username=self.teacher.username, password='passwd')
        self.student.is_active = False
        self.student.save()

        response = self.client.post(self.build_url(self.catalog.id), data=self.request_data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # def test_create_absence_no_calendar(self):
    #     self.client.login(username=self.teacher.username, password='passwd')
    #     self.calendar.delete()
    #
    #     response = self.client.post(self.build_url(self.catalog.id), data=self.request_data)
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertEqual(response.data['message'], "Can't add absences at this time.")
    #
    # @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 8, 5).replace(tzinfo=utc))
    # def test_create_absence_outside_semester(self, timezone_mock):
    #     self.client.login(username=self.teacher.username, password='passwd')
    #
    #     response = self.client.post(self.build_url(self.catalog.id), data=self.request_data)
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertEqual(response.data['message'], "Can't add absences at this time.")

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2019, 9, 20).replace(tzinfo=utc))
    def test_create_absence_future_date(self, timezone_mock):
        self.client.login(username=self.teacher.username, password='passwd')

        self.request_data['taken_at'] = date(2019, 9, 21)

        response = self.client.post(self.build_url(self.catalog.id), data=self.request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['taken_at'], ['The date cannot be in the future.'])

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 2, 1).replace(tzinfo=utc))
    def test_create_absence_wrong_semester(self, timezone_mock):
        self.client.login(username=self.teacher.username, password='passwd')

        self.request_data['taken_at'] = date(2019, 9, 21)

        response = self.client.post(self.build_url(self.catalog.id), data=self.request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['taken_at'], ['The date cannot be in the first semester.'])

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2019, 9, 20).replace(tzinfo=utc))
    def test_create_absence_first_semester_success(self, timezone_mock):
        self.client.login(username=self.teacher.username, password='passwd')

        self.request_data['taken_at'] = date(2019, 9, 20)

        response = self.client.post(self.build_url(self.catalog.id), data=self.request_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertCountEqual(response.data.keys(), self.expected_fields)

        absence = SubjectAbsence.objects.first()
        self.assertEqual(absence.catalog_per_subject, self.catalog)
        self.assertEqual(absence.student, self.student)
        self.assertEqual(absence.subject_name, self.subject.name)
        self.assertEqual(absence.semester, 1)
        self.assertTrue(absence.is_founded)

        self.refresh_objects_from_db([self.catalog, self.catalog_per_year, self.study_class,
                                      self.study_class.academic_program, self.teacher, self.school_unit, self.school_stats])
        for catalog in [self.catalog, self.catalog_per_year]:
            self.assertEqual(catalog.abs_count_sem1, 1)
            self.assertEqual(catalog.abs_count_sem2, 0)
            self.assertEqual(catalog.abs_count_annual, 1)
            self.assertEqual(catalog.founded_abs_count_sem1, 1)
            self.assertEqual(catalog.founded_abs_count_sem2, 0)
            self.assertEqual(catalog.founded_abs_count_annual, 1)
            self.assertEqual(catalog.unfounded_abs_count_sem1, 0)
            self.assertEqual(catalog.unfounded_abs_count_sem2, 0)
            self.assertEqual(catalog.unfounded_abs_count_annual, 0)
        for obj in [self.study_class, self.study_class.academic_program, self.school_stats]:
            self.assertEqual(obj.unfounded_abs_avg_sem1, 0)
            self.assertEqual(obj.unfounded_abs_avg_sem2, 0)
            self.assertEqual(obj.unfounded_abs_avg_annual, 0)

        self.assertEqual(self.teacher.last_change_in_catalog, timezone.now())
        self.assertEqual(self.school_unit.last_change_in_catalog, timezone.now())

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 5, 1).replace(tzinfo=utc))
    def test_create_absence_second_semester_success(self, timezone_mock):
        self.client.login(username=self.teacher.username, password='passwd')

        self.request_data['taken_at'] = date(2020, 4, 20)
        self.request_data['is_founded'] = False

        response = self.client.post(self.build_url(self.catalog.id), data=self.request_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertCountEqual(response.data.keys(), self.expected_fields)

        absence = SubjectAbsence.objects.first()
        self.assertEqual(absence.catalog_per_subject, self.catalog)
        self.assertEqual(absence.student, self.student)
        self.assertEqual(absence.subject_name, self.subject.name)
        self.assertEqual(absence.semester, 2)
        self.assertFalse(absence.is_founded)

        self.refresh_objects_from_db([self.catalog, self.catalog_per_year, self.study_class,
                                      self.study_class.academic_program, self.teacher, self.school_unit, self.school_stats])
        for catalog in [self.catalog, self.catalog_per_year]:
            self.assertEqual(catalog.abs_count_sem1, 0)
            self.assertEqual(catalog.abs_count_sem2, 1)
            self.assertEqual(catalog.abs_count_annual, 1)
            self.assertEqual(catalog.founded_abs_count_sem1, 0)
            self.assertEqual(catalog.founded_abs_count_sem2, 0)
            self.assertEqual(catalog.founded_abs_count_annual, 0)
            self.assertEqual(catalog.unfounded_abs_count_sem1, 0)
            self.assertEqual(catalog.unfounded_abs_count_sem2, 1)
            self.assertEqual(catalog.unfounded_abs_count_annual, 1)
        for obj in [self.study_class, self.study_class.academic_program, self.school_stats]:
            self.assertEqual(obj.unfounded_abs_avg_sem1, 0)
            self.assertEqual(obj.unfounded_abs_avg_sem2, 1)
            self.assertEqual(obj.unfounded_abs_avg_annual, 1)
