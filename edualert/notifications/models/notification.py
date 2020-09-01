from django.db import models
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel

from edualert.notifications import constants
from edualert.notifications.models import TargetUserThrough
from edualert.profiles.constants import UserRoles


class Notification(TimeStampedModel):
    title = models.CharField(max_length=100)
    body = models.TextField()
    send_sms = models.BooleanField(default=False)

    from_user = models.ForeignKey("profiles.UserProfile", related_name="sent_notifications",
                                  related_query_name="sent_notification", on_delete=models.CASCADE)
    from_user_full_name = models.CharField(max_length=180)
    from_user_role = models.CharField(choices=UserRoles.choices, max_length=100)
    from_user_subjects = models.TextField(null=True, blank=True, help_text=_("Concatenated list of sender's taught subjects."))

    ReceiverTypes = constants.ReceiverTypes
    receiver_type = models.CharField(choices=ReceiverTypes.choices, max_length=64)
    target_users_role = models.CharField(choices=UserRoles.choices, max_length=100)
    target_users = models.ManyToManyField("profiles.UserProfile", through=TargetUserThrough, through_fields=('notification', 'user_profile'),
                                          related_name="received_notifications", related_query_name="received_notification")

    target_study_class = models.ForeignKey("study_classes.StudyClass", on_delete=models.SET_NULL, null=True, blank=True,
                                           related_name="received_notifications", related_query_name="received_notification",
                                           help_text=_('For all receiver types except for one parent (who can have children in different study classes).'))

    targets_count = models.PositiveSmallIntegerField(default=0)

    objects = models.Manager()

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return f"Notification {self.id}"
