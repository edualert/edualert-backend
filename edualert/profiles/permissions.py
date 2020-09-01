from edualert.common.constants import GET
from edualert.common.permissions import BaseUserRolePermissionClass
from edualert.profiles.models import UserProfile


class UserDetailPermissionClass(BaseUserRolePermissionClass):
    def has_permission(self, request, view):
        if request.method == GET:
            self.allowed_user_roles = (UserProfile.UserRoles.ADMINISTRATOR, UserProfile.UserRoles.PRINCIPAL, UserProfile.UserRoles.TEACHER,
                                       UserProfile.UserRoles.PARENT, UserProfile.UserRoles.STUDENT)
        else:
            self.allowed_user_roles = (UserProfile.UserRoles.ADMINISTRATOR, UserProfile.UserRoles.PRINCIPAL)

        return super().has_permission(request, view)
