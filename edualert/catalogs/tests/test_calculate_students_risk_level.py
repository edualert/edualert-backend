from datetime import datetime, date
from unittest.mock import patch, call

from pytz import utc

from edualert.academic_calendars.factories import AcademicYearCalendarFactory, SchoolEventFactory
from edualert.academic_calendars.models import SchoolEvent
from edualert.catalogs.factories import StudentCatalogPerYearFactory, StudentCatalogPerSubjectFactory, SubjectAbsenceFactory
from edualert.catalogs.utils import calculate_students_risk_level
from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.constants import ABANDONMENT_RISK_1_LABEL, ABANDONMENT_RISK_2_LABEL, ABANDONMENT_RISK_TITLE, ABANDONMENT_RISK_BODY
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile, Label
from edualert.schools.factories import RegisteredSchoolUnitFactory, SchoolUnitCategoryFactory
from edualert.schools.models import RegisteredSchoolUnit
from edualert.statistics.factories import StudentAtRiskCountsFactory
from edualert.statistics.models import StudentAtRiskCounts
from edualert.study_classes.factories import StudyClassFactory
from edualert.study_classes.models import StudyClass
from edualert.subjects.factories import SubjectFactory


class RiskLevelsTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.calendar = AcademicYearCalendarFactory(
            first_semester__starts_at=datetime(2019, 9, 9),
            first_semester__ends_at=datetime(2020, 1, 12),
            second_semester__starts_at=datetime(2020, 1, 13),
            second_semester__ends_at=datetime(2020, 6, 12)
        )
        cls.create_semester_end_events(cls.calendar)
        subject = SubjectFactory(name='Matematică')

        cls.school1 = RegisteredSchoolUnitFactory()

        cls.study_class1 = StudyClassFactory(school_unit=cls.school1)

        # No risk
        cls.student1 = UserProfileFactory(school_unit=cls.school1, user_role=UserProfile.UserRoles.STUDENT, student_in_class=cls.study_class1)
        StudentCatalogPerYearFactory(student=cls.student1, study_class=cls.study_class1)
        # Absences risk 1
        cls.student2 = UserProfileFactory(school_unit=cls.school1, user_role=UserProfile.UserRoles.STUDENT, student_in_class=cls.study_class1)
        StudentCatalogPerYearFactory(student=cls.student2, study_class=cls.study_class1)
        cls.catalog1 = StudentCatalogPerSubjectFactory(student=cls.student2, study_class=cls.study_class1, subject=subject)
        SubjectAbsenceFactory(catalog_per_subject=cls.catalog1, student=cls.student2)
        # Absences risk 2
        cls.student3 = UserProfileFactory(school_unit=cls.school1, user_role=UserProfile.UserRoles.STUDENT, student_in_class=cls.study_class1)
        StudentCatalogPerYearFactory(student=cls.student3, study_class=cls.study_class1)
        cls.catalog2 = StudentCatalogPerSubjectFactory(student=cls.student3, study_class=cls.study_class1, subject=subject)
        for _ in range(5):
            SubjectAbsenceFactory(catalog_per_subject=cls.catalog2, student=cls.student3)

        cls.study_class2 = StudyClassFactory(school_unit=cls.school1, class_grade='X', class_grade_arabic=10)

        # Grades risk 1
        cls.student4 = UserProfileFactory(school_unit=cls.school1, user_role=UserProfile.UserRoles.STUDENT, student_in_class=cls.study_class2)
        StudentCatalogPerYearFactory(student=cls.student4, study_class=cls.study_class2)
        cls.catalog3 = StudentCatalogPerSubjectFactory(student=cls.student4, study_class=cls.study_class2, subject=subject, avg_sem1=5, avg_sem2=6)
        # Grades risk 2 (sem II)
        cls.student5 = UserProfileFactory(school_unit=cls.school1, user_role=UserProfile.UserRoles.STUDENT, student_in_class=cls.study_class2)
        StudentCatalogPerYearFactory(student=cls.student5, study_class=cls.study_class2)
        cls.catalog4 = StudentCatalogPerSubjectFactory(student=cls.student5, study_class=cls.study_class2, subject=subject, avg_sem1=7, avg_sem2=4)

        cls.study_class3 = StudyClassFactory(school_unit=cls.school1, class_grade='XII', class_grade_arabic=12)

        # Behavior grade risk 1 (sem II)
        cls.student6 = UserProfileFactory(school_unit=cls.school1, user_role=UserProfile.UserRoles.STUDENT, student_in_class=cls.study_class3)
        StudentCatalogPerYearFactory(student=cls.student6, study_class=cls.study_class3, behavior_grade_sem1=10, behavior_grade_sem2=9)
        # Behavior grade risk 2
        cls.student7 = UserProfileFactory(school_unit=cls.school1, user_role=UserProfile.UserRoles.STUDENT, student_in_class=cls.study_class3)
        StudentCatalogPerYearFactory(student=cls.student7, study_class=cls.study_class3, behavior_grade_sem1=7, behavior_grade_sem2=6)

        cls.school2 = RegisteredSchoolUnitFactory()
        cls.school2.categories.add(SchoolUnitCategoryFactory(name='Liceu - Filieră Tehnologică'))

        cls.study_class4 = StudyClassFactory(school_unit=cls.school2, class_grade='VIII', class_grade_arabic=8)

        # Absences risk 1 + Grades risk 1
        cls.student8 = UserProfileFactory(school_unit=cls.school2, user_role=UserProfile.UserRoles.STUDENT, student_in_class=cls.study_class4)
        StudentCatalogPerYearFactory(student=cls.student8, study_class=cls.study_class4)
        cls.catalog5 = StudentCatalogPerSubjectFactory(student=cls.student8, study_class=cls.study_class4, subject=subject, avg_sem1=5, avg_sem2=6)
        SubjectAbsenceFactory(catalog_per_subject=cls.catalog5, student=cls.student8)
        # Grades risk 1 + Behavior grade risk 1 (sem II)
        cls.student9 = UserProfileFactory(school_unit=cls.school2, user_role=UserProfile.UserRoles.STUDENT, student_in_class=cls.study_class4)
        StudentCatalogPerYearFactory(student=cls.student9, study_class=cls.study_class4, behavior_grade_sem1=10, behavior_grade_sem2=9)
        cls.catalog6 = StudentCatalogPerSubjectFactory(student=cls.student9, study_class=cls.study_class4, subject=subject, avg_sem1=7, avg_sem2=6)

        cls.study_class5 = StudyClassFactory(school_unit=cls.school2, class_grade='IX', class_grade_arabic=9)

        # Absences risk 2 (both sem) + Behavior grade risk 2 (sem II)
        cls.student10 = UserProfileFactory(school_unit=cls.school2, user_role=UserProfile.UserRoles.STUDENT, student_in_class=cls.study_class5)
        StudentCatalogPerYearFactory(student=cls.student10, study_class=cls.study_class5, behavior_grade_sem1=10, behavior_grade_sem2=6)
        cls.catalog7 = StudentCatalogPerSubjectFactory(student=cls.student10, study_class=cls.study_class5, subject=subject)
        for _ in range(5):
            SubjectAbsenceFactory(catalog_per_subject=cls.catalog7, student=cls.student10)

        # Absences risk 2 + Grades risk 2 + Behavior grade risk 2
        cls.student11 = UserProfileFactory(school_unit=cls.school2, user_role=UserProfile.UserRoles.STUDENT, student_in_class=cls.study_class5)
        StudentCatalogPerYearFactory(student=cls.student11, study_class=cls.study_class5, behavior_grade_sem1=7, behavior_grade_sem2=6)
        cls.catalog8 = StudentCatalogPerSubjectFactory(student=cls.student11, study_class=cls.study_class5, subject=subject, avg_sem1=4, avg_sem2=3)
        for _ in range(5):
            SubjectAbsenceFactory(catalog_per_subject=cls.catalog8, student=cls.student11)

        cls.create_risk_stats()

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

    @staticmethod
    def create_risk_stats():
        StudentAtRiskCountsFactory(month=1, year=2020, by_country=True, daily_counts=[{
            'day': 11,
            'weekday': 'Lu',
            'count': 0
        }])
        StudentAtRiskCountsFactory(month=6, year=2020, by_country=True, daily_counts=[
            {
                'day': 1,
                'weekday': 'Lu',
                'count': 0
            },
            {
                'day': 6,
                'weekday': 'Lu',
                'count': 0
            },
            {
                'day': 13,
                'weekday': 'Lu',
                'count': 0
            },
            {
                'day': 27,
                'weekday': 'Lu',
                'count': 0
            }
        ])
        for school_unit in RegisteredSchoolUnit.objects.all():
            StudentAtRiskCountsFactory(month=1, year=2020, school_unit=school_unit, daily_counts=[{
                'day': 11,
                'weekday': 'Lu',
                'count': 0
            }])
            StudentAtRiskCountsFactory(month=6, year=2020, school_unit=school_unit, daily_counts=[
                {
                    'day': 1,
                    'weekday': 'Lu',
                    'count': 0
                },
                {
                    'day': 6,
                    'weekday': 'Lu',
                    'count': 0
                },
                {
                    'day': 13,
                    'weekday': 'Lu',
                    'count': 0
                },
                {
                    'day': 27,
                    'weekday': 'Lu',
                    'count': 0
                }
            ])
        for study_class in StudyClass.objects.all():
            StudentAtRiskCountsFactory(month=1, year=2020, study_class=study_class, daily_counts=[{
                'day': 11,
                'weekday': 'Lu',
                'count': 0
            }])
            StudentAtRiskCountsFactory(month=6, year=2020, study_class=study_class, daily_counts=[
                {
                    'day': 1,
                    'weekday': 'Lu',
                    'count': 0
                },
                {
                    'day': 6,
                    'weekday': 'Lu',
                    'count': 0
                },
                {
                    'day': 13,
                    'weekday': 'Lu',
                    'count': 0
                },
                {
                    'day': 27,
                    'weekday': 'Lu',
                    'count': 0
                }
            ])

    @patch('django.utils.timezone.now', return_value=datetime(2020, 1, 11).replace(tzinfo=utc))
    @patch('edualert.profiles.tasks.format_and_send_notification_task')
    def test_risk_levels_during_first_semester(self, send_notification_mock, timezone_mock):
        calculate_students_risk_level()
        self.refresh_objects_from_db([self.student1, self.student2, self.student3, self.student4, self.student5,
                                      self.student6, self.student7, self.student8, self.student9, self.student10, self.student11,
                                      self.catalog1, self.catalog2, self.catalog3, self.catalog4, self.catalog5,
                                      self.catalog6, self.catalog7, self.catalog8])

        self.assertEqual(self.student1.labels.count(), 0)
        self.assertFalse(self.student1.is_at_risk)

        self.assertCountEqual(self.student2.labels.all(), Label.objects.filter(text=ABANDONMENT_RISK_1_LABEL))
        self.assertTrue(self.student2.is_at_risk)
        self.assertTrue(self.catalog1.is_at_risk)
        self.assertEqual(self.student2.risk_description, '1-3 absențe nemotivate')

        self.assertCountEqual(self.student3.labels.all(), Label.objects.filter(text=ABANDONMENT_RISK_2_LABEL))
        self.assertTrue(self.student3.is_at_risk)
        self.assertTrue(self.catalog2.is_at_risk)
        self.assertEqual(self.student3.risk_description, '4 sau mai multe absențe nemotivate')

        self.assertEqual(self.student4.labels.count(), 0)
        self.assertFalse(self.student4.is_at_risk)
        self.assertFalse(self.catalog3.is_at_risk)
        self.assertIsNone(self.student4.risk_description)

        self.assertEqual(self.student5.labels.count(), 0)
        self.assertFalse(self.student5.is_at_risk)
        self.assertFalse(self.catalog4.is_at_risk)
        self.assertIsNone(self.student5.risk_description)

        self.assertEqual(self.student6.labels.count(), 0)
        self.assertFalse(self.student6.is_at_risk)
        self.assertIsNone(self.student6.risk_description)

        self.assertEqual(self.student7.labels.count(), 0)
        self.assertFalse(self.student7.is_at_risk)
        self.assertIsNone(self.student7.risk_description)

        self.assertCountEqual(self.student8.labels.all(), Label.objects.filter(text=ABANDONMENT_RISK_1_LABEL))
        self.assertTrue(self.student8.is_at_risk)
        self.assertTrue(self.catalog5.is_at_risk)
        self.assertEqual(self.student8.risk_description, '1-3 absențe nemotivate')

        self.assertEqual(self.student9.labels.count(), 0)
        self.assertFalse(self.student9.is_at_risk)
        self.assertFalse(self.catalog6.is_at_risk)
        self.assertIsNone(self.student9.risk_description)

        self.assertCountEqual(self.student10.labels.all(), Label.objects.filter(text=ABANDONMENT_RISK_2_LABEL))
        self.assertTrue(self.student10.is_at_risk)
        self.assertTrue(self.catalog7.is_at_risk)
        self.assertEqual(self.student10.risk_description, '4 sau mai multe absențe nemotivate')

        self.assertCountEqual(self.student11.labels.all(), Label.objects.filter(text=ABANDONMENT_RISK_2_LABEL))
        self.assertTrue(self.student11.is_at_risk)
        self.assertTrue(self.catalog8.is_at_risk)
        self.assertEqual(self.student11.risk_description, '4 sau mai multe absențe nemotivate')

        country_stats = StudentAtRiskCounts.objects.get(by_country=True, year=2020, month=1)
        self.assertEqual(country_stats.daily_counts[0]['count'], 5)
        school1_stats = StudentAtRiskCounts.objects.get(school_unit=self.school1, year=2020, month=1)
        self.assertEqual(school1_stats.daily_counts[0]['count'], 2)
        school2_stats = StudentAtRiskCounts.objects.get(school_unit=self.school2, year=2020, month=1)
        self.assertEqual(school2_stats.daily_counts[0]['count'], 3)
        study_class1_stats = StudentAtRiskCounts.objects.get(study_class=self.study_class1, year=2020, month=1)
        self.assertEqual(study_class1_stats.daily_counts[0]['count'], 2)
        study_class2_stats = StudentAtRiskCounts.objects.get(study_class=self.study_class2, year=2020, month=1)
        self.assertEqual(study_class2_stats.daily_counts[0]['count'], 0)
        study_class3_stats = StudentAtRiskCounts.objects.get(study_class=self.study_class3, year=2020, month=1)
        self.assertEqual(study_class3_stats.daily_counts[0]['count'], 0)
        study_class4_stats = StudentAtRiskCounts.objects.get(study_class=self.study_class4, year=2020, month=1)
        self.assertEqual(study_class4_stats.daily_counts[0]['count'], 1)
        study_class5_stats = StudentAtRiskCounts.objects.get(study_class=self.study_class5, year=2020, month=1)
        self.assertEqual(study_class5_stats.daily_counts[0]['count'], 2)

        self.assertEqual(send_notification_mock.call_count, 5)
        calls = [call(ABANDONMENT_RISK_TITLE.format(self.student2.full_name),
                      ABANDONMENT_RISK_BODY.format(1),
                      [self.study_class1.class_master_id, self.school1.school_principal_id], False),
                 call(ABANDONMENT_RISK_TITLE.format(self.student3.full_name),
                      ABANDONMENT_RISK_BODY.format(2),
                      [self.study_class1.class_master_id, self.school1.school_principal_id], False),
                 call(ABANDONMENT_RISK_TITLE.format(self.student8.full_name),
                      ABANDONMENT_RISK_BODY.format(1),
                      [self.study_class4.class_master_id, self.school2.school_principal_id], False),
                 call(ABANDONMENT_RISK_TITLE.format(self.student10.full_name),
                      ABANDONMENT_RISK_BODY.format(2),
                      [self.study_class5.class_master_id, self.school2.school_principal_id], False),
                 call(ABANDONMENT_RISK_TITLE.format(self.student11.full_name),
                      ABANDONMENT_RISK_BODY.format(2),
                      [self.study_class5.class_master_id, self.school2.school_principal_id], False),
                 ]
        send_notification_mock.assert_has_calls(calls, any_order=True)

    @patch('django.utils.timezone.now', return_value=datetime(2020, 6, 1).replace(tzinfo=utc))
    def test_risk_levels_after_second_semester_12_grade_end(self, mocked_method):
        calculate_students_risk_level()
        self.refresh_objects_from_db([self.student1, self.student2, self.student3, self.student4, self.student5,
                                      self.student6, self.student7, self.student8, self.student9, self.student10, self.student11,
                                      self.catalog1, self.catalog2, self.catalog3, self.catalog4, self.catalog5,
                                      self.catalog6, self.catalog7, self.catalog8])

        self.assertEqual(self.student1.labels.count(), 0)
        self.assertFalse(self.student1.is_at_risk)

        self.assertCountEqual(self.student2.labels.all(), Label.objects.filter(text=ABANDONMENT_RISK_1_LABEL))
        self.assertTrue(self.student2.is_at_risk)
        self.assertTrue(self.catalog1.is_at_risk)
        self.assertEqual(self.student2.risk_description, '1-3 absențe nemotivate')

        self.assertCountEqual(self.student3.labels.all(), Label.objects.filter(text=ABANDONMENT_RISK_2_LABEL))
        self.assertTrue(self.student3.is_at_risk)
        self.assertTrue(self.catalog2.is_at_risk)
        self.assertEqual(self.student3.risk_description, '4 sau mai multe absențe nemotivate')

        self.assertCountEqual(self.student4.labels.all(), Label.objects.filter(text=ABANDONMENT_RISK_1_LABEL))
        self.assertTrue(self.student4.is_at_risk)
        self.assertTrue(self.catalog3.is_at_risk)
        self.assertEqual(self.student4.risk_description, '5-6 notă Limba română sau Matematică')

        self.assertEqual(self.student5.labels.count(), 0)
        self.assertFalse(self.student5.is_at_risk)
        self.assertFalse(self.catalog4.is_at_risk)
        self.assertIsNone(self.student5.risk_description)

        self.assertCountEqual(self.student6.labels.all(), Label.objects.filter(text=ABANDONMENT_RISK_1_LABEL))
        self.assertTrue(self.student6.is_at_risk)
        self.assertEqual(self.student6.risk_description, '8-9 notă purtare')

        self.assertCountEqual(self.student7.labels.all(), Label.objects.filter(text=ABANDONMENT_RISK_2_LABEL))
        self.assertTrue(self.student7.is_at_risk)
        self.assertEqual(self.student7.risk_description, 'Notă purtare sub 8')

        self.assertCountEqual(self.student8.labels.all(), Label.objects.filter(text=ABANDONMENT_RISK_1_LABEL))
        self.assertTrue(self.student8.is_at_risk)
        self.assertTrue(self.catalog5.is_at_risk)
        self.assertEqual(self.student8.risk_description, '1-3 absențe nemotivate și 5-6 notă Limba română sau Matematică')

        self.assertEqual(self.student9.labels.count(), 0)
        self.assertFalse(self.student9.is_at_risk)
        self.assertFalse(self.catalog6.is_at_risk)
        self.assertIsNone(self.student9.risk_description)

        self.assertCountEqual(self.student10.labels.all(), Label.objects.filter(text=ABANDONMENT_RISK_2_LABEL))
        self.assertTrue(self.student10.is_at_risk)
        self.assertTrue(self.catalog7.is_at_risk)
        self.assertEqual(self.student10.risk_description, '4 sau mai multe absențe nemotivate')

        self.assertCountEqual(self.student11.labels.all(), Label.objects.filter(text=ABANDONMENT_RISK_2_LABEL))
        self.assertTrue(self.student11.is_at_risk)
        self.assertTrue(self.catalog8.is_at_risk)
        self.assertEqual(self.student11.risk_description, '4 sau mai multe absențe nemotivate și notă Limba română sau Matematică sub 5 și notă purtare sub 8')

        country_stats = StudentAtRiskCounts.objects.get(by_country=True, year=2020, month=6)
        self.assertEqual(country_stats.daily_counts[0]['count'], 8)
        school1_stats = StudentAtRiskCounts.objects.get(school_unit=self.school1, year=2020, month=6)
        self.assertEqual(school1_stats.daily_counts[0]['count'], 5)
        school2_stats = StudentAtRiskCounts.objects.get(school_unit=self.school2, year=2020, month=6)
        self.assertEqual(school2_stats.daily_counts[0]['count'], 3)
        study_class1_stats = StudentAtRiskCounts.objects.get(study_class=self.study_class1, year=2020, month=6)
        self.assertEqual(study_class1_stats.daily_counts[0]['count'], 2)
        study_class2_stats = StudentAtRiskCounts.objects.get(study_class=self.study_class2, year=2020, month=6)
        self.assertEqual(study_class2_stats.daily_counts[0]['count'], 1)
        study_class3_stats = StudentAtRiskCounts.objects.get(study_class=self.study_class3, year=2020, month=6)
        self.assertEqual(study_class3_stats.daily_counts[0]['count'], 2)
        study_class4_stats = StudentAtRiskCounts.objects.get(study_class=self.study_class4, year=2020, month=6)
        self.assertEqual(study_class4_stats.daily_counts[0]['count'], 1)
        study_class5_stats = StudentAtRiskCounts.objects.get(study_class=self.study_class5, year=2020, month=6)
        self.assertEqual(study_class5_stats.daily_counts[0]['count'], 2)

    @patch('django.utils.timezone.now', return_value=datetime(2020, 6, 6).replace(tzinfo=utc))
    def test_risk_levels_after_second_semester_8_grade_end(self, mocked_method):
        calculate_students_risk_level()
        self.refresh_objects_from_db([self.student1, self.student2, self.student3, self.student4, self.student5,
                                      self.student6, self.student7, self.student8, self.student9, self.student10, self.student11,
                                      self.catalog1, self.catalog2, self.catalog3, self.catalog4, self.catalog5,
                                      self.catalog6, self.catalog7, self.catalog8])

        self.assertEqual(self.student1.labels.count(), 0)
        self.assertFalse(self.student1.is_at_risk)

        self.assertCountEqual(self.student2.labels.all(), Label.objects.filter(text=ABANDONMENT_RISK_1_LABEL))
        self.assertTrue(self.student2.is_at_risk)
        self.assertTrue(self.catalog1.is_at_risk)
        self.assertEqual(self.student2.risk_description, '1-3 absențe nemotivate')

        self.assertCountEqual(self.student3.labels.all(), Label.objects.filter(text=ABANDONMENT_RISK_2_LABEL))
        self.assertTrue(self.student3.is_at_risk)
        self.assertTrue(self.catalog2.is_at_risk)
        self.assertEqual(self.student3.risk_description, '4 sau mai multe absențe nemotivate')

        self.assertCountEqual(self.student4.labels.all(), Label.objects.filter(text=ABANDONMENT_RISK_1_LABEL))
        self.assertTrue(self.student4.is_at_risk)
        self.assertTrue(self.catalog3.is_at_risk)
        self.assertEqual(self.student4.risk_description, '5-6 notă Limba română sau Matematică')

        self.assertEqual(self.student5.labels.count(), 0)
        self.assertFalse(self.student5.is_at_risk)
        self.assertFalse(self.catalog4.is_at_risk)
        self.assertIsNone(self.student5.risk_description)

        self.assertCountEqual(self.student6.labels.all(), Label.objects.filter(text=ABANDONMENT_RISK_1_LABEL))
        self.assertTrue(self.student6.is_at_risk)
        self.assertEqual(self.student6.risk_description, '8-9 notă purtare')

        self.assertCountEqual(self.student7.labels.all(), Label.objects.filter(text=ABANDONMENT_RISK_2_LABEL))
        self.assertTrue(self.student7.is_at_risk)
        self.assertEqual(self.student7.risk_description, 'Notă purtare sub 8')

        self.assertCountEqual(self.student8.labels.all(), Label.objects.filter(text=ABANDONMENT_RISK_1_LABEL))
        self.assertTrue(self.student8.is_at_risk)
        self.assertTrue(self.catalog5.is_at_risk)
        self.assertEqual(self.student8.risk_description, '1-3 absențe nemotivate și 5-6 notă Limba română sau Matematică')

        self.assertCountEqual(self.student9.labels.all(), Label.objects.filter(text=ABANDONMENT_RISK_1_LABEL))
        self.assertTrue(self.student9.is_at_risk)
        self.assertTrue(self.catalog6.is_at_risk)
        self.assertEqual(self.student9.risk_description, '5-6 notă Limba română sau Matematică și 8-9 notă purtare')

        self.assertCountEqual(self.student10.labels.all(), Label.objects.filter(text=ABANDONMENT_RISK_2_LABEL))
        self.assertTrue(self.student10.is_at_risk)
        self.assertTrue(self.catalog7.is_at_risk)
        self.assertEqual(self.student10.risk_description, '4 sau mai multe absențe nemotivate')

        self.assertCountEqual(self.student11.labels.all(), Label.objects.filter(text=ABANDONMENT_RISK_2_LABEL))
        self.assertTrue(self.student11.is_at_risk)
        self.assertTrue(self.catalog8.is_at_risk)
        self.assertEqual(self.student11.risk_description, '4 sau mai multe absențe nemotivate și notă Limba română sau Matematică sub 5 și notă purtare sub 8')

        country_stats = StudentAtRiskCounts.objects.get(by_country=True, year=2020, month=6)
        self.assertEqual(country_stats.daily_counts[1]['count'], 9)
        school1_stats = StudentAtRiskCounts.objects.get(school_unit=self.school1, year=2020, month=6)
        self.assertEqual(school1_stats.daily_counts[1]['count'], 5)
        school2_stats = StudentAtRiskCounts.objects.get(school_unit=self.school2, year=2020, month=6)
        self.assertEqual(school2_stats.daily_counts[1]['count'], 4)
        study_class1_stats = StudentAtRiskCounts.objects.get(study_class=self.study_class1, year=2020, month=6)
        self.assertEqual(study_class1_stats.daily_counts[1]['count'], 2)
        study_class2_stats = StudentAtRiskCounts.objects.get(study_class=self.study_class2, year=2020, month=6)
        self.assertEqual(study_class2_stats.daily_counts[1]['count'], 1)
        study_class3_stats = StudentAtRiskCounts.objects.get(study_class=self.study_class3, year=2020, month=6)
        self.assertEqual(study_class3_stats.daily_counts[1]['count'], 2)
        study_class4_stats = StudentAtRiskCounts.objects.get(study_class=self.study_class4, year=2020, month=6)
        self.assertEqual(study_class4_stats.daily_counts[1]['count'], 2)
        study_class5_stats = StudentAtRiskCounts.objects.get(study_class=self.study_class5, year=2020, month=6)
        self.assertEqual(study_class5_stats.daily_counts[1]['count'], 2)

    @patch('django.utils.timezone.now', return_value=datetime(2020, 6, 13).replace(tzinfo=utc))
    def test_risk_levels_after_second_semester_regular_end(self, mocked_method):
        calculate_students_risk_level()
        self.refresh_objects_from_db([self.student1, self.student2, self.student3, self.student4, self.student5,
                                      self.student6, self.student7, self.student8, self.student9, self.student10, self.student11,
                                      self.catalog1, self.catalog2, self.catalog3, self.catalog4, self.catalog5,
                                      self.catalog6, self.catalog7, self.catalog8])

        self.assertEqual(self.student1.labels.count(), 0)
        self.assertFalse(self.student1.is_at_risk)

        self.assertCountEqual(self.student2.labels.all(), Label.objects.filter(text=ABANDONMENT_RISK_1_LABEL))
        self.assertTrue(self.student2.is_at_risk)
        self.assertTrue(self.catalog1.is_at_risk)
        self.assertEqual(self.student2.risk_description, '1-3 absențe nemotivate')

        self.assertCountEqual(self.student3.labels.all(), Label.objects.filter(text=ABANDONMENT_RISK_2_LABEL))
        self.assertTrue(self.student3.is_at_risk)
        self.assertTrue(self.catalog2.is_at_risk)
        self.assertEqual(self.student3.risk_description, '4 sau mai multe absențe nemotivate')

        self.assertCountEqual(self.student4.labels.all(), Label.objects.filter(text=ABANDONMENT_RISK_1_LABEL))
        self.assertTrue(self.student4.is_at_risk)
        self.assertTrue(self.catalog3.is_at_risk)
        self.assertEqual(self.student4.risk_description, '5-6 notă Limba română sau Matematică')

        self.assertCountEqual(self.student5.labels.all(), Label.objects.filter(text=ABANDONMENT_RISK_2_LABEL))
        self.assertTrue(self.student5.is_at_risk)
        self.assertTrue(self.catalog4.is_at_risk)
        self.assertEqual(self.student5.risk_description, 'Notă Limba română sau Matematică sub 5')

        self.assertCountEqual(self.student6.labels.all(), Label.objects.filter(text=ABANDONMENT_RISK_1_LABEL))
        self.assertTrue(self.student6.is_at_risk)
        self.assertEqual(self.student6.risk_description, '8-9 notă purtare')

        self.assertCountEqual(self.student7.labels.all(), Label.objects.filter(text=ABANDONMENT_RISK_2_LABEL))
        self.assertTrue(self.student7.is_at_risk)
        self.assertEqual(self.student7.risk_description, 'Notă purtare sub 8')

        self.assertCountEqual(self.student8.labels.all(), Label.objects.filter(text=ABANDONMENT_RISK_1_LABEL))
        self.assertTrue(self.student8.is_at_risk)
        self.assertTrue(self.catalog5.is_at_risk)
        self.assertEqual(self.student8.risk_description, '1-3 absențe nemotivate și 5-6 notă Limba română sau Matematică')

        self.assertCountEqual(self.student9.labels.all(), Label.objects.filter(text=ABANDONMENT_RISK_1_LABEL))
        self.assertTrue(self.student9.is_at_risk)
        self.assertTrue(self.catalog6.is_at_risk)
        self.assertEqual(self.student9.risk_description, '5-6 notă Limba română sau Matematică și 8-9 notă purtare')

        self.assertCountEqual(self.student10.labels.all(), Label.objects.filter(text=ABANDONMENT_RISK_2_LABEL))
        self.assertTrue(self.student10.is_at_risk)
        self.assertTrue(self.catalog7.is_at_risk)
        self.assertEqual(self.student10.risk_description, '4 sau mai multe absențe nemotivate')

        self.assertCountEqual(self.student11.labels.all(), Label.objects.filter(text=ABANDONMENT_RISK_2_LABEL))
        self.assertTrue(self.student11.is_at_risk)
        self.assertTrue(self.catalog8.is_at_risk)
        self.assertEqual(self.student11.risk_description, '4 sau mai multe absențe nemotivate și notă Limba română sau Matematică sub 5 și notă purtare sub 8')

        country_stats = StudentAtRiskCounts.objects.get(by_country=True, year=2020, month=6)
        self.assertEqual(country_stats.daily_counts[2]['count'], 10)
        school1_stats = StudentAtRiskCounts.objects.get(school_unit=self.school1, year=2020, month=6)
        self.assertEqual(school1_stats.daily_counts[2]['count'], 6)
        school2_stats = StudentAtRiskCounts.objects.get(school_unit=self.school2, year=2020, month=6)
        self.assertEqual(school2_stats.daily_counts[2]['count'], 4)
        study_class1_stats = StudentAtRiskCounts.objects.get(study_class=self.study_class1, year=2020, month=6)
        self.assertEqual(study_class1_stats.daily_counts[2]['count'], 2)
        study_class2_stats = StudentAtRiskCounts.objects.get(study_class=self.study_class2, year=2020, month=6)
        self.assertEqual(study_class2_stats.daily_counts[2]['count'], 2)
        study_class3_stats = StudentAtRiskCounts.objects.get(study_class=self.study_class3, year=2020, month=6)
        self.assertEqual(study_class3_stats.daily_counts[2]['count'], 2)
        study_class4_stats = StudentAtRiskCounts.objects.get(study_class=self.study_class4, year=2020, month=6)
        self.assertEqual(study_class4_stats.daily_counts[2]['count'], 2)
        study_class5_stats = StudentAtRiskCounts.objects.get(study_class=self.study_class5, year=2020, month=6)
        self.assertEqual(study_class5_stats.daily_counts[2]['count'], 2)

    @patch('django.utils.timezone.now', return_value=datetime(2020, 6, 27).replace(tzinfo=utc))
    def test_risk_levels_after_second_semester_technological_end(self, mocked_method):
        calculate_students_risk_level()
        self.refresh_objects_from_db([self.student1, self.student2, self.student3, self.student4, self.student5,
                                      self.student6, self.student7, self.student8, self.student9, self.student10, self.student11,
                                      self.catalog1, self.catalog2, self.catalog3, self.catalog4, self.catalog5,
                                      self.catalog6, self.catalog7, self.catalog8])

        self.assertEqual(self.student1.labels.count(), 0)
        self.assertFalse(self.student1.is_at_risk)

        self.assertCountEqual(self.student2.labels.all(), Label.objects.filter(text=ABANDONMENT_RISK_1_LABEL))
        self.assertTrue(self.student2.is_at_risk)
        self.assertTrue(self.catalog1.is_at_risk)
        self.assertEqual(self.student2.risk_description, '1-3 absențe nemotivate')

        self.assertCountEqual(self.student3.labels.all(), Label.objects.filter(text=ABANDONMENT_RISK_2_LABEL))
        self.assertTrue(self.student3.is_at_risk)
        self.assertTrue(self.catalog2.is_at_risk)
        self.assertEqual(self.student3.risk_description, '4 sau mai multe absențe nemotivate')

        self.assertCountEqual(self.student4.labels.all(), Label.objects.filter(text=ABANDONMENT_RISK_1_LABEL))
        self.assertTrue(self.student4.is_at_risk)
        self.assertTrue(self.catalog3.is_at_risk)
        self.assertEqual(self.student4.risk_description, '5-6 notă Limba română sau Matematică')

        self.assertCountEqual(self.student5.labels.all(), Label.objects.filter(text=ABANDONMENT_RISK_2_LABEL))
        self.assertTrue(self.student5.is_at_risk)
        self.assertTrue(self.catalog4.is_at_risk)
        self.assertEqual(self.student5.risk_description, 'Notă Limba română sau Matematică sub 5')

        self.assertCountEqual(self.student6.labels.all(), Label.objects.filter(text=ABANDONMENT_RISK_1_LABEL))
        self.assertTrue(self.student6.is_at_risk)
        self.assertEqual(self.student6.risk_description, '8-9 notă purtare')

        self.assertCountEqual(self.student7.labels.all(), Label.objects.filter(text=ABANDONMENT_RISK_2_LABEL))
        self.assertTrue(self.student7.is_at_risk)
        self.assertEqual(self.student7.risk_description, 'Notă purtare sub 8')

        self.assertCountEqual(self.student8.labels.all(), Label.objects.filter(text=ABANDONMENT_RISK_1_LABEL))
        self.assertTrue(self.student8.is_at_risk)
        self.assertTrue(self.catalog5.is_at_risk)
        self.assertEqual(self.student8.risk_description, '1-3 absențe nemotivate și 5-6 notă Limba română sau Matematică')

        self.assertCountEqual(self.student9.labels.all(), Label.objects.filter(text=ABANDONMENT_RISK_1_LABEL))
        self.assertTrue(self.student9.is_at_risk)
        self.assertTrue(self.catalog6.is_at_risk)
        self.assertEqual(self.student9.risk_description, '5-6 notă Limba română sau Matematică și 8-9 notă purtare')

        self.assertCountEqual(self.student10.labels.all(), Label.objects.filter(text=ABANDONMENT_RISK_2_LABEL))
        self.assertTrue(self.student10.is_at_risk)
        self.assertTrue(self.catalog7.is_at_risk)
        self.assertEqual(self.student10.risk_description, '4 sau mai multe absențe nemotivate și notă purtare sub 8')

        self.assertCountEqual(self.student11.labels.all(), Label.objects.filter(text=ABANDONMENT_RISK_2_LABEL))
        self.assertTrue(self.student11.is_at_risk)
        self.assertTrue(self.catalog8.is_at_risk)
        self.assertEqual(self.student11.risk_description, '4 sau mai multe absențe nemotivate și notă Limba română sau Matematică sub 5 și notă purtare sub 8')

        country_stats = StudentAtRiskCounts.objects.get(by_country=True, year=2020, month=6)
        self.assertEqual(country_stats.daily_counts[3]['count'], 10)
        school1_stats = StudentAtRiskCounts.objects.get(school_unit=self.school1, year=2020, month=6)
        self.assertEqual(school1_stats.daily_counts[3]['count'], 6)
        school2_stats = StudentAtRiskCounts.objects.get(school_unit=self.school2, year=2020, month=6)
        self.assertEqual(school2_stats.daily_counts[3]['count'], 4)
        study_class1_stats = StudentAtRiskCounts.objects.get(study_class=self.study_class1, year=2020, month=6)
        self.assertEqual(study_class1_stats.daily_counts[3]['count'], 2)
        study_class2_stats = StudentAtRiskCounts.objects.get(study_class=self.study_class2, year=2020, month=6)
        self.assertEqual(study_class2_stats.daily_counts[3]['count'], 2)
        study_class3_stats = StudentAtRiskCounts.objects.get(study_class=self.study_class3, year=2020, month=6)
        self.assertEqual(study_class3_stats.daily_counts[3]['count'], 2)
        study_class4_stats = StudentAtRiskCounts.objects.get(study_class=self.study_class4, year=2020, month=6)
        self.assertEqual(study_class4_stats.daily_counts[3]['count'], 2)
        study_class5_stats = StudentAtRiskCounts.objects.get(study_class=self.study_class5, year=2020, month=6)
        self.assertEqual(study_class5_stats.daily_counts[3]['count'], 2)
