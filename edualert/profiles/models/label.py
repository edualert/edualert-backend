from django.db import models
from django.utils.translation import gettext_lazy as _

from edualert.profiles.constants import UserRoles


class Label(models.Model):
    text = models.CharField(max_length=100)
    user_role = models.CharField(choices=UserRoles.choices, max_length=100,
                                 help_text=_("Only user profiles with this role can be assigned to this label."))
    is_label_for_transfers_between_schools = models.BooleanField(default=False)

    objects = models.Manager()

    def __str__(self):
        return f"Label {self.id} {self.text}"
