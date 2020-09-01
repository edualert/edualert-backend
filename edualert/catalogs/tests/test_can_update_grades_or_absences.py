import datetime
from unittest.mock import patch

from ddt import data, unpack, ddt
from django.utils import timezone
from pytz import utc

from edualert.academic_calendars.factories import AcademicYearCalendarFactory, SchoolEventFactory
from edualert.academic_calendars.models import SchoolEvent
from edualert.catalogs.utils import can_update_grades_or_absences
from edualert.common.api_tests import CommonAPITestCase
from edualert.schools.factories import RegisteredSchoolUnitFactory, SchoolUnitCategoryFactory
from edualert.study_classes.factories import StudyClassFactory


@ddt
class CanUpdateGradesOrAbsencesTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year_calendar = AcademicYearCalendarFactory()
        cls.school_unit = RegisteredSchoolUnitFactory()

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 5, 5).replace(tzinfo=utc))
    def test_can_update_grades_or_absences_study_class_not_from_current_academic_year(self, mocked_method):
        study_class = StudyClassFactory(
            academic_year=self.academic_year_calendar.academic_year - 1, class_grade='VII', class_grade_arabic=7,
            class_letter='A', school_unit=self.school_unit)
        self.assertFalse(can_update_grades_or_absences(study_class))

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 5, 5).replace(tzinfo=utc))
    def test_can_update_grades_or_absences_inside_event(self, mocked_method):
        study_class = StudyClassFactory(class_grade='VII', class_grade_arabic=7, class_letter='A', school_unit=self.school_unit)
        SchoolEventFactory(
            academic_year_calendar=self.academic_year_calendar,
            event_type=SchoolEvent.EventTypes.CORIGENTE,
            starts_at=datetime.date(2020, 4, 4),
            ends_at=datetime.date(2020, 6, 6))
        self.assertFalse(can_update_grades_or_absences(study_class))

    @data(
        (SchoolEvent.EventTypes.SECOND_SEMESTER_END_IX_XI_FILIERA_TEHNOLOGICA, 11),
        (SchoolEvent.EventTypes.SECOND_SEMESTER_END_XII_XIII_GRADE, 13),
        (SchoolEvent.EventTypes.SECOND_SEMESTER_END_VIII_GRADE, 8)
    )
    @unpack
    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 5, 5).replace(tzinfo=utc))
    def test_can_update_grades_or_absences_during_second_semester_end(self, event_type, class_grade, mocked_method):
        study_class = StudyClassFactory(class_grade_arabic=class_grade, class_letter='A', school_unit=self.school_unit)
        SchoolEventFactory(
            semester=self.academic_year_calendar.second_semester,
            event_type=event_type,
            starts_at=datetime.date(2020, 4, 4),
            ends_at=datetime.date(2020, 6, 6)
        )
        self.assertTrue(can_update_grades_or_absences(study_class))

    @data(
        (SchoolEvent.EventTypes.SECOND_SEMESTER_END_IX_XI_FILIERA_TEHNOLOGICA, 9, 'Liceu - Filieră Tehnologică'),
        (SchoolEvent.EventTypes.SECOND_SEMESTER_END_IX_XI_FILIERA_TEHNOLOGICA, 10, 'Liceu - Filieră Tehnologică'),
        (SchoolEvent.EventTypes.SECOND_SEMESTER_END_IX_XI_FILIERA_TEHNOLOGICA, 11, 'Liceu - Filieră Tehnologică'),
        (SchoolEvent.EventTypes.SECOND_SEMESTER_END_XII_XIII_GRADE, 12, None),
        (SchoolEvent.EventTypes.SECOND_SEMESTER_END_XII_XIII_GRADE, 13, None),
        (SchoolEvent.EventTypes.SECOND_SEMESTER_END_VIII_GRADE, 8, None)
    )
    @unpack
    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 9, 11).replace(tzinfo=utc))
    def test_can_update_grades_or_absences_during_second_semester(self, event_type, class_grade, category_name, mocked_method):
        study_class = StudyClassFactory(class_grade_arabic=class_grade, class_letter='A', school_unit=self.school_unit)
        if category_name:
            self.school_unit.categories.add(SchoolUnitCategoryFactory(name='Liceu - Filieră Tehnologică'))

        second_semester = self.academic_year_calendar.second_semester
        second_semester.starts_at = datetime.date(2020, 6, 6)
        second_semester.ends_at = datetime.date(2020, 9, 9)
        SchoolEventFactory(
            semester=self.academic_year_calendar.second_semester,
            event_type=event_type,
            starts_at=datetime.date(2020, 9, 10),
            ends_at=datetime.date(2020, 9, 11)
        )
        self.assertTrue(can_update_grades_or_absences(study_class))

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 8, 13).replace(tzinfo=utc))
    def test_can_update_grades_or_absences_outside_semester(self, mocked_method):
        study_class = StudyClassFactory(class_grade_arabic=12, class_letter='A', school_unit=self.school_unit)
        self.assertFalse(can_update_grades_or_absences(study_class))
