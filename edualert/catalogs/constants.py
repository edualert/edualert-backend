from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _


class GradeTypes(TextChoices):
    REGULAR = 'REGULAR', _("Regular")
    THESIS = 'THESIS', _("Thesis")


class ExaminationTypes(TextChoices):
    WRITTEN = 'WRITTEN', _("Written")
    ORAL = 'ORAL', _("Oral")


class ExaminationGradeTypes(TextChoices):
    SECOND_EXAMINATION = 'SECOND_EXAMINATION', _('Second examination')
    DIFFERENCE = 'DIFFERENCE', _('Difference')


# Emails / SMS
AVG_BELOW_7_TITLE = 'Medie sub 7 - {}'
AVG_BELOW_7_BODY = 'Elevul are o medie {} sub 7 la materia {}.\n'

AVG_BELOW_LIMIT_TITLE = 'Medie sub {} - {}'
AVG_BELOW_LIMIT_BODY = 'Elevul are o medie semestrială sub {} la materia {}.\n'

BEHAVIOR_GRADE_BELOW_10_TITLE = 'Notă purtare sub 10 - {}'
BEHAVIOR_GRADE_BELOW_10_BODY = 'Elevul are o notă {} sub 10 la purtare.'

BEHAVIOR_GRADE_BELOW_8_TITLE = 'Notă purtare sub 8 - {}'
BEHAVIOR_GRADE_BELOW_8_BODY = 'Elevul are o notă semestrială sub 8 la purtare.'

ABSENCES_BETWEEN_1_3_TITLE = 'Număr absențe nemotivate materie între 1 și 3 - {}'
ABSENCES_BETWEEN_1_3_BODY = 'Elevul are un număr de absențe nemotivate între 1 și 3 la materia {}.\n'

ABSENCES_ABOVE_3_TITLE = 'Număr absențe nemotivate materie mai mare ca 3 - {}'
ABSENCES_ABOVE_3_BODY = 'Elevul are un număr de absențe nemotivate mai mare ca 3 la materia {}.\n'

ABSENCES_ABOVE_LIMIT_TITLE = 'Număr total absențe nemotivate semestru mai mare ca {} - {}'
ABSENCES_ABOVE_LIMIT_BODY = 'Elevul are un număr total de absențe nemotivate pe semestru mai mare ca {}.'

SCHOOL_SITUATION_SMS_BODY = 'EduAlert - Situație {} {}. Note: {}. Absențe nemotivate: {}.'
SCHOOL_SITUATION_EMAIL_TITLE = 'Situație școlară {} {}'
SCHOOL_SITUATION_EMAIL_BODY = 'Bună ziua!\n\n' \
                              'Acesta este un raport săptămânal automat cu privire la situația școlară a lui {} pentru perioada {}.\n\n' \
                              'Note: {}.\n\n' \
                              'Absențe nemotivate: {}.'
SCHOOL_SITUATION_EMAIL_SIGNATURE = 'Gânduri bune,\n{}'
