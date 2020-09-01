import datetime
from unittest.mock import patch

from ddt import data, unpack, ddt
from django.utils import timezone
from pytz import utc

from edualert.academic_calendars.factories import AcademicYearCalendarFactory, SchoolEventFactory
from edualert.academic_calendars.models import SchoolEvent
from edualert.catalogs.models import ExaminationGrade
from edualert.catalogs.utils import can_update_examination_grades
from edualert.common.api_tests import CommonAPITestCase
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.study_classes.factories import StudyClassFactory


@ddt
class CanUpdateExaminationGradesTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year_calendar = AcademicYearCalendarFactory()
        cls.school_unit = RegisteredSchoolUnitFactory()
        cls.study_class = StudyClassFactory(school_unit=cls.school_unit)
        cls.corigente_event = SchoolEventFactory(event_type=SchoolEvent.EventTypes.CORIGENTE, academic_year_calendar=cls.academic_year_calendar,
                                                 starts_at=datetime.date(2020, 8, 20), ends_at=datetime.date(2020, 8, 27))
        cls.diferente_event = SchoolEventFactory(event_type=SchoolEvent.EventTypes.DIFERENTE, academic_year_calendar=cls.academic_year_calendar,
                                                 starts_at=datetime.date(2020, 9, 1), ends_at=datetime.date(2020, 9, 8))

    def setUp(self):
        self.study_class = StudyClassFactory(school_unit=self.school_unit)

    def test_can_update_examination_grades_no_calendar(self):
        self.academic_year_calendar.delete()
        self.assertFalse(can_update_examination_grades(self.study_class, ExaminationGrade.GradeTypes.SECOND_EXAMINATION))

    def test_can_update_examination_grades_study_class_not_from_current_academic_year(self):
        # This is only for 2nd examination grade type
        self.study_class.academic_year -= 1
        self.study_class.save()

        self.assertFalse(can_update_examination_grades(self.study_class, ExaminationGrade.GradeTypes.SECOND_EXAMINATION))

    @data(
        ('corigente_event', ExaminationGrade.GradeTypes.SECOND_EXAMINATION),
        ('diferente_event', ExaminationGrade.GradeTypes.DIFFERENCE),
    )
    @unpack
    def test_can_update_examination_grades_no_event(self, event_param, grade_type):
        getattr(self, event_param).delete()
        self.assertFalse(can_update_examination_grades(self.study_class, grade_type))

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 8, 13).replace(tzinfo=utc))
    def test_can_update_examination_grades_outside_event(self, mocked_method):
        self.assertFalse(can_update_examination_grades(self.study_class, ExaminationGrade.GradeTypes.SECOND_EXAMINATION))
        self.assertFalse(can_update_examination_grades(self.study_class, ExaminationGrade.GradeTypes.DIFFERENCE))

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 8, 20).replace(tzinfo=utc))
    def test_can_update_examination_grades_2nd_exam_success(self, mocked_method):
        self.assertTrue(can_update_examination_grades(self.study_class, ExaminationGrade.GradeTypes.SECOND_EXAMINATION))

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 9, 8).replace(tzinfo=utc))
    def test_can_update_examination_grades_difference_success(self, mocked_method):
        self.assertTrue(can_update_examination_grades(self.study_class, ExaminationGrade.GradeTypes.DIFFERENCE))

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 9, 8).replace(tzinfo=utc))
    def test_can_update_examination_grades_difference_previous_year_success(self, mocked_method):
        self.study_class.academic_year = 2019
        self.study_class.save()

        self.assertTrue(can_update_examination_grades(self.study_class, ExaminationGrade.GradeTypes.DIFFERENCE))
