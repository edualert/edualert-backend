from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _


class EventTypes(TextChoices):
    SECOND_SEMESTER_END_VIII_GRADE = 'SECOND_SEMESTER_END_VIII_GRADE', _("Semester II end for VIII grade")
    SECOND_SEMESTER_END_XII_XIII_GRADE = 'SECOND_SEMESTER_END_XII_XIII_GRADE', \
                                         _("Semester II end for XII & XIII grade ('seral & frecvență redusă')")
    SECOND_SEMESTER_END_IX_XI_FILIERA_TEHNOLOGICA = 'SECOND_SEMESTER_END_IX_XI_FILIERA_TEHNOLOGICA', \
                                                    _("Semester II end for IX-XI grades, profile 'Filieră Tehnologică'")
    I_IV_GRADES_AUTUMN_HOLIDAY = 'I_IV_GRADES_AUTUMN_HOLIDAY', _("I-IV grades autumn holiday")
    WINTER_HOLIDAY = 'WINTER_HOLIDAY', _("Winter holiday")
    SPRING_HOLIDAY = 'SPRING_HOLIDAY', _("Spring holiday")
    LEGAL_PUBLIC_HOLIDAY = 'LEGAL_PUBLIC_HOLIDAY', _("Legal/Public holiday")
    CORIGENTE = 'CORIGENTE', _("Corigente")
    DIFERENTE = 'DIFERENTE', _("Diferente")


SEMESTER_END_EVENTS = [
    EventTypes.SECOND_SEMESTER_END_VIII_GRADE,
    EventTypes.SECOND_SEMESTER_END_XII_XIII_GRADE,
    EventTypes.SECOND_SEMESTER_END_IX_XI_FILIERA_TEHNOLOGICA
]
