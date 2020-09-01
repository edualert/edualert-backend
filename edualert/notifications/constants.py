from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _

from edualert.profiles.constants import UserRoles


class ReceiverTypes(TextChoices):
    CLASS_STUDENTS = 'CLASS_STUDENTS', _("Class students")
    CLASS_PARENTS = 'CLASS_PARENTS', _("Class parents")
    ONE_STUDENT = 'ONE_STUDENT', _("One student")
    ONE_PARENT = 'ONE_PARENT', _("One parent")


TARGET_USERS_ROLE_MAP = {
    ReceiverTypes.CLASS_STUDENTS: UserRoles.STUDENT,
    ReceiverTypes.CLASS_PARENTS: UserRoles.PARENT,
    ReceiverTypes.ONE_STUDENT: UserRoles.STUDENT,
    ReceiverTypes.ONE_PARENT: UserRoles.PARENT,
}


# Emails / SMS
NEW_MESSAGE_TITLE = 'Mesaj nou'
NEW_MESSAGE_BODY = 'Aveți un mesaj nou în platforma EduAlert.'
