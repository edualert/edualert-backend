from celery import shared_task
from django.utils import timezone

from edualert.academic_calendars.utils import get_current_academic_calendar, generate_next_year_academic_calendar
from edualert.academic_programs.utils import generate_next_year_academic_programs
from edualert.profiles.constants import FAILING_1_SUBJECT_LABEL, FAILING_2_SUBJECTS_LABEL, EXEMPTED_SPORT_LABEL, EXEMPTED_RELIGION_LABEL
from edualert.profiles.models import Label, UserProfile


@shared_task
def generate_next_study_year_task():
    current_calendar = get_current_academic_calendar()
    if not current_calendar:
        return

    last_event = current_calendar.school_events.order_by('-ends_at').first()
    if last_event and timezone.now().date() == last_event.ends_at + timezone.timedelta(days=1):
        generate_next_year_academic_calendar()
        generate_next_year_academic_programs()
        remove_students_from_study_classes()


def remove_students_from_study_classes():
    labels_to_be_removed = [label for label in Label.objects.filter(text__in=[FAILING_1_SUBJECT_LABEL, FAILING_2_SUBJECTS_LABEL,
                                                                              EXEMPTED_SPORT_LABEL, EXEMPTED_RELIGION_LABEL])]
    students_to_update = []
    for student in UserProfile.objects.filter(user_role=UserProfile.UserRoles.STUDENT, student_in_class__isnull=False):
        student.labels.remove(*labels_to_be_removed)
        student.student_in_class = None
        students_to_update.append(student)
    UserProfile.objects.bulk_update(students_to_update, ['student_in_class'], batch_size=100)
