from unittest.mock import patch

from ddt import data, ddt
from django.urls import reverse
from django.utils import timezone
from pytz import utc
from rest_framework import status

from edualert.academic_calendars.factories import AcademicYearCalendarFactory
from edualert.catalogs.factories import StudentCatalogPerSubjectFactory, SubjectAbsenceFactory, StudentCatalogPerYearFactory
from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.statistics.factories import SchoolUnitStatsFactory
from edualert.study_classes.factories import StudyClassFactory, TeacherClassThroughFactory
from edualert.subjects.factories import SubjectFactory, ProgramSubjectThroughFactory


@ddt
class AbsenceAuthorizeTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.calendar = AcademicYearCalendarFactory()
        cls.school_unit = RegisteredSchoolUnitFactory()
        cls.school_stats = SchoolUnitStatsFactory(school_unit=cls.school_unit)

        cls.class_master = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=cls.school_unit)
        cls.study_class = StudyClassFactory(school_unit=cls.school_unit, class_master=cls.class_master)

        cls.subject = SubjectFactory()
        ProgramSubjectThroughFactory(academic_program=cls.study_class.academic_program, subject=cls.subject,
                                     weekly_hours_count=1, class_grade=cls.study_class.class_grade, class_grade_arabic=cls.study_class.class_grade_arabic)

        cls.student = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=cls.school_unit, student_in_class=cls.study_class)
        cls.teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=cls.school_unit)
        TeacherClassThroughFactory(teacher=cls.teacher, study_class=cls.study_class, is_class_master=False, subject=cls.subject)
        cls.catalog = StudentCatalogPerSubjectFactory(student=cls.student, study_class=cls.study_class, teacher=cls.teacher, subject=cls.subject,
                                                      abs_count_sem1=1, abs_count_annual=1, unfounded_abs_count_sem1=1, unfounded_abs_count_annual=1)
        cls.catalog_per_year = StudentCatalogPerYearFactory(student=cls.student, study_class=cls.study_class, abs_count_sem1=1, abs_count_annual=1,
                                                            unfounded_abs_count_sem1=1, unfounded_abs_count_annual=1)
        cls.absence = SubjectAbsenceFactory(student=cls.student, catalog_per_subject=cls.catalog)
        cls.expected_fields = ['id', 'student', 'avg_sem1', 'avg_sem2', 'avg_annual', 'avg_after_2nd_examination', 'abs_count_sem1', 'abs_count_sem2',
                               'abs_count_annual', 'founded_abs_count_sem1', 'founded_abs_count_sem2', 'founded_abs_count_annual', 'unfounded_abs_count_sem1',
                               'unfounded_abs_count_sem2', 'unfounded_abs_count_annual', 'grades_sem1', 'grades_sem2', 'second_examination_grades',
                               'difference_grades_sem1', 'difference_grades_sem2', 'abs_sem1', 'abs_sem2', 'wants_thesis', 'is_exempted', 'is_coordination_subject']

    def setUp(self):
        self.refresh_objects_from_db([self.study_class, self.study_class.academic_program, self.catalog_per_year, self.catalog, self.absence])

    @staticmethod
    def build_url(absence_id):
        return reverse('catalogs:authorize-absence', kwargs={'id': absence_id})

    def test_authorize_absence_unauthenticated(self):
        response = self.client.post(self.build_url(self.absence.id), data={})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.PRINCIPAL,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_authorize_absence_wrong_user_type(self, user_role):
        user = UserProfileFactory(
            user_role=user_role,
            school_unit=self.school_unit if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )
        self.client.login(username=user.username, password='passwd')

        response = self.client.post(self.build_url(self.absence.id), data={})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authorize_absence_not_found(self):
        self.client.login(username=self.teacher.username, password='passwd')

        response = self.client.post(self.build_url(0), data={})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_authorize_absence_not_class_teacher(self):
        teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=self.school_unit)
        self.client.login(username=teacher.username, password='passwd')

        response = self.client.post(self.build_url(self.absence.id), data={})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_authorize_absence_already_founded(self):
        self.client.login(username=self.teacher.username, password='passwd')
        absence = SubjectAbsenceFactory(student=self.student, catalog_per_subject=self.catalog, is_founded=True)

        response = self.client.post(self.build_url(absence.id), data={})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], "This absence is already authorized.")

    # def test_authorize_absence_no_calendar(self):
    #     self.client.login(username=self.teacher.username, password='passwd')
    #     self.calendar.delete()
    #
    #     response = self.client.post(self.build_url(self.absence.id), data={})
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertEqual(response.data['message'], "Can't authorize absences at this time.")
    #
    # @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 8, 5).replace(tzinfo=utc))
    # def test_authorize_absence_outside_semester(self, timezone_mock):
    #     self.client.login(username=self.teacher.username, password='passwd')
    #
    #     response = self.client.post(self.build_url(self.absence.id), data={})
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertEqual(response.data['message'], "Can't authorize absences at this time.")

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2019, 9, 20).replace(tzinfo=utc))
    def test_authorize_absence_8_days_ago_teacher(self, timezone_mock):
        self.client.login(username=self.teacher.username, password='passwd')

        self.absence.created = timezone.now() - timezone.timedelta(days=8)
        self.absence.save()

        response = self.client.post(self.build_url(self.absence.id), data={})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], "You can't authorize this absence anymore.")

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2019, 9, 20).replace(tzinfo=utc))
    def test_authorize_absence_8_days_ago_class_master(self, timezone_mock):
        self.client.login(username=self.class_master.username, password='passwd')

        self.absence.created = timezone.now() - timezone.timedelta(days=8)
        self.absence.save()

        response = self.client.post(self.build_url(self.absence.id), data={})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.refresh_objects_from_db([self.catalog, self.catalog_per_year, self.study_class,
                                      self.study_class.academic_program, self.school_stats])
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

    @data(
        'class_master', 'teacher'
    )
    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 3, 3).replace(tzinfo=utc))
    def test_authorize_absence_success(self, profile_param, timezone_mock):
        profile = getattr(self, profile_param)
        self.client.login(username=profile.username, password='passwd')

        absence = SubjectAbsenceFactory(student=self.student, catalog_per_subject=self.catalog, semester=2)
        self.catalog.abs_count_sem2 = 1
        self.catalog.abs_count_annual = 2
        self.catalog.unfounded_abs_count_sem2 = 1
        self.catalog.unfounded_abs_count_annual = 2
        self.catalog.save()

        response = self.client.post(self.build_url(absence.id), data={})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.refresh_objects_from_db([absence, self.catalog, self.catalog_per_year, self.study_class,
                                      self.study_class.academic_program, profile, self.school_unit, self.school_stats])
        self.assertTrue(absence.is_founded)
        for catalog in [self.catalog, self.catalog_per_year]:
            self.assertEqual(catalog.abs_count_sem1, 1)
            self.assertEqual(catalog.abs_count_sem2, 1)
            self.assertEqual(catalog.abs_count_annual, 2)
            self.assertEqual(catalog.founded_abs_count_sem1, 0)
            self.assertEqual(catalog.founded_abs_count_sem2, 1)
            self.assertEqual(catalog.founded_abs_count_annual, 1)
            self.assertEqual(catalog.unfounded_abs_count_sem1, 1)
            self.assertEqual(catalog.unfounded_abs_count_sem2, 0)
            self.assertEqual(catalog.unfounded_abs_count_annual, 1)
        for obj in [self.study_class, self.study_class.academic_program, self.school_stats]:
            self.assertEqual(obj.unfounded_abs_avg_sem1, 1)
            self.assertEqual(obj.unfounded_abs_avg_sem2, 0)
            self.assertEqual(obj.unfounded_abs_avg_annual, 1)

        self.assertEqual(profile.last_change_in_catalog, timezone.now())
        self.assertEqual(self.school_unit.last_change_in_catalog, timezone.now())
