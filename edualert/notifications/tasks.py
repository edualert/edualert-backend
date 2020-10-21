from celery import shared_task
from django.conf import settings
from django.template.loader import get_template

from edualert.notifications.utils import send_mass_mail, send_mail, send_sms


@shared_task
def format_and_send_notification_task(subject, body, user_profile_ids, should_send_sms, show_my_account=True):
    from edualert.profiles.models import UserProfile
    mails_to_send = []
    sms_to_send = []

    text_message = get_template('message.txt').render(context={'body': body})
    bodies = {
        'text/html': get_template('message.html').render(context={'title': subject, 'body': body,
                                                                  'frontend_url': settings.FRONTEND_URL,
                                                                  'show_my_account': show_my_account,
                                                                  'signature': 'Echipa EduAlert'}),
    }

    for profile_id in user_profile_ids:
        profile = UserProfile.objects.filter(id=profile_id).first()

        if not profile:
            continue

        if profile.email_notifications_enabled and profile.email:
            mails_to_send.append([subject, bodies, settings.SERVER_EMAIL, [profile.email]])

        if should_send_sms and profile.sms_notifications_enabled and profile.phone_number:
            phone_number = profile.phone_number if profile.phone_number.startswith('+') or profile.phone_number.startswith('00') \
                else '+4' + profile.phone_number
            sms_to_send.append((phone_number, text_message))

    if len(mails_to_send) > 1:
        send_mass_mail(mails_to_send)
    elif len(mails_to_send) == 1:
        send_mail(*mails_to_send[0])

    if sms_to_send:
        send_sms(sms_to_send)
