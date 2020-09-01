from edualert.academic_calendars.factories import AcademicYearCalendarFactory
from edualert.academic_programs.utils import generate_next_year_academic_programs
from edualert.academic_programs.factories import AcademicProgramFactory
from edualert.academic_programs.models import AcademicProgram
from edualert.common.api_tests import CommonAPITestCase
from edualert.subjects.factories import ProgramSubjectThroughFactory, SubjectFactory
from edualert.subjects.models import ProgramSubjectThrough


class GenerateNextYearAcademicProgramsTestCase(CommonAPITestCase):
    def test_generate_next_year_academic_programs(self):
        current_calendar = AcademicYearCalendarFactory()

        program1 = AcademicProgramFactory(academic_year=current_calendar.academic_year - 1)
        ProgramSubjectThroughFactory(academic_program=program1, subject=SubjectFactory())

        program2 = AcademicProgramFactory(academic_year=current_calendar.academic_year - 1)
        ProgramSubjectThroughFactory(academic_program=program2, subject=SubjectFactory())

        generate_next_year_academic_programs()

        self.assertEqual(AcademicProgram.objects.filter(academic_year=current_calendar.academic_year).count(), 2)
        cloned_program1 = AcademicProgram.objects.filter(name=program1.name, academic_year=current_calendar.academic_year).first()
        self.assertIsNotNone(cloned_program1)
        cloned_program2 = AcademicProgram.objects.filter(name=program2.name, academic_year=current_calendar.academic_year).first()
        self.assertIsNotNone(cloned_program2)

        for field in ['avg_sem1', 'avg_sem2', 'avg_annual',
                      'unfounded_abs_avg_sem1', 'unfounded_abs_avg_sem2', 'unfounded_abs_avg_annual']:
            self.assertIsNone(getattr(cloned_program1, field))
            self.assertIsNone(getattr(cloned_program2, field))
        for field in ['classes_count', 'students_at_risk_count']:
            self.assertEqual(getattr(cloned_program1, field), 0)
            self.assertEqual(getattr(cloned_program2, field), 0)

        self.assertEqual(ProgramSubjectThrough.objects.count(), 4)
        self.assertEqual(ProgramSubjectThrough.objects.filter(academic_program__academic_year=current_calendar.academic_year).count(), 2)
        self.assertTrue(ProgramSubjectThrough.objects.filter(academic_program=cloned_program1).exists())
        self.assertTrue(ProgramSubjectThrough.objects.filter(academic_program=cloned_program2).exists())
