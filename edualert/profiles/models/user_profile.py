from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q
from django.db.models.signals import m2m_changed
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel

from edualert.profiles import constants
from edualert.profiles.signals import post_add_labels


class UserProfile(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="user_profile")
    school_unit = models.ForeignKey("schools.RegisteredSchoolUnit", related_name="user_profiles",
                                    related_query_name="user_profile", null=True, blank=True, on_delete=models.SET_NULL)

    UserRoles = constants.UserRoles
    user_role = models.CharField(choices=UserRoles.choices, max_length=100)

    # These fields are duplicated from django.contrib.auth.models.User
    username = models.CharField(max_length=150, unique=True, help_text=_("Same username as auth User."))
    is_active = models.BooleanField(default=True)

    full_name = models.CharField(max_length=180)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(max_length=150, null=True, blank=True)
    use_phone_as_username = models.BooleanField(default=False)
    email_notifications_enabled = models.BooleanField(default=True)
    sms_notifications_enabled = models.BooleanField(default=True)
    push_notifications_enabled = models.BooleanField(default=True)
    last_online = models.DateTimeField(null=True, blank=True)

    last_change_in_catalog = models.DateTimeField(null=True, blank=True, help_text=_("Only for teachers and school principals."))
    taught_subjects = models.ManyToManyField("subjects.Subject", related_name="teachers", blank=True,
                                             help_text=_("Only for teachers."))

    parents = models.ManyToManyField("self", related_name="children", related_query_name="child", blank=True,
                                     help_text=_("Only for students."), symmetrical=False)
    educator_full_name = models.CharField(max_length=180, null=True, blank=True, help_text=_("Only for students."))
    educator_phone_number = models.CharField(max_length=20, null=True, blank=True, help_text=_("Only for students."))
    educator_email = models.EmailField(max_length=150, null=True, blank=True, help_text=_("Only for students."))
    personal_id_number = models.CharField(max_length=13, null=True, blank=True, help_text=_("Only for students."))
    address = models.CharField(max_length=100, null=True, blank=True, help_text=_("Only for students and parents."))
    birth_date = models.DateField(null=True, blank=True, help_text=_("Only for students."))
    student_in_class = models.ForeignKey("study_classes.StudyClass", null=True, blank=True, related_name="students",
                                         related_query_name="student", on_delete=models.SET_NULL, help_text=_("Only for students."))

    is_at_risk = models.BooleanField(default=False, help_text=_("Only for students."))
    risk_description = models.CharField(max_length=254, null=True, blank=True, help_text=_("Only for students."))

    labels = models.ManyToManyField("profiles.label", related_name="user_profile_set", related_query_name="profile",
                                    blank=True)

    objects = models.Manager()

    def __str__(self):
        return f"UserProfile {self.id} {self.username}"

    @property
    def risk_alerts(self):
        from edualert.notifications.models import TargetUserThrough
        target_user_through_qs = TargetUserThrough.objects.select_related('notification', 'user_profile') \
            .filter(Q(user_profile_id=self.id) | Q(children__id=self.id)).order_by('notification__created')

        if len(target_user_through_qs) == 0:
            return {}

        dates = set()
        alerted_users = []
        alerted_users_ids = []

        for target_user_through in target_user_through_qs:
            target_user = target_user_through.user_profile
            if target_user.id in alerted_users_ids:
                continue
            alerted_users_ids.append(target_user.id)
            dates.add(target_user_through.notification.created.date())
            alerted_users.append({
                "id": target_user.id,
                "user_role": target_user.user_role,
                "full_name": target_user.full_name,
                "email": target_user_through.sent_at_email,
                "phone_number": target_user_through.sent_at_phone_number
            })

        return {
            "dates": dates,
            "alerted_users": alerted_users
        }


m2m_changed.connect(post_add_labels, sender=UserProfile.labels.through)
