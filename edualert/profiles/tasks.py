from copy import copy

from celery import shared_task
from django.conf import settings
from django.template.loader import get_template

from edualert.notifications.tasks import format_and_send_notification_task
from edualert.notifications.utils import send_mail, send_sms
from edualert.profiles.constants import TRANSFERRED_LABEL, EXPELLED_LABEL, \
    ABANDONMENT_RISK_1_LABEL, ABANDONMENT_RISK_2_LABEL, ABANDONMENT_LABEL, \
    HELD_BACK_LABEL, HELD_BACK_ILLNESS_LABEL, EXEMPTED_SPORT_LABEL, EXEMPTED_RELIGION_LABEL, \
    SUPPORT_GROUP_LABEL, MENTORING_LABEL, WORKSHOP_LABEL, SUMMER_CAMP_LABEL, PSYCHOLOGICAL_COUNSELING_LABEL, \
    ABANDONMENT_RISK_TITLE, ABANDONMENT_RISK_BODY, TRANSFERRED_TITLE, TRANSFERRED_BODY, \
    EXPELLED_TITLE, EXPELLED_BODY, ABANDONMENT_TITLE, ABANDONMENT_BODY, \
    HELD_BACK_TITLE, HELD_BACK_BODY, EXEMPTED_TITLE, EXEMPTED_BODY, \
    PROJECTS_MAP, PROGRAM_ENROLLMENT_TITLE, PROGRAM_ENROLLMENT_BODY, RESET_PASSWORD_TITLE, RESET_PASSWORD_BODY_EMAIL, RESET_PASSWORD_BODY_SMS


@shared_task
def send_alert_for_labels(user_profile_id, label_ids):
    from edualert.profiles.models import UserProfile, Label
    profile = UserProfile.objects.filter(id=user_profile_id).select_related('student_in_class', 'school_unit').first()
    if not profile:
        return

    recipient_ids = list(profile.parents.values_list('id', flat=True))
    if profile.student_in_class:
        recipient_ids.append(profile.student_in_class.class_master_id)
    school_principal_id = None
    if profile.school_unit:
        school_principal_id = profile.school_unit.school_principal_id

    labels = Label.objects.filter(id__in=label_ids)
    for label in labels:
        subject = None
        body = None
        send_to_principal = False

        # if label.text == ABANDONMENT_RISK_1_LABEL:
        #     subject = ABANDONMENT_RISK_TITLE.format(profile.full_name)
        #     body = ABANDONMENT_RISK_BODY.format(profile.full_name, 1)
        #     send_to_principal = True
        # elif label.text == ABANDONMENT_RISK_2_LABEL:
        #     subject = ABANDONMENT_RISK_TITLE.format(profile.full_name)
        #     body = ABANDONMENT_RISK_BODY.format(profile.full_name, 2)
        #     send_to_principal = True
        if label.text == TRANSFERRED_LABEL:
            subject = TRANSFERRED_TITLE.format(profile.full_name)
            body = TRANSFERRED_BODY.format(profile.full_name)
            send_to_principal = True
        elif label.text == EXPELLED_LABEL:
            subject = EXPELLED_TITLE.format(profile.full_name)
            body = EXPELLED_BODY.format(profile.full_name)
            send_to_principal = True
        elif label.text == ABANDONMENT_LABEL:
            subject = ABANDONMENT_TITLE.format(profile.full_name)
            body = ABANDONMENT_BODY.format(profile.full_name)
            send_to_principal = True
        elif label.text in [HELD_BACK_LABEL, HELD_BACK_ILLNESS_LABEL]:
            subject = HELD_BACK_TITLE.format(profile.full_name)
            body = HELD_BACK_BODY.format(profile.full_name)
            send_to_principal = True
        elif label.text in [EXEMPTED_SPORT_LABEL, EXEMPTED_RELIGION_LABEL]:
            subject = EXEMPTED_TITLE.format(profile.full_name)
            body = EXEMPTED_BODY.format(profile.full_name, ' '.join(label.text.split(' ')[1:]))
            send_to_principal = False
        elif label.text in [SUPPORT_GROUP_LABEL, MENTORING_LABEL, WORKSHOP_LABEL, SUMMER_CAMP_LABEL, PSYCHOLOGICAL_COUNSELING_LABEL]:
            subject = PROGRAM_ENROLLMENT_TITLE.format(profile.full_name)
            body = PROGRAM_ENROLLMENT_BODY.format(profile.full_name, PROJECTS_MAP[label.text])
            send_to_principal = True

        if subject and body:
            final_recipient_ids = copy(recipient_ids)
            if send_to_principal and school_principal_id:
                final_recipient_ids.append(school_principal_id)
            format_and_send_notification_task(subject, body, final_recipient_ids, False)


@shared_task
def send_reset_password_message(user_profile_id, link):
    from edualert.profiles.models import UserProfile
    profile = UserProfile.objects.filter(id=user_profile_id).first()
    if not profile:
        return

    if profile.email:
        bodies = {
            'text/html': get_template('message.html').render(context={'title': RESET_PASSWORD_TITLE,
                                                                      'body': RESET_PASSWORD_BODY_EMAIL.format(link),
                                                                      'frontend_url': settings.FRONTEND_URL,
                                                                      'show_my_account': False,
                                                                      'signature': 'Echipa EduAlert'}),
        }
        send_mail(RESET_PASSWORD_TITLE, bodies, settings.SERVER_EMAIL, [profile.email])
    elif profile.phone_number:
        phone_number = profile.phone_number if profile.phone_number.startswith('+') or profile.phone_number.startswith('00') \
            else '+4' + profile.phone_number
        text_message = RESET_PASSWORD_BODY_SMS.format(link)
        send_sms([(phone_number, text_message)])
