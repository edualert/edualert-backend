from django.conf import settings
from django.template.loader import get_template
from django.utils import timezone

from edualert.catalogs.constants import SCHOOL_SITUATION_SMS_BODY, SCHOOL_SITUATION_EMAIL_TITLE, SCHOOL_SITUATION_EMAIL_BODY, SCHOOL_SITUATION_EMAIL_SIGNATURE
from edualert.catalogs.models import SubjectGrade, SubjectAbsence
from edualert.notifications.utils import send_sms, send_mail
from edualert.profiles.models import UserProfile
from edualert.schools.models import RegisteredSchoolUnit


def send_alerts_for_school_situation():
    today = timezone.now().date()
    one_week_ago = today - timezone.timedelta(days=7)
    yesterday = today - timezone.timedelta(days=1)
    time_period = get_time_period(one_week_ago, yesterday)

    for school_unit in RegisteredSchoolUnit.objects.all():
        for student in UserProfile.objects.filter(school_unit_id=school_unit.id, user_role=UserProfile.UserRoles.STUDENT, is_active=True):
            unfounded_absences_count = SubjectAbsence.objects.filter(student_id=student.id, taken_at__gte=one_week_ago, taken_at__lt=yesterday, is_founded=False).count()
            grades = SubjectGrade.objects.filter(student_id=student.id, taken_at__gte=one_week_ago, taken_at__lt=yesterday)

            if unfounded_absences_count == 0 and grades.count() == 0:
                continue

            parents_with_emails = []
            parents_with_phone_numbers = []
            for parent in student.parents.all():
                if parent.email:
                    parents_with_emails.append(parent)
                elif parent.phone_number:
                    parents_with_phone_numbers.append(parent)

            grouped_grades = group_grades_by_subject(grades)

            if parents_with_emails:
                formatted_grades_for_email = format_grades_for_email(grouped_grades)
                format_and_send_school_situation_email(student.full_name, time_period, formatted_grades_for_email, unfounded_absences_count,
                                                       school_unit.name, parents_with_emails)
            if parents_with_phone_numbers:
                student_initials = "".join([word[0] for word in student.full_name.split(" ")])
                formatted_grades_for_sms = format_grades_for_email(grouped_grades, True)
                format_and_send_school_situation_sms(student_initials, time_period, formatted_grades_for_sms, unfounded_absences_count,
                                                     parents_with_phone_numbers)


def get_time_period(one_week_ago, yesterday):
    if one_week_ago.month == yesterday.month:
        return "{}-{}.{}.{}".format(one_week_ago.day, yesterday.day, yesterday.month, yesterday.year)

    return "{}.{}.{}-{}.{}.{}".format(one_week_ago.day, one_week_ago.month, one_week_ago.year,
                                      yesterday.day, yesterday.month, yesterday.year)


def group_grades_by_subject(grades):
    grouped_grades = {}

    for subject_grade in grades:
        if subject_grade.subject_name not in grouped_grades:
            grouped_grades[subject_grade.subject_name] = []
        grouped_grades[subject_grade.subject_name].append(subject_grade.grade)

    return grouped_grades


def get_subject_initials(subject_name):
    subject_name_words = subject_name.split(" ")

    if len(subject_name_words) == 0:
        return ""
    if len(subject_name_words) == 1:
        return subject_name_words[0][0:3]
    if len(subject_name_words) == 2:
        return "{}{}".format(subject_name_words[0][0], subject_name_words[1][0:2])

    return "{}{}{}".format(subject_name_words[0][0], subject_name_words[1][0], subject_name_words[2][0])


def format_grades_for_email(grouped_grades, is_for_sms=False):
    formatted_grades_per_subject = []

    for subject_name, grades_list in grouped_grades.items():
        if is_for_sms:
            subject_name = get_subject_initials(subject_name)
        formatted_grades_per_subject.append("{} {}".format(subject_name, " ; ".join(grades_list)))

    return ", ".join(formatted_grades_per_subject)


def format_and_send_school_situation_email(student_name, time_period, formatted_grades, unfounded_absences_count, school_name, parents):
    email_title = SCHOOL_SITUATION_EMAIL_TITLE.format(student_name, time_period)

    bodies = {
        'text/html': get_template('message.html').render(context={'title': email_title,
                                                                  'body': SCHOOL_SITUATION_EMAIL_BODY.format(student_name, time_period, formatted_grades, unfounded_absences_count),
                                                                  'show_my_account': False,
                                                                  'signature': SCHOOL_SITUATION_EMAIL_SIGNATURE.format(school_name)}),
    }
    send_mail(email_title, bodies, settings.SERVER_EMAIL, [parent.email for parent in parents])


def format_and_send_school_situation_sms(student_initials, time_period, formatted_grades, unfounded_absences_count, parents):
    text_message = SCHOOL_SITUATION_SMS_BODY.format(student_initials, time_period, formatted_grades, unfounded_absences_count)

    sms_to_send = []
    for parent in parents:
        phone_number = parent.phone_number if parent.phone_number.startswith('+') or parent.phone_number.startswith('00') \
            else '+4' + parent.phone_number
        sms_to_send.append((phone_number, text_message))

    send_sms(sms_to_send)
