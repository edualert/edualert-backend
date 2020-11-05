from dateutil.relativedelta import relativedelta
from django.db.models import Q

from edualert.academic_calendars.constants import SEMESTER_END_EVENTS
from edualert.academic_calendars.models import AcademicYearCalendar, SchoolEvent
from edualert.common.utils import clone_object_and_override_fields


def get_current_academic_calendar():
    return AcademicYearCalendar.objects.order_by('-academic_year') \
        .select_related('first_semester', 'second_semester').first()


def check_event_is_semester_end(event_type):
    return event_type in SEMESTER_END_EVENTS


def get_second_semester_end_events(current_calendar):
    return {
        SchoolEvent.EventTypes.SECOND_SEMESTER_END_VIII_GRADE: current_calendar.second_semester.school_events
            .filter(event_type=SchoolEvent.EventTypes.SECOND_SEMESTER_END_VIII_GRADE).first(),
        SchoolEvent.EventTypes.SECOND_SEMESTER_END_IX_XI_FILIERA_TEHNOLOGICA: current_calendar.second_semester.school_events
            .filter(event_type=SchoolEvent.EventTypes.SECOND_SEMESTER_END_IX_XI_FILIERA_TEHNOLOGICA).first(),
        SchoolEvent.EventTypes.SECOND_SEMESTER_END_XII_XIII_GRADE: current_calendar.second_semester.school_events
            .filter(event_type=SchoolEvent.EventTypes.SECOND_SEMESTER_END_XII_XIII_GRADE).first(),
    }


def generate_next_year_academic_calendar():
    current_calendar = get_current_academic_calendar()
    next_year = current_calendar.academic_year + 1

    first_semester = clone_object_and_override_fields(
        current_calendar.first_semester,
        save=True,
        starts_at=current_calendar.first_semester.starts_at + relativedelta(years=1),
        ends_at=current_calendar.first_semester.ends_at + relativedelta(years=1)
    )
    second_semester = clone_object_and_override_fields(
        current_calendar.second_semester,
        save=True,
        starts_at=current_calendar.second_semester.starts_at + relativedelta(years=1),
        ends_at=current_calendar.second_semester.ends_at + relativedelta(years=1)
    )

    next_calendar = clone_object_and_override_fields(
        current_calendar, save=True,
        academic_year=next_year,
        first_semester=first_semester,
        second_semester=second_semester
    )

    events_to_create = []
    for event in SchoolEvent.objects.filter(Q(academic_year_calendar=current_calendar) |
                                            Q(semester=current_calendar.first_semester) |
                                            Q(semester=current_calendar.second_semester)):
        semester = None
        if event.semester == current_calendar.first_semester:
            semester = next_calendar.first_semester
        elif event.semester == current_calendar.second_semester:
            semester = next_calendar.second_semester

        events_to_create.append(clone_object_and_override_fields(
            event, save=False,
            academic_year_calendar=next_calendar if event.academic_year_calendar else None,
            semester=semester,
            starts_at=event.starts_at + relativedelta(years=1),
            ends_at=event.ends_at + relativedelta(years=1)
        ))
    SchoolEvent.objects.bulk_create(events_to_create)
