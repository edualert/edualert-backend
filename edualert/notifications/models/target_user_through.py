from django.db import models
from django.utils.translation import gettext_lazy as _

from edualert.notifications.constants import NEW_MESSAGE_TITLE, NEW_MESSAGE_BODY
from edualert.notifications.tasks import format_and_send_notification_task


class TargetUserThroughManager(models.Manager):
    def create_and_send(self, *args, **kwargs):
        instance = super(TargetUserThroughManager, self).create(*args, **kwargs)
        # format_and_send_notification_task.delay(NEW_MESSAGE_TITLE, NEW_MESSAGE_BODY, [instance.user_profile.id], not instance.notification.send_sms)
        format_and_send_notification_task.delay(NEW_MESSAGE_TITLE, NEW_MESSAGE_BODY, [instance.user_profile.id], True)
        return instance

    def bulk_create_and_send(self, *args, **kwargs):
        instances = super(TargetUserThroughManager, self).bulk_create(*args, **kwargs)
        target_through_by_notification = {}
        for instance in instances:
            if instance.notification_id in target_through_by_notification:
                target_through_by_notification[instance.notification_id]['user_profile_id_set'].append(instance.user_profile_id)
            else:
                target_through_by_notification[instance.notification_id] = {
                    'notification': instance.notification,
                    'user_profile_id_set': [instance.user_profile_id]
                }

        for notification_id, data in target_through_by_notification.items():
            # format_and_send_notification_task.delay(NEW_MESSAGE_TITLE, NEW_MESSAGE_BODY, data['user_profile_id_set'], not data['notification'].send_sms)
            format_and_send_notification_task.delay(NEW_MESSAGE_TITLE, NEW_MESSAGE_BODY, data['user_profile_id_set'], True)

        return instances


class TargetUserThrough(models.Model):
    notification = models.ForeignKey("notifications.Notification", on_delete=models.CASCADE,
                                     related_name="target_users_through", related_query_name="target_user_through")
    user_profile = models.ForeignKey("profiles.UserProfile", on_delete=models.CASCADE,
                                     related_name="target_users_through", related_query_name="target_user_through")

    user_profile_full_name = models.CharField(max_length=180)
    sent_at_email = models.EmailField(max_length=150, null=True, blank=True)
    sent_at_phone_number = models.CharField(max_length=20, null=True, blank=True)
    is_read = models.BooleanField(default=False)

    children = models.ManyToManyField("profiles.UserProfile", blank=True, related_name="+",
                                      help_text=_("Only if the target is one parent."))

    objects = TargetUserThroughManager()

    def __str__(self):
        return f"TargetUserThrough {self.id} {self.notification} - {self.user_profile_full_name}"
