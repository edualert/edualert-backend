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
AVG_BELOW_LIMIT_TITLE = 'Medii sub {} - {}'
AVG_BELOW_LIMIT_BODY = 'Elevul {} are media semestrială sub {} la materiile: {}.'

BEHAVIOR_GRADE_BELOW_8_TITLE = 'Notă purtare sub 8 - {}'
BEHAVIOR_GRADE_BELOW_8_BODY = 'Elevul {} are nota semestrială sub 8 la purtare.'

ABSENCES_ABOVE_LIMIT_TITLE = 'Absențe nemotivate - {}'
ABSENCES_ABOVE_LIMIT_BODY = 'Elevul {} are {} absențe nemotivate în acest semestru.'

SCHOOL_SITUATION_SMS_BODY = 'EduAlert - Situație {} {}. Note: {}. Absențe nemotivate: {}.'
SCHOOL_SITUATION_EMAIL_TITLE = 'Situație școlară {} {}'
SCHOOL_SITUATION_EMAIL_BODY = 'Bună ziua!\n\n' \
                              'Acesta este un raport săptămânal automat cu privire la situația școlară a lui {} pentru perioada {}.\n\n' \
                              'Note: {}.\n\n' \
                              'Absențe nemotivate: {}.'
SCHOOL_SITUATION_EMAIL_SIGNATURE = 'Gânduri bune,\n{}'
