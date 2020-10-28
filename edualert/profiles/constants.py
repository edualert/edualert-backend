from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _


class UserRoles(TextChoices):
    ADMINISTRATOR = 'ADMINISTRATOR', _("Administrator")
    PRINCIPAL = 'SCHOOL_PRINCIPAL', _("School Principal")
    TEACHER = 'TEACHER', _("Teacher")
    PARENT = 'PARENT', _("Parent")
    STUDENT = 'STUDENT', _("Student")


# Labels
TRANSFERRED_LABEL = 'Transferat'
EXPELLED_LABEL = 'Exmatriculat'
ABANDONMENT_RISK_1_LABEL = 'Risc Abandon 1'
ABANDONMENT_RISK_2_LABEL = 'Risc Abandon 2'
ABANDONMENT_LABEL = 'Abandon'
FAILING_1_SUBJECT_LABEL = 'Corigent 1 Materie'
FAILING_2_SUBJECTS_LABEL = 'Corigent 2 Materii'
HELD_BACK_LABEL = 'Repetent'
HELD_BACK_ILLNESS_LABEL = 'Repetent Caz Boală'
EXEMPTED_SPORT_LABEL = 'Scutit Educație Fizică'
EXEMPTED_RELIGION_LABEL = 'Scutit Religie'
SUPPORT_GROUP_LABEL = 'Înregistrat Proiect ORS - Grup Suport'
MENTORING_LABEL = 'Înregistrat Proiect ORS - Mentoring'
WORKSHOP_LABEL = 'Înregistrat Proiect ORS - Workshop'
SUMMER_CAMP_LABEL = 'Înregistrat Proiect ORS - Summer Camp'
PSYCHOLOGICAL_COUNSELING_LABEL = 'Consiliere Psihologică'

PROJECTS_MAP = {
    SUPPORT_GROUP_LABEL: 'Proiect ORS - Grup Suport',
    MENTORING_LABEL: 'Proiect ORS - Mentoring',
    WORKSHOP_LABEL: 'Proiect ORS - Workshop',
    SUMMER_CAMP_LABEL: 'Proiect ORS - Summer Camp',
    PSYCHOLOGICAL_COUNSELING_LABEL: 'Proiect Consiliere Psihologică'
}

# Emails / SMS
ABANDONMENT_RISK_TITLE = 'Risc abandon școlar - {}'
ABANDONMENT_RISK_BODY = 'Elevul {} este în situație de risc abandon școlar, grad {}.'

TRANSFERRED_TITLE = 'Transfer - {}'
TRANSFERRED_BODY = 'Elevul {} este în situație de transfer între școli.'

EXPELLED_TITLE = 'Exmatriculare - {}'
EXPELLED_BODY = 'Elevul {} a fost exmatriculat.'

ABANDONMENT_TITLE = 'Abandon școlar - {}'
ABANDONMENT_BODY = 'Elevul {} este în situație de abandon școlar.'

FAILING_SUBJECTS_TITLE = 'Corigență - {}'
FAILING_SUBJECTS_BODY = 'Elevul {} este corigent la materiile: {}.'

HELD_BACK_TITLE = 'Repetare an școlar - {}'
HELD_BACK_BODY = 'Elevul {} este repetent.'

EXEMPTED_TITLE = 'Scutire materie - {}'
EXEMPTED_BODY = 'Elevul {} este scutit de {}.'

PROGRAM_ENROLLMENT_TITLE = 'Înrolare program prevenție abandon școlar - {}'
PROGRAM_ENROLLMENT_BODY = 'Elevul {} este înrolat în {}.'

ACCOUNT_CHANGED_TITLE = 'Contul EduAlert'
ACCOUNT_ACTIVATED_BODY = 'Contul EduAlert a fost reactivat.'
ACCOUNT_DEACTIVATED_BODY = 'Contul EduAlert a fost dezactivat.'

RESET_PASSWORD_TITLE = 'Resetare parolă'
RESET_PASSWORD_BODY_EMAIL = 'Pentru resetarea parolei pentru platforma EduAlert, accesați linkul de mai jos și urmați instrucțiunile:\n' \
                            '{}\n' \
                            'Dacă nu ați cerut resetarea parolei din platforma EduAlert ignorați acest email.'
RESET_PASSWORD_BODY_SMS = 'Click pentru resetare parolă EduAlert: {}.'
