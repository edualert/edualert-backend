from datetime import datetime, date
from unittest.mock import patch, call

from pytz import utc

from edualert.academic_calendars.factories import AcademicYearCalendarFactory, SchoolEventFactory
from edualert.academic_calendars.models import SchoolEvent
from edualert.catalogs.constants import AVG_BELOW_7_TITLE, AVG_BELOW_7_BODY, AVG_BELOW_LIMIT_TITLE, AVG_BELOW_LIMIT_BODY, \
    BEHAVIOR_GRADE_BELOW_10_TITLE, BEHAVIOR_GRADE_BELOW_10_BODY, BEHAVIOR_GRADE_BELOW_8_TITLE, BEHAVIOR_GRADE_BELOW_8_BODY, \
    ABSENCES_BETWEEN_1_3_TITLE, ABSENCES_BETWEEN_1_3_BODY, ABSENCES_ABOVE_3_TITLE, ABSENCES_ABOVE_3_BODY, \
    ABSENCES_ABOVE_LIMIT_TITLE, ABSENCES_ABOVE_LIMIT_BODY
from edualert.catalogs.factories import StudentCatalogPerYearFactory, StudentCatalogPerSubjectFactory, SubjectAbsenceFactory
from edualert.catalogs.utils import send_alerts_for_risks
from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory, SchoolUnitCategoryFactory
from edualert.study_classes.factories import StudyClassFactory
from edualert.subjects.factories import SubjectFactory


class SendAlertsForRisksTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.calendar = AcademicYearCalendarFactory(
            first_semester__starts_at=datetime(2019, 9, 9),
            first_semester__ends_at=datetime(2020, 1, 12),
            second_semester__starts_at=datetime(2020, 1, 13),
            second_semester__ends_at=datetime(2020, 6, 12)
        )
        cls.create_semester_end_events(cls.calendar)
        cls.subject = SubjectFactory(name='Matematică')
        coordination_subject = SubjectFactory(is_coordination=True)

        cls.school1 = RegisteredSchoolUnitFactory()

        cls.study_class1 = StudyClassFactory(school_unit=cls.school1)

        # 1 unauthorized absence (both sem) + average below 5 (sem I) + average below 7 (sem II) + behavior grade below 8 (sem I) + behavior grade below 10 (sem II)
        cls.student1 = UserProfileFactory(school_unit=cls.school1, user_role=UserProfile.UserRoles.STUDENT, student_in_class=cls.study_class1)
        cls.parent1 = UserProfileFactory(school_unit=cls.school1, user_role=UserProfile.UserRoles.PARENT)
        cls.student1.parents.add(cls.parent1)
        StudentCatalogPerYearFactory(student=cls.student1, study_class=cls.study_class1)
        cls.catalog1 = StudentCatalogPerSubjectFactory(student=cls.student1, study_class=cls.study_class1, subject=cls.subject, avg_sem1=4, avg_final=6)
        SubjectAbsenceFactory(catalog_per_subject=cls.catalog1, student=cls.student1, semester=1)
        SubjectAbsenceFactory(catalog_per_subject=cls.catalog1, student=cls.student1, semester=2)
        StudentCatalogPerSubjectFactory(student=cls.student1, study_class=cls.study_class1, subject=coordination_subject, avg_sem1=7, avg_final=9)

        cls.study_class2 = StudyClassFactory(school_unit=cls.school1, class_grade='XII', class_grade_arabic=12)

        # 4 unauthorized absences (both sem)
        cls.student2 = UserProfileFactory(school_unit=cls.school1, user_role=UserProfile.UserRoles.STUDENT, student_in_class=cls.study_class2)
        StudentCatalogPerYearFactory(student=cls.student2, study_class=cls.study_class2)
        cls.catalog2 = StudentCatalogPerSubjectFactory(student=cls.student2, study_class=cls.study_class2, subject=cls.subject)
        for _ in range(4):
            SubjectAbsenceFactory(catalog_per_subject=cls.catalog2, student=cls.student2, semester=1)
            SubjectAbsenceFactory(catalog_per_subject=cls.catalog2, student=cls.student2, semester=2)
        # 14 unauthorized absences (both sem)
        cls.student3 = UserProfileFactory(school_unit=cls.school1, user_role=UserProfile.UserRoles.STUDENT, student_in_class=cls.study_class2)
        StudentCatalogPerYearFactory(student=cls.student3, study_class=cls.study_class2)
        cls.catalog3 = StudentCatalogPerSubjectFactory(student=cls.student3, study_class=cls.study_class2, subject=cls.subject)
        for _ in range(14):
            SubjectAbsenceFactory(catalog_per_subject=cls.catalog3, student=cls.student3, semester=1)
            SubjectAbsenceFactory(catalog_per_subject=cls.catalog3, student=cls.student3, semester=2)

        cls.school2 = RegisteredSchoolUnitFactory()
        cls.school2.categories.add(SchoolUnitCategoryFactory(name='Liceu - Filieră Tehnologică'))

        cls.study_class3 = StudyClassFactory(school_unit=cls.school2, class_grade='VIII', class_grade_arabic=8)

        # 24 unauthorized absences (both sem)
        cls.student4 = UserProfileFactory(school_unit=cls.school2, user_role=UserProfile.UserRoles.STUDENT, student_in_class=cls.study_class3)
        StudentCatalogPerYearFactory(student=cls.student4, study_class=cls.study_class3)
        cls.catalog4 = StudentCatalogPerSubjectFactory(student=cls.student4, study_class=cls.study_class3, subject=cls.subject)
        for _ in range(24):
            SubjectAbsenceFactory(catalog_per_subject=cls.catalog4, student=cls.student4, semester=1)
            SubjectAbsenceFactory(catalog_per_subject=cls.catalog4, student=cls.student4, semester=2)

        cls.study_class4 = StudyClassFactory(school_unit=cls.school2, class_grade='IX', class_grade_arabic=9)

        # 34 unauthorized absences (both sem)
        cls.student5 = UserProfileFactory(school_unit=cls.school2, user_role=UserProfile.UserRoles.STUDENT, student_in_class=cls.study_class4)
        StudentCatalogPerYearFactory(student=cls.student5, study_class=cls.study_class4)
        cls.catalog5 = StudentCatalogPerSubjectFactory(student=cls.student5, study_class=cls.study_class4, subject=cls.subject)
        for _ in range(34):
            SubjectAbsenceFactory(catalog_per_subject=cls.catalog5, student=cls.student5, semester=1)
            SubjectAbsenceFactory(catalog_per_subject=cls.catalog5, student=cls.student5, semester=2)

    @staticmethod
    def create_semester_end_events(calendar):
        SchoolEventFactory(
            academic_year_calendar=calendar,
            semester=calendar.second_semester,
            event_type=SchoolEvent.EventTypes.SECOND_SEMESTER_END_XII_XIII_GRADE,
            starts_at=date(2020, 5, 29),
            ends_at=date(2020, 5, 29)
        )
        SchoolEventFactory(
            academic_year_calendar=calendar,
            semester=calendar.second_semester,
            event_type=SchoolEvent.EventTypes.SECOND_SEMESTER_END_VIII_GRADE,
            starts_at=date(2020, 6, 5),
            ends_at=date(2020, 6, 5)
        )
        SchoolEventFactory(
            academic_year_calendar=calendar,
            semester=calendar.second_semester,
            event_type=SchoolEvent.EventTypes.SECOND_SEMESTER_END_IX_XI_FILIERA_TEHNOLOGICA,
            starts_at=date(2020, 6, 26),
            ends_at=date(2020, 6, 26)
        )

    @patch('django.utils.timezone.now', return_value=datetime(2019, 12, 9).replace(tzinfo=utc))
    @patch('edualert.catalogs.utils.risk_alerts.format_and_send_notification_task')
    def test_send_alerts_for_risks_during_first_semester(self, send_notification_mock, timezone_mock):
        send_alerts_for_risks()
        self.assertEqual(send_notification_mock.call_count, 8)
        calls = [call(ABSENCES_BETWEEN_1_3_TITLE.format(self.student1.full_name),
                      ABSENCES_BETWEEN_1_3_BODY.format(self.subject.name),
                      [self.parent1.id, self.study_class1.class_master_id], True),
                 call(ABSENCES_ABOVE_3_TITLE.format(self.student2.full_name),
                      ABSENCES_ABOVE_3_BODY.format(self.subject.name),
                      [self.study_class2.class_master_id], True),
                 call(ABSENCES_ABOVE_3_TITLE.format(self.student3.full_name),
                      ABSENCES_ABOVE_3_BODY.format(self.subject.name),
                      [self.study_class2.class_master_id], True),
                 call(ABSENCES_ABOVE_LIMIT_TITLE.format(10, self.student3.full_name),
                      ABSENCES_ABOVE_LIMIT_BODY.format(10),
                      [self.study_class2.class_master_id], True),
                 call(ABSENCES_ABOVE_3_TITLE.format(self.student4.full_name),
                      ABSENCES_ABOVE_3_BODY.format(self.subject.name),
                      [self.study_class3.class_master_id], True),
                 call(ABSENCES_ABOVE_LIMIT_TITLE.format(20, self.student4.full_name),
                      ABSENCES_ABOVE_LIMIT_BODY.format(20),
                      [self.study_class3.class_master_id], True),
                 call(ABSENCES_ABOVE_3_TITLE.format(self.student5.full_name),
                      ABSENCES_ABOVE_3_BODY.format(self.subject.name),
                      [self.study_class4.class_master_id], True),
                 call(ABSENCES_ABOVE_LIMIT_TITLE.format(30, self.student5.full_name),
                      ABSENCES_ABOVE_LIMIT_BODY.format(30),
                      [self.study_class4.class_master_id], True),
                 ]
        send_notification_mock.assert_has_calls(calls, any_order=True)

    @patch('django.utils.timezone.now', return_value=datetime(2020, 1, 13).replace(tzinfo=utc))
    @patch('edualert.catalogs.utils.risk_alerts.format_and_send_notification_task')
    def test_send_alerts_for_risks_after_first_semester(self, send_notification_mock, timezone_mock):
        send_alerts_for_risks()
        self.assertEqual(send_notification_mock.call_count, 10)
        calls = [call(ABSENCES_BETWEEN_1_3_TITLE.format(self.student1.full_name),
                      ABSENCES_BETWEEN_1_3_BODY.format(self.subject.name),
                      [self.parent1.id, self.study_class1.class_master_id], True),
                 call(AVG_BELOW_LIMIT_TITLE.format(5, self.student1.full_name),
                      AVG_BELOW_LIMIT_BODY.format(5, self.subject.name),
                      [self.parent1.id, self.study_class1.class_master_id], True),
                 call(BEHAVIOR_GRADE_BELOW_8_TITLE.format(self.student1.full_name),
                      BEHAVIOR_GRADE_BELOW_8_BODY,
                      [self.parent1.id, self.study_class1.class_master_id], True),
                 call(ABSENCES_ABOVE_3_TITLE.format(self.student2.full_name),
                      ABSENCES_ABOVE_3_BODY.format(self.subject.name),
                      [self.study_class2.class_master_id], True),
                 call(ABSENCES_ABOVE_3_TITLE.format(self.student3.full_name),
                      ABSENCES_ABOVE_3_BODY.format(self.subject.name),
                      [self.study_class2.class_master_id], True),
                 call(ABSENCES_ABOVE_LIMIT_TITLE.format(10, self.student3.full_name),
                      ABSENCES_ABOVE_LIMIT_BODY.format(10),
                      [self.study_class2.class_master_id], True),
                 call(ABSENCES_ABOVE_3_TITLE.format(self.student4.full_name),
                      ABSENCES_ABOVE_3_BODY.format(self.subject.name),
                      [self.study_class3.class_master_id], True),
                 call(ABSENCES_ABOVE_LIMIT_TITLE.format(20, self.student4.full_name),
                      ABSENCES_ABOVE_LIMIT_BODY.format(20),
                      [self.study_class3.class_master_id], True),
                 call(ABSENCES_ABOVE_3_TITLE.format(self.student5.full_name),
                      ABSENCES_ABOVE_3_BODY.format(self.subject.name),
                      [self.study_class4.class_master_id], True),
                 call(ABSENCES_ABOVE_LIMIT_TITLE.format(30, self.student5.full_name),
                      ABSENCES_ABOVE_LIMIT_BODY.format(30),
                      [self.study_class4.class_master_id], True),
                 ]
        send_notification_mock.assert_has_calls(calls, any_order=True)

    @patch('django.utils.timezone.now', return_value=datetime(2020, 6, 1).replace(tzinfo=utc))
    @patch('edualert.catalogs.utils.risk_alerts.format_and_send_notification_task')
    def test_send_alerts_for_risks_after_second_semester_12_grade_end(self, send_notification_mock, timezone_mock):
        send_alerts_for_risks()
        self.assertEqual(send_notification_mock.call_count, 5)
        calls = [call(ABSENCES_BETWEEN_1_3_TITLE.format(self.student1.full_name),
                      ABSENCES_BETWEEN_1_3_BODY.format(self.subject.name),
                      [self.parent1.id, self.study_class1.class_master_id], True),
                 call(ABSENCES_ABOVE_3_TITLE.format(self.student4.full_name),
                      ABSENCES_ABOVE_3_BODY.format(self.subject.name),
                      [self.study_class3.class_master_id], True),
                 call(ABSENCES_ABOVE_LIMIT_TITLE.format(20, self.student4.full_name),
                      ABSENCES_ABOVE_LIMIT_BODY.format(20),
                      [self.study_class3.class_master_id], True),
                 call(ABSENCES_ABOVE_3_TITLE.format(self.student5.full_name),
                      ABSENCES_ABOVE_3_BODY.format(self.subject.name),
                      [self.study_class4.class_master_id], True),
                 call(ABSENCES_ABOVE_LIMIT_TITLE.format(30, self.student5.full_name),
                      ABSENCES_ABOVE_LIMIT_BODY.format(30),
                      [self.study_class4.class_master_id], True),
                 ]
        send_notification_mock.assert_has_calls(calls, any_order=True)

    @patch('django.utils.timezone.now', return_value=datetime(2020, 6, 8).replace(tzinfo=utc))
    @patch('edualert.catalogs.utils.risk_alerts.format_and_send_notification_task')
    def test_send_alerts_for_risks_after_second_semester_8_grade_end(self, send_notification_mock, timezone_mock):
        send_alerts_for_risks()
        self.assertEqual(send_notification_mock.call_count, 3)
        calls = [call(ABSENCES_BETWEEN_1_3_TITLE.format(self.student1.full_name),
                      ABSENCES_BETWEEN_1_3_BODY.format(self.subject.name),
                      [self.parent1.id, self.study_class1.class_master_id], True),
                 call(ABSENCES_ABOVE_3_TITLE.format(self.student5.full_name),
                      ABSENCES_ABOVE_3_BODY.format(self.subject.name),
                      [self.study_class4.class_master_id], True),
                 call(ABSENCES_ABOVE_LIMIT_TITLE.format(30, self.student5.full_name),
                      ABSENCES_ABOVE_LIMIT_BODY.format(30),
                      [self.study_class4.class_master_id], True),
                 ]
        send_notification_mock.assert_has_calls(calls, any_order=True)

    @patch('django.utils.timezone.now', return_value=datetime(2020, 6, 15).replace(tzinfo=utc))
    @patch('edualert.catalogs.utils.risk_alerts.format_and_send_notification_task')
    def test_send_alerts_for_risks_after_second_semester_regular_end(self, send_notification_mock, timezone_mock):
        send_alerts_for_risks()
        self.assertEqual(send_notification_mock.call_count, 4)
        calls = [call(AVG_BELOW_7_TITLE.format(self.student1.full_name),
                      AVG_BELOW_7_BODY.format('anuală', self.subject.name),
                      [self.parent1.id, self.study_class1.class_master_id], True),
                 call(BEHAVIOR_GRADE_BELOW_10_TITLE.format(self.student1.full_name),
                      BEHAVIOR_GRADE_BELOW_10_BODY.format('anuală'),
                      [self.parent1.id, self.study_class1.class_master_id], True),
                 call(ABSENCES_ABOVE_3_TITLE.format(self.student5.full_name),
                      ABSENCES_ABOVE_3_BODY.format(self.subject.name),
                      [self.study_class4.class_master_id], True),
                 call(ABSENCES_ABOVE_LIMIT_TITLE.format(30, self.student5.full_name),
                      ABSENCES_ABOVE_LIMIT_BODY.format(30),
                      [self.study_class4.class_master_id], True),
                 ]
        send_notification_mock.assert_has_calls(calls, any_order=True)

    @patch('django.utils.timezone.now', return_value=datetime(2020, 6, 29).replace(tzinfo=utc))
    @patch('edualert.catalogs.utils.risk_alerts.format_and_send_notification_task')
    def test_send_alerts_for_risks_after_second_semester_technological_end(self, send_notification_mock, timezone_mock):
        send_alerts_for_risks()
        send_notification_mock.assert_not_called()

    @patch('django.utils.timezone.now', return_value=datetime(2020, 7, 20).replace(tzinfo=utc))
    @patch('edualert.catalogs.utils.risk_alerts.format_and_send_notification_task')
    def test_send_alerts_for_risks_during_summer_holiday(self, send_notification_mock, timezone_mock):
        send_alerts_for_risks()
        send_notification_mock.assert_not_called()
