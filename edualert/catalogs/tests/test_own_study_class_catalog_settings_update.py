import datetime
from unittest.mock import patch, call

from ddt import data, ddt
from django.urls import reverse
from pytz import utc
from rest_framework import status

from edualert.academic_calendars.factories import AcademicYearCalendarFactory
from edualert.catalogs.factories import StudentCatalogPerSubjectFactory, SubjectGradeFactory
from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.constants import EXEMPTED_SPORT_LABEL, EXEMPTED_RELIGION_LABEL, EXEMPTED_TITLE, EXEMPTED_BODY
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile, Label
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.study_classes.factories import StudyClassFactory, TeacherClassThroughFactory
from edualert.subjects.factories import SubjectFactory, ProgramSubjectThroughFactory


@ddt
class CatalogSettingsUpdateTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        AcademicYearCalendarFactory()
        cls.school_unit = RegisteredSchoolUnitFactory()
        cls.teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=cls.school_unit)
        cls.study_class = StudyClassFactory(school_unit=cls.school_unit, class_grade='IX', class_grade_arabic=9)
        cls.subject = SubjectFactory()
        ProgramSubjectThroughFactory(academic_program=cls.study_class.academic_program, subject=cls.subject, weekly_hours_count=1)

        cls.teacher_class_through = TeacherClassThroughFactory(
            study_class=cls.study_class,
            teacher=cls.teacher,
            subject=cls.subject
        )

        cls.student1 = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, student_in_class=cls.study_class)
        cls.catalog1 = StudentCatalogPerSubjectFactory(
            subject=cls.subject,
            teacher=cls.teacher,
            student=cls.student1,
            study_class=cls.study_class,
            avg_sem1=10,
            avg_sem2=10,
            avg_annual=10,
            avg_final=10
        )
        for semester in [1, 2]:
            for i in range(2):
                SubjectGradeFactory(student=cls.student1, catalog_per_subject=cls.catalog1, semester=semester)

        cls.student2 = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, student_in_class=cls.study_class)
        cls.catalog2 = StudentCatalogPerSubjectFactory(
            subject=cls.subject,
            teacher=cls.teacher,
            student=cls.student2,
            study_class=cls.study_class
        )

    def setUp(self):
        self.request_data = [
            {
                'id': self.catalog1.id,
                'wants_level_testing_grade': True,
                'wants_thesis': True,
                'wants_simulation': True
            },
            {
                'id': self.catalog2.id,
                'wants_level_testing_grade': False,
                'wants_thesis': False,
                'wants_simulation': False
            }
        ]

    @staticmethod
    def build_url(study_class_id, subject_id):
        return reverse('catalogs:catalog-settings', kwargs={'study_class_id': study_class_id, 'subject_id': subject_id})

    def test_catalog_settings_update_unauthenticated(self):
        response = self.client.put(self.build_url(self.study_class.id, self.subject.id), self.request_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.PRINCIPAL,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_catalog_settings_update_wrong_user_type(self, user_role):
        user = UserProfileFactory(
            user_role=user_role,
            school_unit=self.school_unit if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )
        self.client.login(username=user.username, password='passwd')

        response = self.client.put(self.build_url(self.study_class.id, self.subject.id), self.request_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_catalog_settings_update_study_class_does_not_exist(self):
        self.client.login(username=self.teacher.username, password='passwd')
        response = self.client.put(self.build_url(0, self.subject.id), self.request_data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_catalog_settings_update_subject_does_not_exist(self):
        self.client.login(username=self.teacher.username, password='passwd')
        response = self.client.put(self.build_url(self.study_class.id, 0), self.request_data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_catalog_settings_update_not_assigned_teacher(self):
        self.client.login(username=self.teacher.username, password='passwd')
        study_class = StudyClassFactory(school_unit=self.school_unit)

        response = self.client.put(self.build_url(study_class.id, self.subject.id), self.request_data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_catalog_settings_update_not_teaching_subject(self):
        self.client.login(username=self.teacher.username, password='passwd')

        response = self.client.put(self.build_url(self.study_class.id, SubjectFactory().id), self.request_data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @data(
        'id', 'wants_level_testing_grade', 'wants_thesis', 'wants_simulation'
    )
    def test_catalog_settings_update_missing_required_field(self, field):
        self.client.login(username=self.teacher.username, password='passwd')
        del self.request_data[0][field]

        response = self.client.put(self.build_url(self.study_class.id, self.subject.id), self.request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data[0][field], ['This field is required.'])

    def test_catalog_settings_update_catalog_does_not_exist(self):
        self.client.login(username=self.teacher.username, password='passwd')
        self.request_data[0]['id'] = 0

        response = self.client.put(self.build_url(self.study_class.id, self.subject.id), self.request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['general_errors'], ['Invalid pk "0" - object does not exist.'])

    def test_catalog_settings_update_no_exemption_allowed(self):
        self.client.login(username=self.teacher.username, password='passwd')
        self.request_data[0]['is_exempted'] = True

        response = self.client.put(self.build_url(self.study_class.id, self.subject.id), self.request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['is_exempted'], ["This subject doesn't allow exemption."])

    def test_catalog_settings_update_not_optional(self):
        self.client.login(username=self.teacher.username, password='passwd')
        self.request_data[0]['is_enrolled'] = False

        response = self.client.put(self.build_url(self.study_class.id, self.subject.id), self.request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['is_enrolled'], ["This subject is not optional."])

    def test_catalog_settings_update_success(self):
        self.client.login(username=self.teacher.username, password='passwd')

        response = self.client.put(self.build_url(self.study_class.id, self.subject.id), self.request_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        catalog_expected_fields = ['id', 'student', 'wants_level_testing_grade', 'wants_thesis',
                                   'wants_simulation', 'is_exempted', 'is_enrolled']
        student_expected_fields = ['id', 'full_name']

        for catalog_data in response.data:
            self.assertCountEqual(catalog_data.keys(), catalog_expected_fields)
            self.assertCountEqual(catalog_data['student'].keys(), student_expected_fields)

        self.refresh_objects_from_db([self.catalog1, self.catalog2])

        updated_fields = ['wants_level_testing_grade', 'wants_thesis', 'wants_simulation']
        for field in updated_fields:
            self.assertTrue(getattr(self.catalog1, field))
            self.assertFalse(getattr(self.catalog2, field))

    @patch('edualert.profiles.tasks.format_and_send_notification_task')
    def test_catalog_settings_update_exemption(self, send_notification_mock):
        self.client.login(username=self.teacher.username, password='passwd')

        # Religion

        self.subject.name = 'Religie'
        self.subject.allows_exemption = True
        self.subject.save()
        self.request_data[0]['is_exempted'] = True

        response = self.client.put(self.build_url(self.study_class.id, self.subject.id), self.request_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.catalog1.refresh_from_db()
        self.assertTrue(self.catalog1.is_exempted)
        self.assertCountEqual(self.student1.labels.all(), Label.objects.filter(text=EXEMPTED_RELIGION_LABEL))

        # Set is_exempted back to False
        self.request_data[0]['is_exempted'] = False

        response = self.client.put(self.build_url(self.study_class.id, self.subject.id), self.request_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.catalog1.refresh_from_db()
        self.assertFalse(self.catalog1.is_exempted)
        self.assertEqual(self.student1.labels.count(), 0)

        # Sport

        self.subject.name = 'Educație Fizică'
        self.subject.save()
        self.request_data[0]['is_exempted'] = True

        response = self.client.put(self.build_url(self.study_class.id, self.subject.id), self.request_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(self.student1.labels.all(), Label.objects.filter(text=EXEMPTED_SPORT_LABEL))

        # Set is_exempted back to False
        self.request_data[0]['is_exempted'] = False

        response = self.client.put(self.build_url(self.study_class.id, self.subject.id), self.request_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.student1.labels.count(), 0)

        self.assertEqual(send_notification_mock.call_count, 2)
        calls = [call(EXEMPTED_TITLE.format(self.student1.full_name),
                      EXEMPTED_BODY.format('Religie'),
                      [self.study_class.class_master_id], False),
                 call(EXEMPTED_TITLE.format(self.student1.full_name),
                      EXEMPTED_BODY.format('Educație Fizică'),
                      [self.study_class.class_master_id], False),
                 ]
        send_notification_mock.assert_has_calls(calls, any_order=True)

    def test_catalog_settings_update_enrollment(self):
        self.client.login(username=self.teacher.username, password='passwd')

        self.teacher_class_through.is_optional_subject = True
        self.teacher_class_through.save()
        self.request_data[0]['is_enrolled'] = False

        response = self.client.put(self.build_url(self.study_class.id, self.subject.id), self.request_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.catalog1.refresh_from_db()
        self.assertFalse(self.catalog1.is_enrolled)

    @patch('django.utils.timezone.now', return_value=datetime.datetime(2019, 10, 10).replace(tzinfo=utc))
    def test_catalog_settings_update_wants_thesis_first_semester(self, mocked_method):
        self.client.login(username=self.teacher.username, password='passwd')

        response = self.client.put(self.build_url(self.study_class.id, self.subject.id), self.request_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.catalog1.refresh_from_db()
        self.assertIsNone(self.catalog1.avg_sem1)

    @patch('django.utils.timezone.now', return_value=datetime.datetime(2020, 2, 10).replace(tzinfo=utc))
    def test_catalog_settings_update_wants_thesis_second_semester(self, mocked_method):
        self.client.login(username=self.teacher.username, password='passwd')

        response = self.client.put(self.build_url(self.study_class.id, self.subject.id), self.request_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.catalog1.refresh_from_db()
        self.assertIsNone(self.catalog1.avg_sem2)
        self.assertIsNone(self.catalog1.avg_annual)
        self.assertIsNone(self.catalog1.avg_final)
