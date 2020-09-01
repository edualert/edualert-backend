from django.contrib.auth.backends import ModelBackend

from edualert.profiles.models import UserProfile


class CustomModelBackend(ModelBackend):
    def user_can_authenticate(self, user):
        profile = getattr(user, "user_profile", None)
        if not profile:
            return False

        return super().user_can_authenticate(user) and self._has_active_school(profile)

    @staticmethod
    def _has_active_school(profile):
        if profile.user_role == UserProfile.UserRoles.ADMINISTRATOR:
            return True

        if not profile.school_unit or not profile.school_unit.is_active:
            return False

        return True
