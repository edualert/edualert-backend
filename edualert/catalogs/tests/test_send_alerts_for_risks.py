from datetime import datetime, date
from unittest.mock import patch, call

from pytz import utc

from edualert.academic_calendars.factories import AcademicYearCalendarFactory, SchoolEventFactory
from edualert.academic_calendars.models import SchoolEvent
from edualert.catalogs.constants import AVG_BELOW_LIMIT_TITLE, AVG_BELOW_LIMIT_BODY, \
    BEHAVIOR_GRADE_BELOW_8_TITLE, BEHAVIOR_GRADE_BELOW_8_BODY, \
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
        cls.subject2 = SubjectFactory(name='Limba Romana')
        coordination_subject = SubjectFactory(is_coordination=True)

        cls.school1 = RegisteredSchoolUnitFactory()

        cls.study_class1 = StudyClassFactory(school_unit=cls.school1)

        # behavior grade for the 1st semester lower than 8
        cls.student1 = UserProfileFactory(school_unit=cls.school1, user_role=UserProfile.UserRoles.STUDENT, student_in_class=cls.study_class1)
        cls.parent1 = UserProfileFactory(school_unit=cls.school1, user_role=UserProfile.UserRoles.PARENT)
        cls.student1.parents.add(cls.parent1)
        StudentCatalogPerYearFactory(student=cls.student1, study_class=cls.study_class1)
        cls.catalog1 = StudentCatalogPerSubjectFactory(student=cls.student1, study_class=cls.study_class1, subject=cls.subject, avg_sem1=4, avg_final=6)
        SubjectAbsenceFactory(catalog_per_subject=cls.catalog1, student=cls.student1, semester=1)
        SubjectAbsenceFactory(catalog_per_subject=cls.catalog1, student=cls.student1, semester=2)
        StudentCatalogPerSubjectFactory(student=cls.student1, study_class=cls.study_class1, subject=coordination_subject, avg_sem1=7, avg_final=9)

        cls.study_class2 = StudyClassFactory(school_unit=cls.school1, class_grade='XII', class_grade_arabic=12)

        # 11 unauthorized absences (both sem)
        cls.student2 = UserProfileFactory(school_unit=cls.school1, user_role=UserProfile.UserRoles.STUDENT, student_in_class=cls.study_class2)
        StudentCatalogPerYearFactory(student=cls.student2, study_class=cls.study_class2)
        cls.catalog2 = StudentCatalogPerSubjectFactory(student=cls.student2, study_class=cls.study_class2, subject=cls.subject)
        for _ in range(11):
            SubjectAbsenceFactory(catalog_per_subject=cls.catalog2, student=cls.student2, semester=1)
            SubjectAbsenceFactory(catalog_per_subject=cls.catalog2, student=cls.student2, semester=2)

        cls.school2 = RegisteredSchoolUnitFactory()
        cls.school2.categories.add(SchoolUnitCategoryFactory(name='Liceu - Filieră Tehnologică'))

        cls.study_class3 = StudyClassFactory(school_unit=cls.school2, class_grade='VIII', class_grade_arabic=8)

        # Average below limit (both sem)
        cls.student3 = UserProfileFactory(school_unit=cls.school2, user_role=UserProfile.UserRoles.STUDENT, student_in_class=cls.study_class3)
        StudentCatalogPerYearFactory(student=cls.student3, study_class=cls.study_class3)
        StudentCatalogPerSubjectFactory(student=cls.student3, study_class=cls.study_class3, subject=cls.subject, avg_sem1=4, avg_sem2=3)

        cls.study_class4 = StudyClassFactory(school_unit=cls.school2, class_grade='IX', class_grade_arabic=9)

        # Averages below limit (both sem)
        cls.student4 = UserProfileFactory(school_unit=cls.school2, user_role=UserProfile.UserRoles.STUDENT, student_in_class=cls.study_class4)
        StudentCatalogPerYearFactory(student=cls.student4, study_class=cls.study_class4)
        StudentCatalogPerSubjectFactory(student=cls.student4, study_class=cls.study_class4, subject=cls.subject, avg_sem1=4, avg_sem2=2)
        StudentCatalogPerSubjectFactory(student=cls.student4, study_class=cls.study_class4, subject=cls.subject2, avg_sem1=3, avg_sem2=4)

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

    @patch('django.utils.timezone.now', return_value=datetime(2019, 9, 23).replace(tzinfo=utc))
    @patch('edualert.catalogs.utils.risk_alerts.format_and_send_notification_task')
    def test_send_alerts_for_risks_during_first_semester(self, send_notification_mock, timezone_mock):
        send_alerts_for_risks()
        self.assertEqual(send_notification_mock.call_count, 1)
        calls = [call(ABSENCES_ABOVE_LIMIT_TITLE.format(self.student2.full_name),
                      ABSENCES_ABOVE_LIMIT_BODY.format(self.student2.full_name, 11),
                      [self.study_class2.class_master_id], False)]
        send_notification_mock.assert_has_calls(calls, any_order=True)

    @patch('django.utils.timezone.now', return_value=datetime(2020, 1, 6).replace(tzinfo=utc))
    @patch('edualert.catalogs.utils.risk_alerts.format_and_send_notification_task')
    def test_send_alerts_for_risks_last_first_semester_month(self, send_notification_mock, timezone_mock):
        send_alerts_for_risks()
        self.assertEqual(send_notification_mock.call_count, 4)
        calls = [call(AVG_BELOW_LIMIT_TITLE.format(5, self.student1.full_name),
                      AVG_BELOW_LIMIT_BODY.format(self.student1.full_name, 5, "MAT"),
                      [self.parent1.id, self.study_class1.class_master_id], False),
                 call(ABSENCES_ABOVE_LIMIT_TITLE.format(self.student2.full_name),
                      ABSENCES_ABOVE_LIMIT_BODY.format(self.student2.full_name, 11),
                      [self.study_class2.class_master_id], False),
                 call(AVG_BELOW_LIMIT_TITLE.format(5, self.student3.full_name),
                      AVG_BELOW_LIMIT_BODY.format(self.student3.full_name, 5, "MAT"),
                      [self.study_class3.class_master_id], False),
                 call(AVG_BELOW_LIMIT_TITLE.format(5, self.student4.full_name),
                      AVG_BELOW_LIMIT_BODY.format(self.student4.full_name, 5, "LRO, MAT"),
                      [self.study_class4.class_master_id], False)]
        send_notification_mock.assert_has_calls(calls, any_order=True)

    @patch('django.utils.timezone.now', return_value=datetime(2020, 1, 13).replace(tzinfo=utc))
    @patch('edualert.catalogs.utils.risk_alerts.format_and_send_notification_task')
    def test_send_alerts_for_risks_after_first_semester(self, send_notification_mock, timezone_mock):
        send_alerts_for_risks()
        self.assertEqual(send_notification_mock.call_count, 2)
        calls = [call(BEHAVIOR_GRADE_BELOW_8_TITLE.format(self.student1.full_name),
                      BEHAVIOR_GRADE_BELOW_8_BODY.format(self.student1.full_name),
                      [self.parent1.id, self.study_class1.class_master_id], False),
                 call(ABSENCES_ABOVE_LIMIT_TITLE.format(self.student2.full_name),
                      ABSENCES_ABOVE_LIMIT_BODY.format(self.student2.full_name, 11),
                      [self.study_class2.class_master_id], False)]
        send_notification_mock.assert_has_calls(calls, any_order=True)

    @patch('django.utils.timezone.now', return_value=datetime(2020, 5, 25).replace(tzinfo=utc))
    @patch('edualert.catalogs.utils.risk_alerts.format_and_send_notification_task')
    def test_send_alerts_for_risks_last_second_semester_month_12_grade(self, send_notification_mock, timezone_mock):
        send_alerts_for_risks()
        self.assertEqual(send_notification_mock.call_count, 2)
        calls = [call(ABSENCES_ABOVE_LIMIT_TITLE.format(self.student2.full_name),
                      ABSENCES_ABOVE_LIMIT_BODY.format(self.student2.full_name, 11),
                      [self.study_class2.class_master_id], False),
                 call(AVG_BELOW_LIMIT_TITLE.format(5, self.student3.full_name),
                      AVG_BELOW_LIMIT_BODY.format(self.student3.full_name, 5, "MAT"),
                      [self.study_class3.class_master_id], False)]
        send_notification_mock.assert_has_calls(calls, any_order=True)

    @patch('django.utils.timezone.now', return_value=datetime(2020, 6, 1).replace(tzinfo=utc))
    @patch('edualert.catalogs.utils.risk_alerts.format_and_send_notification_task')
    def test_send_alerts_for_risks_last_second_semester_month_8_grade(self, send_notification_mock, timezone_mock):
        send_alerts_for_risks()
        self.assertEqual(send_notification_mock.call_count, 2)
        calls = [call(AVG_BELOW_LIMIT_TITLE.format(5, self.student3.full_name),
                      AVG_BELOW_LIMIT_BODY.format(self.student3.full_name, 5, "MAT"),
                      [self.study_class3.class_master_id], False),
                 call(AVG_BELOW_LIMIT_TITLE.format(5, self.student4.full_name),
                      AVG_BELOW_LIMIT_BODY.format(self.student4.full_name, 5, "LRO, MAT"),
                      [self.study_class4.class_master_id], False)]
        send_notification_mock.assert_has_calls(calls, any_order=True)

    @patch('django.utils.timezone.now', return_value=datetime(2020, 6, 8).replace(tzinfo=utc))
    @patch('edualert.catalogs.utils.risk_alerts.format_and_send_notification_task')
    def test_send_alerts_for_risks_last_second_semester_month_regular(self, send_notification_mock, timezone_mock):
        send_alerts_for_risks()
        self.assertEqual(send_notification_mock.call_count, 1)
        calls = [call(AVG_BELOW_LIMIT_TITLE.format(5, self.student4.full_name),
                      AVG_BELOW_LIMIT_BODY.format(self.student4.full_name, 5, "LRO, MAT"),
                      [self.study_class4.class_master_id], False)]
        send_notification_mock.assert_has_calls(calls, any_order=True)

    @patch('django.utils.timezone.now', return_value=datetime(2020, 6, 22).replace(tzinfo=utc))
    @patch('edualert.catalogs.utils.risk_alerts.format_and_send_notification_task')
    def test_send_alerts_for_risks_last_second_semester_month_technological(self, send_notification_mock, timezone_mock):
        send_alerts_for_risks()
        self.assertEqual(send_notification_mock.call_count, 1)
        calls = [call(AVG_BELOW_LIMIT_TITLE.format(5, self.student4.full_name),
                      AVG_BELOW_LIMIT_BODY.format(self.student4.full_name, 5, "LRO, MAT"),
                      [self.study_class4.class_master_id], False)]
        send_notification_mock.assert_has_calls(calls, any_order=True)

    @patch('django.utils.timezone.now', return_value=datetime(2020, 7, 20).replace(tzinfo=utc))
    @patch('edualert.catalogs.utils.risk_alerts.format_and_send_notification_task')
    def test_send_alerts_for_risks_during_summer_holiday(self, send_notification_mock, timezone_mock):
        send_alerts_for_risks()
        send_notification_mock.assert_not_called()
