from datetime import datetime, date
from unittest.mock import patch

from pytz import utc

from edualert.academic_calendars.factories import AcademicYearCalendarFactory, SchoolEventFactory
from edualert.academic_calendars.models import SchoolEvent
from edualert.catalogs.factories import StudentCatalogPerYearFactory
from edualert.catalogs.utils import calculate_student_placements
from edualert.common.api_tests import CommonAPITestCase
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.study_classes.factories import StudyClassFactory


class StudentPlacementTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.school = RegisteredSchoolUnitFactory()
        cls.study_class = StudyClassFactory(school_unit=cls.school)
        cls.calendar = AcademicYearCalendarFactory(
            first_semester__starts_at=datetime(2020, 1, 10),
            first_semester__ends_at=datetime(2020, 4, 3),
            second_semester__starts_at=datetime(2020, 9, 9),
            second_semester__ends_at=datetime(2020, 12, 11)
        )
        cls.corigente_event = SchoolEventFactory(
            academic_year_calendar=cls.calendar,
            semester=cls.calendar.second_semester,
            event_type=SchoolEvent.EventTypes.CORIGENTE,
            starts_at=date(2020, 12, 20),
            ends_at=date(2020, 12, 21),
        )
        SchoolEventFactory(
            academic_year_calendar=cls.calendar,
            semester=cls.calendar.second_semester,
            event_type=SchoolEvent.EventTypes.SECOND_SEMESTER_END_IX_XI_FILIERA_TEHNOLOGICA,
            starts_at=date(2020, 12, 23),
            ends_at=date(2020, 12, 23)
        )
        SchoolEventFactory(
            academic_year_calendar=cls.calendar,
            semester=cls.calendar.second_semester,
            event_type=SchoolEvent.EventTypes.SECOND_SEMESTER_END_XII_XIII_GRADE,
            starts_at=date(2020, 12, 22),
            ends_at=date(2020, 12, 22)
        )
        SchoolEventFactory(
            academic_year_calendar=cls.calendar,
            semester=cls.calendar.second_semester,
            event_type=SchoolEvent.EventTypes.SECOND_SEMESTER_END_VIII_GRADE,
            starts_at=date(2020, 12, 24),
            ends_at=date(2020, 12, 24)
        )

    @patch('django.utils.timezone.now', return_value=datetime(2020, 10, 10))
    def test_student_placement_outside_of_semester_end(self, mocked_method):
        self.assertFalse(calculate_student_placements())

    @patch('django.utils.timezone.now', return_value=datetime(2020, 12, 22))
    def test_student_placement_during_semester_end_event(self, mocked_method):
        self.assertTrue(calculate_student_placements())

    @patch('django.utils.timezone.now', return_value=datetime(2020, 12, 21))
    def test_student_placement_during_corigente_event(self, mocked_method):
        self.assertTrue(calculate_student_placements())

    @patch('django.utils.timezone.now', return_value=datetime(2020, 4, 3))
    def test_student_placement_during_first_semester_end(self, mocked_method):
        self.assertTrue(calculate_student_placements())

    @patch('django.utils.timezone.now', return_value=datetime(2020, 12, 11))
    def test_student_placement_during_second_semester_end(self, mocked_method):
        self.assertTrue(calculate_student_placements())

    @patch('django.utils.timezone.now', return_value=datetime(2020, 4, 3).replace(tzinfo=utc))
    def test_student_placement_during_first_semester(self, mocked_method):
        catalog1 = StudentCatalogPerYearFactory(
            study_class=self.study_class,
            avg_sem1=1,
            avg_sem2=1,
            avg_annual=1,
            abs_count_sem1=1,
            abs_count_sem2=1,
            abs_count_annual=1
        )

        catalog2 = StudentCatalogPerYearFactory(
            study_class=self.study_class,
            avg_sem1=None,
            avg_sem2=None,
            avg_annual=None,
            abs_count_sem1=2,
            abs_count_sem2=2,
            abs_count_annual=2
        )

        catalog3 = StudentCatalogPerYearFactory(
            study_class=self.study_class,
            avg_sem1=3,
            avg_sem2=3,
            avg_annual=3,
            abs_count_sem1=3,
            abs_count_sem2=3,
            abs_count_annual=3
        )

        other_class = StudyClassFactory(school_unit=self.school)
        catalog4 = StudentCatalogPerYearFactory(
            study_class=other_class,
            avg_sem1=4,
            avg_sem2=4,
            avg_annual=4,
            abs_count_sem1=4,
            abs_count_sem2=4,
            abs_count_annual=4
        )

        catalog5 = StudentCatalogPerYearFactory(
            study_class=other_class,
            avg_sem1=5,
            avg_sem2=5,
            avg_annual=5,
            abs_count_sem1=5,
            abs_count_sem2=5,
            abs_count_annual=5
        )

        other_class2 = StudyClassFactory()
        catalog6 = StudentCatalogPerYearFactory(
            study_class=other_class2,
            avg_sem1=10,
            avg_sem2=10,
            avg_annual=10,
            abs_count_sem1=10,
            abs_count_sem2=10,
            abs_count_annual=10
        )

        self.assertTrue(calculate_student_placements())
        catalog1.refresh_from_db()
        catalog2.refresh_from_db()
        catalog3.refresh_from_db()
        catalog4.refresh_from_db()
        catalog5.refresh_from_db()

        self.assertEqual(catalog3.class_place_by_avg_sem1, 1)
        self.assertEqual(catalog1.class_place_by_avg_sem1, 2)
        self.assertEqual(catalog2.class_place_by_avg_sem1, 3)
        self.assertEqual(catalog3.class_place_by_abs_sem1, 1)
        self.assertEqual(catalog2.class_place_by_abs_sem1, 2)
        self.assertEqual(catalog1.class_place_by_abs_sem1, 3)

        self.assertEqual(catalog4.class_place_by_avg_sem1, 2)
        self.assertEqual(catalog5.class_place_by_avg_sem1, 1)
        self.assertEqual(catalog4.class_place_by_abs_sem1, 2)
        self.assertEqual(catalog5.class_place_by_abs_sem1, 1)

        self.assertEqual(catalog3.school_place_by_avg_sem1, 3)
        self.assertEqual(catalog1.school_place_by_avg_sem1, 4)
        self.assertEqual(catalog2.school_place_by_avg_sem1, 5)
        self.assertEqual(catalog3.school_place_by_abs_sem1, 3)
        self.assertEqual(catalog2.school_place_by_abs_sem1, 4)
        self.assertEqual(catalog1.school_place_by_abs_sem1, 5)

        self.assertEqual(catalog4.school_place_by_abs_sem1, 2)
        self.assertEqual(catalog5.school_place_by_abs_sem1, 1)
        self.assertEqual(catalog4.class_place_by_abs_sem1, 2)
        self.assertEqual(catalog5.class_place_by_abs_sem1, 1)

        for field in [
            'class_place_by_avg_sem2', 'class_place_by_avg_annual', 'class_place_by_abs_sem2', 'class_place_by_abs_annual',
            'school_place_by_avg_sem2', 'school_place_by_avg_annual', 'school_place_by_abs_sem2', 'school_place_by_abs_annual'
        ]:
            self.assertIsNone(getattr(catalog1, field))
            self.assertIsNone(getattr(catalog2, field))
            self.assertIsNone(getattr(catalog3, field))
            self.assertIsNone(getattr(catalog4, field))
            self.assertIsNone(getattr(catalog5, field))

    @patch('django.utils.timezone.now', return_value=datetime(2020, 12, 11).replace(tzinfo=utc))
    def test_student_placement_during_second_semester(self, mocked_method):
        catalog1 = StudentCatalogPerYearFactory(
            study_class=self.study_class,
            avg_sem1=1,
            avg_sem2=1,
            avg_annual=5,
            avg_final=1,
            abs_count_sem1=1,
            abs_count_sem2=1,
            abs_count_annual=1
        )

        catalog2 = StudentCatalogPerYearFactory(
            study_class=self.study_class,
            avg_sem1=2,
            avg_sem2=2,
            avg_annual=1,
            avg_final=2,
            abs_count_sem1=2,
            abs_count_sem2=2,
            abs_count_annual=2
        )

        catalog3 = StudentCatalogPerYearFactory(
            study_class=self.study_class,
            avg_sem1=3,
            avg_sem2=3,
            avg_annual=6,
            avg_final=3,
            abs_count_sem1=3,
            abs_count_sem2=3,
            abs_count_annual=3
        )

        other_class = StudyClassFactory(school_unit=self.school)
        catalog4 = StudentCatalogPerYearFactory(
            study_class=other_class,
            avg_sem1=4,
            avg_sem2=4,
            avg_annual=1,
            avg_final=4,
            abs_count_sem1=4,
            abs_count_sem2=4,
            abs_count_annual=4
        )

        catalog5 = StudentCatalogPerYearFactory(
            study_class=other_class,
            avg_sem1=4,
            avg_sem2=4,
            avg_annual=2,
            avg_final=4,
            abs_count_sem1=4,
            abs_count_sem2=4,
            abs_count_annual=4
        )

        other_class2 = StudyClassFactory()
        catalog6 = StudentCatalogPerYearFactory(
            study_class=other_class2,
            avg_sem1=10,
            avg_sem2=10,
            avg_annual=10,
            abs_count_sem1=10,
            abs_count_sem2=10,
            abs_count_annual=10
        )

        self.assertTrue(calculate_student_placements())
        catalog1.refresh_from_db()
        catalog2.refresh_from_db()
        catalog3.refresh_from_db()
        catalog4.refresh_from_db()
        catalog5.refresh_from_db()

        self.assertEqual(catalog3.class_place_by_avg_sem1, 1)
        self.assertEqual(catalog2.class_place_by_avg_sem1, 2)
        self.assertEqual(catalog1.class_place_by_avg_sem1, 3)
        self.assertEqual(catalog3.class_place_by_abs_sem1, 1)
        self.assertEqual(catalog2.class_place_by_abs_sem1, 2)
        self.assertEqual(catalog1.class_place_by_abs_sem1, 3)
        self.assertEqual(catalog3.class_place_by_avg_sem2, 1)
        self.assertEqual(catalog2.class_place_by_avg_sem2, 2)
        self.assertEqual(catalog1.class_place_by_avg_sem2, 3)
        self.assertEqual(catalog3.class_place_by_abs_sem2, 1)
        self.assertEqual(catalog2.class_place_by_abs_sem2, 2)
        self.assertEqual(catalog1.class_place_by_abs_sem2, 3)
        self.assertEqual(catalog3.class_place_by_avg_annual, 1)
        self.assertEqual(catalog2.class_place_by_avg_annual, 2)
        self.assertEqual(catalog1.class_place_by_avg_annual, 3)
        self.assertEqual(catalog3.class_place_by_abs_annual, 1)
        self.assertEqual(catalog2.class_place_by_abs_annual, 2)
        self.assertEqual(catalog1.class_place_by_abs_annual, 3)

        self.assertEqual(catalog4.class_place_by_avg_sem1, 1)
        self.assertEqual(catalog5.class_place_by_avg_sem1, 1)
        self.assertEqual(catalog4.class_place_by_abs_sem1, 1)
        self.assertEqual(catalog5.class_place_by_abs_sem1, 1)
        self.assertEqual(catalog4.class_place_by_avg_sem2, 1)
        self.assertEqual(catalog5.class_place_by_avg_sem2, 1)
        self.assertEqual(catalog4.class_place_by_abs_sem2, 1)
        self.assertEqual(catalog5.class_place_by_abs_sem2, 1)
        self.assertEqual(catalog4.class_place_by_avg_annual, 1)
        self.assertEqual(catalog5.class_place_by_avg_annual, 1)
        self.assertEqual(catalog4.class_place_by_abs_annual, 1)
        self.assertEqual(catalog5.class_place_by_abs_annual, 1)

        self.assertEqual(catalog3.school_place_by_avg_sem1, 2)
        self.assertEqual(catalog2.school_place_by_avg_sem1, 3)
        self.assertEqual(catalog1.school_place_by_avg_sem1, 4)
        self.assertEqual(catalog3.school_place_by_abs_sem1, 2)
        self.assertEqual(catalog2.school_place_by_abs_sem1, 3)
        self.assertEqual(catalog1.school_place_by_abs_sem1, 4)
        self.assertEqual(catalog3.school_place_by_avg_sem2, 2)
        self.assertEqual(catalog2.school_place_by_avg_sem2, 3)
        self.assertEqual(catalog1.school_place_by_avg_sem2, 4)
        self.assertEqual(catalog3.school_place_by_abs_sem2, 2)
        self.assertEqual(catalog2.school_place_by_abs_sem2, 3)
        self.assertEqual(catalog1.school_place_by_abs_sem2, 4)
        self.assertEqual(catalog3.school_place_by_avg_annual, 2)
        self.assertEqual(catalog2.school_place_by_avg_annual, 3)
        self.assertEqual(catalog1.school_place_by_avg_annual, 4)
        self.assertEqual(catalog3.school_place_by_abs_annual, 2)
        self.assertEqual(catalog2.school_place_by_abs_annual, 3)
        self.assertEqual(catalog1.school_place_by_abs_annual, 4)

        self.assertEqual(catalog4.school_place_by_abs_sem1, 1)
        self.assertEqual(catalog5.school_place_by_abs_sem1, 1)
        self.assertEqual(catalog4.class_place_by_abs_sem1, 1)
        self.assertEqual(catalog5.class_place_by_abs_sem1, 1)
        self.assertEqual(catalog4.school_place_by_abs_sem2, 1)
        self.assertEqual(catalog5.school_place_by_abs_sem2, 1)
        self.assertEqual(catalog4.class_place_by_abs_sem2, 1)
        self.assertEqual(catalog5.class_place_by_abs_sem2, 1)
        self.assertEqual(catalog4.school_place_by_abs_annual, 1)
        self.assertEqual(catalog5.school_place_by_abs_annual, 1)
        self.assertEqual(catalog4.class_place_by_abs_annual, 1)
        self.assertEqual(catalog5.class_place_by_abs_annual, 1)
