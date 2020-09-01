import datetime
from dateutil import tz
from ddt import ddt, data, unpack
from unittest.mock import patch

from django.urls import reverse
from rest_framework import status

from edualert.academic_calendars.factories import AcademicYearCalendarFactory
from edualert.academic_programs.factories import AcademicProgramFactory
from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.study_classes.factories import StudyClassFactory


@ddt
class StudyClassDeleteTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.principal = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL)
        cls.school_unit = RegisteredSchoolUnitFactory(school_principal=cls.principal)
        cls.calendar = AcademicYearCalendarFactory()
        cls.study_class = StudyClassFactory(school_unit=cls.school_unit, class_grade='V', class_grade_arabic=5)

    @staticmethod
    def build_url(study_class_id):
        return reverse('study_classes:study-class-detail', kwargs={'id': study_class_id})

    def test_study_class_delete_unauthenticated(self):
        response = self.client.delete(self.build_url(self.study_class.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.TEACHER,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_study_class_delete_wrong_user_type(self, user_role):
        if user_role == UserProfile.UserRoles.ADMINISTRATOR:
            user = UserProfileFactory(user_role=user_role)
        else:
            user = UserProfileFactory(user_role=user_role, school_unit=self.school_unit)
        self.client.login(username=user.username, password='passwd')

        response = self.client.delete(self.build_url(self.study_class.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_study_class_delete_not_found(self):
        self.client.login(username=self.principal.username, password='passwd')

        response = self.client.delete(self.build_url(0))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_study_class_delete_another_school_unit(self):
        self.client.login(username=self.principal.username, password='passwd')
        study_class2 = StudyClassFactory(class_grade='V', class_grade_arabic=5)

        response = self.client.delete(self.build_url(study_class2.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_study_class_delete_no_calendar(self):
        self.client.login(username=self.principal.username, password='passwd')
        self.calendar.delete()

        response = self.client.delete(self.build_url(self.study_class.id))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], 'No academic calendar defined.')

    def test_study_class_delete_different_year(self):
        self.client.login(username=self.principal.username, password='passwd')
        self.study_class.academic_year = 2018
        self.study_class.save()

        response = self.client.delete(self.build_url(self.study_class.id))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], 'Cannot delete a study class from a previous year.')

    # @patch('django.utils.timezone.now')
    # def test_study_class_delete_after_15_september(self, timezone_mock):
    #     timezone_mock.return_value = datetime.datetime(self.calendar.academic_year, 9, 16, tzinfo=tz.UTC)
    #     self.client.login(username=self.principal.username, password='passwd')
    #
    #     response = self.client.delete(self.build_url(self.study_class.id))
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertEqual(response.data['message'], 'Cannot delete the study class.')

    @patch('django.utils.timezone.now')
    def test_study_class_delete_class_with_data(self, timezone_mock):
        timezone_mock.return_value = datetime.datetime(self.calendar.academic_year, 9, 14, tzinfo=tz.UTC)
        self.client.login(username=self.principal.username, password='passwd')

        StudyClassFactory(school_unit=self.school_unit, class_grade='P', class_grade_arabic=0, academic_year=self.calendar.academic_year - 1)
        study_class = StudyClassFactory(school_unit=self.school_unit, class_grade='I', class_grade_arabic=1)
        response = self.client.delete(self.build_url(study_class.id))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], 'Cannot delete the study class.')

    @data(
        ('P', 0),
        ('I', 1),
        ('V', 5),
        ('IX', 9),
        ('X', 10),
    )
    @unpack
    @patch('django.utils.timezone.now')
    def test_study_class_delete_success(self, class_grade, class_grade_arabic, timezone_mock):
        timezone_mock.return_value = datetime.datetime(self.calendar.academic_year, 9, 14, tzinfo=tz.UTC)
        self.client.login(username=self.principal.username, password='passwd')

        academic_program = None
        academic_program_name = None
        if class_grade_arabic >= 9:
            academic_program = AcademicProgramFactory(school_unit=self.school_unit)
            academic_program_name = academic_program.name
        study_class = StudyClassFactory(school_unit=self.school_unit, academic_program=academic_program,
                                        academic_program_name=academic_program_name,
                                        class_grade=class_grade, class_grade_arabic=class_grade_arabic)

        response = self.client.delete(self.build_url(study_class.id))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
