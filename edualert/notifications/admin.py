from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html, escape

from edualert.notifications.models import Notification, TargetUserThrough


class NotificationAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'title', 'send_sms', 'from_user_link', 'from_user_role',
                    'receiver_type', 'target_users_role', 'target_study_class_link')
    list_filter = ('from_user_role', 'receiver_type', 'target_users_role')
    search_fields = ('title',)
    readonly_fields = ('from_user_full_name', 'from_user_role')

    def from_user_link(self, instance):
        url = reverse("admin:profiles_userprofile_change", args=(instance.from_user.id,))
        return format_html('<a href="{}">{}</a>', url, escape(instance.from_user))

    from_user_link.short_description = "Sender"

    def target_study_class_link(self, instance):
        if instance.target_study_class:
            url = reverse("admin:study_classes_studyclass_change", args=(instance.target_study_class.id,))
            return format_html('<a href="{}">{}</a>', url, escape(instance.target_study_class))
        return '-'

    target_study_class_link.short_description = "Target study class"

    def save_model(self, request, obj, form, change):
        if request.path.endswith('/change/'):
            obj.save()
            return
        obj.from_user_full_name = obj.from_user.full_name
        obj.from_user_role = obj.from_user.user_role
        obj.save()


class TargetUserThroughAdmin(admin.ModelAdmin):
    list_display = ('str_representation', 'notification_link', 'user_profile_link', 'is_read')
    readonly_fields = ('user_profile_full_name', 'sent_at_email', 'sent_at_phone_number')

    def str_representation(self, instance):
        return "TargetUserThroughAdmin {}".format(instance.id)

    str_representation.short_description = "Object"

    def notification_link(self, instance):
        url = reverse("admin:notifications_notification_change", args=(instance.notification.id,))
        return format_html('<a href="{}">{}</a>', url, escape(instance.notification))

    notification_link.short_description = "Notification"

    def user_profile_link(self, instance):
        url = reverse("admin:profiles_userprofile_change", args=(instance.user_profile.id,))
        return format_html('<a href="{}">{}</a>', url, escape(instance.user_profile))

    user_profile_link.short_description = "User profile"

    def save_model(self, request, obj, form, change):
        if request.path.endswith('/change/'):
            obj.save()
            return
        obj.user_profile_full_name = obj.user_profile.full_name
        obj.sent_at_email = obj.user_profile.email
        obj.sent_at_phone_number = obj.user_profile.phone_number
        obj.save()


admin.site.register(Notification, NotificationAdmin)
admin.site.register(TargetUserThrough, TargetUserThroughAdmin)
