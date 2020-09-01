from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _


class CategoryLevels(TextChoices):
    PRIMARY_SCHOOL = 'PRIMARY_SCHOOL', _("Primary school")
    SECONDARY_SCHOOL = 'SECONDARY_SCHOOL', _("Secondary school")
    HIGHSCHOOL = 'HIGHSCHOOL', _("Highschool")


BEHAVIOR_GRADE_EXCEPTIONS_PROFILES = ['Pedagogic', 'Militar', 'Teologic']
PROFILES_WITH_CORE_SUBJECTS = ['Artistic', 'Sportiv']
