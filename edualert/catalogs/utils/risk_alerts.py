from django.utils import timezone

from edualert.academic_calendars.models import SchoolEvent
from edualert.academic_calendars.utils import get_current_academic_calendar
from edualert.catalogs.constants import AVG_BELOW_7_TITLE, AVG_BELOW_7_BODY, AVG_BELOW_LIMIT_TITLE, AVG_BELOW_LIMIT_BODY, \
    BEHAVIOR_GRADE_BELOW_10_TITLE, BEHAVIOR_GRADE_BELOW_10_BODY, BEHAVIOR_GRADE_BELOW_8_TITLE, BEHAVIOR_GRADE_BELOW_8_BODY, \
    ABSENCES_BETWEEN_1_3_TITLE, ABSENCES_BETWEEN_1_3_BODY, ABSENCES_ABOVE_3_TITLE, ABSENCES_ABOVE_3_BODY, \
    ABSENCES_ABOVE_LIMIT_TITLE, ABSENCES_ABOVE_LIMIT_BODY
from edualert.catalogs.models import StudentCatalogPerYear
from edualert.catalogs.utils import has_technological_category, get_avg_limit_for_subject
from edualert.catalogs.utils.risk_levels import get_second_semester_end_events, get_mapped_catalogs_per_subject
from edualert.notifications.tasks import format_and_send_notification_task
from edualert.schools.models import RegisteredSchoolUnit


def send_alerts_for_risks():
    today = timezone.now().date()

    current_calendar = get_current_academic_calendar()
    if not current_calendar:
        return
    second_semester_end_events = get_second_semester_end_events(current_calendar)
    first_semester_report_date = get_next_monday_for_date(current_calendar.first_semester.ends_at)

    for school_unit in RegisteredSchoolUnit.objects.select_related('academic_profile').all():
        is_technological_school = has_technological_category(school_unit)
        school_academic_profile = school_unit.academic_profile

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
            subjects_with_1_3_absences = []
            subjects_with_more_than_3_absences = []
            subjects_with_avg_below_7 = []
            subjects_with_avg_below_limit = []
            has_behavior_grade_below_10 = False
            has_behavior_grade_below_8 = False
            avg_type = ''

            current_semester = None
            semester_unfounded_absences_count = 0
            if today < first_semester_report_date:
                current_semester = 1
            elif today < second_semester_report_date:
                current_semester = 2

            for catalog_per_subject in student_catalogs_per_subject:
                if current_semester:
                    absences_count = catalog_per_subject.absences.filter(is_founded=False, semester=current_semester).count()
                    if 1 <= absences_count <= 3:
                        subjects_with_1_3_absences.append(catalog_per_subject.subject_name)
                    elif absences_count > 3:
                        subjects_with_more_than_3_absences.append(catalog_per_subject.subject_name)

                if today == first_semester_report_date:
                    avg_type = 'semestrială'
                    if catalog_per_subject.is_coordination_subject:
                        if catalog_per_subject.avg_sem1 and catalog_per_subject.avg_sem1 < 8:
                            has_behavior_grade_below_8 = True
                        elif catalog_per_subject.avg_sem1 and catalog_per_subject.avg_sem1 < 10:
                            has_behavior_grade_below_10 = True
                    else:
                        avg_limit = get_avg_limit_for_subject(catalog.study_class, False, catalog_per_subject.subject_id, school_academic_profile)
                        if catalog_per_subject.avg_sem1 and catalog_per_subject.avg_sem1 < avg_limit:
                            subjects_with_avg_below_limit.append((avg_limit, catalog_per_subject.subject_name))
                        elif catalog_per_subject.avg_sem1 and catalog_per_subject.avg_sem1 < 7:
                            subjects_with_avg_below_7.append(catalog_per_subject.subject_name)
                elif today == second_semester_report_date:
                    avg_type = 'anuală'
                    if catalog_per_subject.is_coordination_subject:
                        if catalog_per_subject.avg_final and catalog_per_subject.avg_final < 10:
                            has_behavior_grade_below_10 = True
                    else:
                        if catalog_per_subject.avg_final and catalog_per_subject.avg_final < 7:
                            subjects_with_avg_below_7.append(catalog_per_subject.subject_name)

            if current_semester:
                semester_unfounded_absences_count = student.absences.filter(academic_year=current_calendar.academic_year,
                                                                            semester=current_semester, is_founded=False).count()

            # Send alerts
            user_profiles_ids = list(student.parents.values_list('id', flat=True)) + [catalog.study_class.class_master_id]
            send_alert_for_1_3_absences(subjects_with_1_3_absences, student, user_profiles_ids)
            send_alert_for_more_than_3_absences(subjects_with_more_than_3_absences, student, user_profiles_ids)
            send_alert_for_absences_above_limit(semester_unfounded_absences_count, student, user_profiles_ids)
            send_alert_for_subjects_with_avg_below_7(subjects_with_avg_below_7, student, avg_type, user_profiles_ids)
            send_alert_for_subjects_below_limit(subjects_with_avg_below_limit, student, user_profiles_ids)
            sent_alert_for_behavior_grade_below_10(has_behavior_grade_below_10, student, avg_type, user_profiles_ids)
            send_alert_for_behavior_grade_below_8(has_behavior_grade_below_8, student, user_profiles_ids)


def send_alert_for_1_3_absences(subjects_with_1_3_absences, student, user_profiles_ids):
    if not subjects_with_1_3_absences:
        return
    title = ABSENCES_BETWEEN_1_3_TITLE.format(student.full_name)
    body = ''
    for subject_name in subjects_with_1_3_absences:
        body += ABSENCES_BETWEEN_1_3_BODY.format(subject_name)
    format_and_send_notification_task(title, body, user_profiles_ids, True)


def send_alert_for_more_than_3_absences(subjects_with_more_than_3_absences, student, user_profiles_ids):
    if not subjects_with_more_than_3_absences:
        return
    title = ABSENCES_ABOVE_3_TITLE.format(student.full_name)
    body = ''
    for subject_name in subjects_with_more_than_3_absences:
        body += ABSENCES_ABOVE_3_BODY.format(subject_name)
    format_and_send_notification_task(title, body, user_profiles_ids, True)


def send_alert_for_absences_above_limit(semester_unfounded_absences_count, student, user_profiles_ids):
    if semester_unfounded_absences_count <= 10:
        return
    if semester_unfounded_absences_count > 30:
        absences_limit = 30
    elif semester_unfounded_absences_count > 20:
        absences_limit = 20
    else:
        absences_limit = 10
    title = ABSENCES_ABOVE_LIMIT_TITLE.format(absences_limit, student.full_name)
    body = ABSENCES_ABOVE_LIMIT_BODY.format(absences_limit)
    format_and_send_notification_task(title, body, user_profiles_ids, True)


def send_alert_for_subjects_with_avg_below_7(subjects_with_avg_below_7, student, avg_type, user_profiles_ids):
    if not subjects_with_avg_below_7:
        return
    title = AVG_BELOW_7_TITLE.format(student.full_name)
    body = ''
    for subject_name in subjects_with_avg_below_7:
        body += AVG_BELOW_7_BODY.format(avg_type, subject_name)
    format_and_send_notification_task(title, body, user_profiles_ids, True)


def send_alert_for_subjects_below_limit(subjects_with_avg_below_limit, student, user_profiles_ids):
    if not subjects_with_avg_below_limit:
        return
    title = AVG_BELOW_LIMIT_TITLE.format(subjects_with_avg_below_limit[0][0], student.full_name)
    body = ''
    for subject in subjects_with_avg_below_limit:
        body += AVG_BELOW_LIMIT_BODY.format(subject[0], subject[1])
    format_and_send_notification_task(title, body, user_profiles_ids, True)


def sent_alert_for_behavior_grade_below_10(has_behavior_grade_below_10, student, avg_type, user_profiles_ids):
    if not has_behavior_grade_below_10:
        return
    title = BEHAVIOR_GRADE_BELOW_10_TITLE.format(student.full_name)
    body = BEHAVIOR_GRADE_BELOW_10_BODY.format(avg_type)
    format_and_send_notification_task(title, body, user_profiles_ids, True)


def send_alert_for_behavior_grade_below_8(has_behavior_grade_below_8, student, user_profiles_ids):
    if not has_behavior_grade_below_8:
        return
    title = BEHAVIOR_GRADE_BELOW_8_TITLE.format(student.full_name)
    body = BEHAVIOR_GRADE_BELOW_8_BODY
    format_and_send_notification_task(title, body, user_profiles_ids, True)


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
