from datetime import timedelta
from celery import shared_task

from edualert.academic_calendars.models import SchoolEvent, AcademicYearCalendar


@shared_task()
def calculate_semesters_working_weeks_task(calendar_id):
    calendar = AcademicYearCalendar.objects \
        .select_related('first_semester', 'second_semester') \
        .prefetch_related('first_semester__school_events', 'second_semester__school_events') \
        .get(id=calendar_id)
    calculate_first_semester_working_weeks(calendar.first_semester)
    calculate_second_semester_working_weeks(calendar.second_semester)


def calculate_first_semester_working_weeks(semester):
    total_weeks = get_weeks_count(semester.starts_at, semester.ends_at)
    semester_events = semester.school_events.all()

    winter_holiday = get_event_by_type(semester_events, SchoolEvent.EventTypes.WINTER_HOLIDAY)
    if winter_holiday:
        total_weeks -= get_weeks_count(winter_holiday.starts_at, winter_holiday.ends_at)

    semester.working_weeks_count = total_weeks
    semester.working_weeks_count_8_grade = total_weeks
    semester.working_weeks_count_12_grade = total_weeks
    semester.working_weeks_count_technological = total_weeks

    autumn_holiday = get_event_by_type(semester_events, SchoolEvent.EventTypes.I_IV_GRADES_AUTUMN_HOLIDAY)
    if autumn_holiday:
        total_weeks -= get_weeks_count(autumn_holiday.starts_at, autumn_holiday.ends_at)
    semester.working_weeks_count_primary_school = total_weeks

    semester.save()


def calculate_second_semester_working_weeks(semester):
    semester_events = semester.school_events.all()
    holiday_weeks = 0

    for event_type in [SchoolEvent.EventTypes.WINTER_HOLIDAY, SchoolEvent.EventTypes.SPRING_HOLIDAY]:
        event = get_event_by_type(semester_events, event_type)
        if event:
            holiday_weeks += get_weeks_count(event.starts_at, event.ends_at)

    # Special cases
    for event_type, field_name in zip([SchoolEvent.EventTypes.SECOND_SEMESTER_END_VIII_GRADE,
                                       SchoolEvent.EventTypes.SECOND_SEMESTER_END_XII_XIII_GRADE,
                                       SchoolEvent.EventTypes.SECOND_SEMESTER_END_IX_XI_FILIERA_TEHNOLOGICA],
                                      ['working_weeks_count_8_grade', 'working_weeks_count_12_grade', 'working_weeks_count_technological']):
        event = get_event_by_type(semester_events, event_type)
        ends_at = event.ends_at if event else semester.ends_at
        setattr(semester, field_name, get_weeks_count(semester.starts_at, ends_at) - holiday_weeks)

    # Regular semester
    working_weeks = get_weeks_count(semester.starts_at, semester.ends_at) - holiday_weeks
    semester.working_weeks_count = working_weeks
    semester.working_weeks_count_primary_school = working_weeks

    semester.save()


def get_weeks_count(start_date, end_date):
    start_date_weekday = start_date.weekday()
    if start_date_weekday in [5, 6]:
        monday1 = start_date + timedelta(days=7 - start_date_weekday)
    else:
        monday1 = start_date - timedelta(days=start_date_weekday)
    monday2 = end_date - timedelta(days=end_date.weekday())
    return (monday2 - monday1).days // 7 + 1


def get_event_by_type(events, event_type):
    for event in events:
        if event.event_type == event_type:
            return event
