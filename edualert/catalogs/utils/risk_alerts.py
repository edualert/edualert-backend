from dateutil.relativedelta import relativedelta
from django.utils import timezone

from edualert.academic_calendars.models import SchoolEvent
from edualert.academic_calendars.utils import get_current_academic_calendar, get_second_semester_end_events
from edualert.catalogs.constants import AVG_BELOW_LIMIT_TITLE, AVG_BELOW_LIMIT_BODY, \
    BEHAVIOR_GRADE_BELOW_8_TITLE, BEHAVIOR_GRADE_BELOW_8_BODY
from edualert.catalogs.models import StudentCatalogPerYear
from edualert.catalogs.utils import has_technological_category
from edualert.catalogs.utils.risk_levels import get_mapped_catalogs_per_subject
from edualert.catalogs.utils.school_situation_alerts import get_subject_initials
from edualert.notifications.tasks import format_and_send_notification_task
from edualert.schools.models import RegisteredSchoolUnit


def send_alerts_for_risks():
    today = timezone.now().date()

    current_calendar = get_current_academic_calendar()
    if not current_calendar:
        return
    second_semester_end_events = get_second_semester_end_events(current_calendar)
    first_semester_report_date = get_next_monday_for_date(current_calendar.first_semester.ends_at)
    last_month_of_first_semester = first_semester_report_date - relativedelta(months=1)

    for school_unit in RegisteredSchoolUnit.objects.select_related('academic_profile').all():
        is_technological_school = has_technological_category(school_unit)

        catalogs_per_year = StudentCatalogPerYear.objects.filter(academic_year=current_calendar.academic_year,
                                                                 student__is_active=True,
                                                                 study_class__school_unit_id=school_unit.id) \
            .select_related('student', 'study_class')
        catalogs_per_subject = get_mapped_catalogs_per_subject(current_calendar.academic_year, school_unit.id)

        for catalog in catalogs_per_year:
            student = catalog.student
            student_catalogs_per_subject = catalogs_per_subject.get(catalog.student_id, [])
            second_semester_report_date = get_second_semester_report_date(current_calendar, second_semester_end_events,
                                                                          catalog.study_class.class_grade_arabic, is_technological_school)
            last_month_of_second_semester = second_semester_report_date - relativedelta(months=1)

            subjects_with_avg_below_limit = []
            has_behavior_grade_below_8 = False

            for catalog_per_subject in student_catalogs_per_subject:
                if today == first_semester_report_date:
                    if catalog_per_subject.is_coordination_subject and catalog_per_subject.avg_sem1 and catalog_per_subject.avg_sem1 < 8:
                        has_behavior_grade_below_8 = True
                else:
                    if catalog_per_subject.is_coordination_subject:
                        continue

                    if last_month_of_first_semester <= today < first_semester_report_date:
                        if catalog_per_subject.avg_sem1 and catalog_per_subject.avg_sem1 < 5:
                            subjects_with_avg_below_limit.append(catalog_per_subject.subject_name)
                    elif last_month_of_second_semester <= today < second_semester_report_date:
                        if catalog_per_subject.avg_sem2 and catalog_per_subject.avg_sem2 < 5:
                            subjects_with_avg_below_limit.append(catalog_per_subject.subject_name)

            # Send alerts
            user_profiles_ids = list(student.parents.values_list('id', flat=True)) + [catalog.study_class.class_master_id]
            send_alert_for_subjects_below_limit(subjects_with_avg_below_limit, student, user_profiles_ids)
            send_alert_for_behavior_grade_below_8(has_behavior_grade_below_8, student, user_profiles_ids)


def send_alert_for_subjects_below_limit(subjects_with_avg_below_limit, student, user_profiles_ids):
    if not subjects_with_avg_below_limit:
        return

    subjects_with_avg_below_limit = sorted(subjects_with_avg_below_limit)
    title = AVG_BELOW_LIMIT_TITLE.format(5, student.full_name)
    subjects = ", ".join([get_subject_initials(subject) for subject in subjects_with_avg_below_limit])
    body = AVG_BELOW_LIMIT_BODY.format(student.full_name, 5, subjects)
    format_and_send_notification_task(title, body, user_profiles_ids, False)


def send_alert_for_behavior_grade_below_8(has_behavior_grade_below_8, student, user_profiles_ids):
    if not has_behavior_grade_below_8:
        return

    title = BEHAVIOR_GRADE_BELOW_8_TITLE.format(student.full_name)
    body = BEHAVIOR_GRADE_BELOW_8_BODY.format(student.full_name)
    format_and_send_notification_task(title, body, user_profiles_ids, False)


def get_next_monday_for_date(date):
    days_ahead = 7 - date.weekday()
    return date + timezone.timedelta(days=days_ahead)


def get_second_semester_report_date(current_calendar, second_semester_end_events, class_grade_arabic, is_technological_school):
    second_semester_end_event = None
    if class_grade_arabic == 8:
        second_semester_end_event = second_semester_end_events.get(SchoolEvent.EventTypes.SECOND_SEMESTER_END_VIII_GRADE)
    elif class_grade_arabic in [9, 10, 11]:
        if is_technological_school:
            second_semester_end_event = second_semester_end_events.get(SchoolEvent.EventTypes.SECOND_SEMESTER_END_IX_XI_FILIERA_TEHNOLOGICA)
    elif class_grade_arabic in [12, 13]:
        second_semester_end_event = second_semester_end_events.get(SchoolEvent.EventTypes.SECOND_SEMESTER_END_XII_XIII_GRADE)

    second_semester_end = second_semester_end_event.ends_at if second_semester_end_event else current_calendar.second_semester.ends_at
    return get_next_monday_for_date(second_semester_end)
