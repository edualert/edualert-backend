from edualert.academic_calendars.utils import get_current_academic_calendar
from edualert.academic_programs.models import AcademicProgram
from edualert.common.utils import clone_object_and_override_fields
from edualert.subjects.models import ProgramSubjectThrough


def generate_next_year_academic_programs():
    current_academic_year = get_current_academic_calendar().academic_year
    academic_programs = list(AcademicProgram.objects.filter(academic_year=current_academic_year - 1).prefetch_related('program_subjects_through'))

    academic_programs_to_clone = []
    for academic_program in academic_programs:
        academic_programs_to_clone.append(clone_object_and_override_fields(
            academic_program, save=False,
            academic_year=current_academic_year,
            classes_count=0,
            students_at_risk_count=0,
            avg_sem1=None,
            avg_sem2=None,
            avg_annual=None,
            unfounded_abs_avg_sem1=None,
            unfounded_abs_avg_sem2=None,
            unfounded_abs_avg_annual=None
        ))
    cloned_programs = AcademicProgram.objects.bulk_create(academic_programs_to_clone, batch_size=100)

    program_subjects_through_to_clone = []
    for index, academic_program in enumerate(academic_programs):
        for subject_through in academic_program.program_subjects_through.all():
            program_subjects_through_to_clone.append(clone_object_and_override_fields(
                subject_through, save=False, academic_program=cloned_programs[index])
            )
    ProgramSubjectThrough.objects.bulk_create(program_subjects_through_to_clone, batch_size=100)
