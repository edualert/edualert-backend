import datetime
from unittest.mock import patch

from django.utils import timezone
from pytz import utc

from edualert.academic_calendars.factories import AcademicYearCalendarFactory, SchoolEventFactory
from edualert.academic_calendars.models import AcademicYearCalendar, SchoolEvent
from edualert.academic_programs.factories import AcademicProgramFactory
from edualert.academic_programs.models import AcademicProgram
from edualert.common.api_tests import CommonAPITestCase
from edualert.common.tasks import generate_next_study_year_task
from edualert.profiles.constants import FAILING_1_SUBJECT_LABEL, EXEMPTED_SPORT_LABEL, WORKSHOP_LABEL
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile, Label
from edualert.study_classes.factories import StudyClassFactory


class GenerateNextStudyYearTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.current_calendar = AcademicYearCalendarFactory()
        cls.academic_program = AcademicProgramFactory()

        cls.label1 = Label.objects.get(text=FAILING_1_SUBJECT_LABEL)
        cls.label2 = Label.objects.get(text=EXEMPTED_SPORT_LABEL)
        cls.label3 = Label.objects.get(text=WORKSHOP_LABEL)
        cls.student = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, student_in_class=StudyClassFactory(academic_program=cls.academic_program))
        cls.student.labels.add(cls.label1, cls.label2, cls.label3)

    def setUp(self):
        SchoolEventFactory(academic_year_calendar=self.current_calendar)
        self.event = SchoolEventFactory(academic_year_calendar=self.current_calendar,
                                        starts_at=datetime.date(2020, 6, 1), ends_at=datetime.date(2020, 6, 6))

    def test_generate_next_study_year_no_calendar(self):
        generate_next_study_year_task()
        self.assertEqual(AcademicYearCalendar.objects.count(), 1)

    def test_generate_next_study_year_no_events(self):
        SchoolEvent.objects.all().delete()
        generate_next_study_year_task()
        self.assertEqual(AcademicYearCalendar.objects.count(), 1)

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 6, 6).replace(tzinfo=utc))
    def test_generate_next_study_year_different_day(self, timezone_mock):
        generate_next_study_year_task()
        self.assertEqual(AcademicYearCalendar.objects.count(), 1)

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 6, 7).replace(tzinfo=utc))
    def test_generate_next_study_year(self, timezone_mock):
        generate_next_study_year_task()

        self.assertEqual(AcademicYearCalendar.objects.count(), 2)
        self.assertTrue(AcademicYearCalendar.objects.filter(academic_year=self.current_calendar.academic_year + 1).exists())

        self.assertEqual(AcademicProgram.objects.count(), 2)
        self.assertTrue(AcademicProgram.objects.filter(generic_academic_program=self.academic_program.generic_academic_program,
                                                       school_unit=self.academic_program.school_unit,
                                                       name=self.academic_program.name,
                                                       academic_year=self.current_calendar.academic_year + 1).exists())

        self.student.refresh_from_db()
        self.assertIsNone(self.student.student_in_class)
        self.assertCountEqual(self.student.labels.all(), Label.objects.filter(text=WORKSHOP_LABEL))
