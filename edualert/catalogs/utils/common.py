from django.db.models import Q
from django.utils import timezone

from edualert.academic_calendars.models import SchoolEvent
from edualert.academic_calendars.utils import get_current_academic_calendar, check_event_is_semester_end
from edualert.catalogs.models import ExaminationGrade
from edualert.subjects.models import ProgramSubjectThrough


def can_update_grades_or_absences(study_class):
    today = timezone.now().date()
    current_calendar = get_current_academic_calendar()
    if current_calendar is None:
        return False

    if study_class.academic_year != current_calendar.academic_year:
        return False

    events = current_calendar.school_events.all() | current_calendar.second_semester.school_events.all()

    second_semester_end_event = None
    if study_class.class_grade_arabic == 8:
        second_semester_end_event = events.filter(event_type=SchoolEvent.EventTypes.SECOND_SEMESTER_END_VIII_GRADE).first()
    elif study_class.class_grade_arabic in [9, 10, 11]:
        if has_technological_category(study_class.school_unit):
            second_semester_end_event = events.filter(
                event_type=SchoolEvent.EventTypes.SECOND_SEMESTER_END_IX_XI_FILIERA_TEHNOLOGICA
            ).first()
    elif study_class.class_grade_arabic in [12, 13]:
        second_semester_end_event = events.filter(event_type=SchoolEvent.EventTypes.SECOND_SEMESTER_END_XII_XIII_GRADE).first()

    second_semester_end = second_semester_end_event.ends_at if second_semester_end_event else current_calendar.second_semester.ends_at
    if not current_calendar.first_semester.starts_at <= today <= current_calendar.first_semester.ends_at and not \
            current_calendar.second_semester.starts_at <= today <= second_semester_end:
        return False

    for event in events:
        if not check_event_is_semester_end(event.event_type) and event.starts_at < today < event.ends_at:
            return False

    return True


def can_update_examination_grades(study_class, grade_type):
    current_calendar = get_current_academic_calendar()
    if current_calendar is None:
        return False

    if grade_type == ExaminationGrade.GradeTypes.SECOND_EXAMINATION and study_class.academic_year != current_calendar.academic_year:
        return False

    event_type = SchoolEvent.EventTypes.CORIGENTE if grade_type == ExaminationGrade.GradeTypes.SECOND_EXAMINATION \
        else SchoolEvent.EventTypes.DIFERENTE
    event = current_calendar.school_events.filter(event_type=event_type).first()

    if event is None:
        return False

    if not event.starts_at <= timezone.now().date() <= event.ends_at:
        return False

    return True


def update_last_change_in_catalog(user_profile):
    now = timezone.now()
    user_profile.last_change_in_catalog = now
    user_profile.school_unit.last_change_in_catalog = now
    user_profile.school_unit.save()


def has_technological_category(school_unit):
    return school_unit.categories.filter(name='Liceu - Filieră Tehnologică').exists()


def get_working_weeks_count(calendar, semester, study_class, is_technological_school):
    if not calendar:
        return 0

    if semester == 1:
        semester_calendar = calendar.first_semester
    else:
        semester_calendar = calendar.second_semester
    if study_class.class_grade_arabic in range(0, 5):
        working_weeks_count = getattr(semester_calendar, 'working_weeks_count_primary_school')
    elif study_class.class_grade_arabic == 8:
        working_weeks_count = getattr(semester_calendar, 'working_weeks_count_8_grade')
    elif study_class.class_grade_arabic == 12:
        working_weeks_count = getattr(semester_calendar, 'working_weeks_count_12_grade')
    elif study_class.class_grade_arabic in [9, 10, 11] and is_technological_school:
        working_weeks_count = getattr(semester_calendar, 'working_weeks_count_technological')
    else:
        working_weeks_count = getattr(semester_calendar, 'working_weeks_count')

    return working_weeks_count


def get_weekly_hours_count(study_class, subject_id):
    program_subject_through = ProgramSubjectThrough.objects \
        .filter(Q(academic_program_id=study_class.academic_program_id) |
                Q(generic_academic_program_id=study_class.academic_program.generic_academic_program_id),
                subject_id=subject_id, class_grade=study_class.class_grade).first()

    if program_subject_through:
        return program_subject_through.weekly_hours_count

    return 1
