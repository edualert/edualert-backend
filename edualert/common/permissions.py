from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import IsAuthenticated

from edualert.profiles.models import UserProfile


class BaseUserRolePermissionClass(IsAuthenticated):
    """
    Base permission class that checks whether the request's user profile is of a certain role.
    The required role can be overridden by all extending classes by setting allowed_user_role to a tuple of roles.
    """

    allowed_user_roles = None

    def has_permission(self, request, view):
        has_user_profile = super().has_permission(request, view)

        try:
            allowed_roles = tuple(self.allowed_user_roles)
        except TypeError:
            raise Exception(_("allowed_user_roles must be a tuple."))

        return has_user_profile and request.user.user_profile.user_role in allowed_roles


class IsAdministrator(BaseUserRolePermissionClass):
    allowed_user_roles = (UserProfile.UserRoles.ADMINISTRATOR,)


class IsPrincipal(BaseUserRolePermissionClass):
    allowed_user_roles = (UserProfile.UserRoles.PRINCIPAL,)


class IsTeacher(BaseUserRolePermissionClass):
    allowed_user_roles = (UserProfile.UserRoles.TEACHER,)


class IsParent(BaseUserRolePermissionClass):
    allowed_user_roles = (UserProfile.UserRoles.PARENT,)


class IsStudent(BaseUserRolePermissionClass):
    allowed_user_roles = (UserProfile.UserRoles.STUDENT,)


class IsAdministratorOrPrincipal(BaseUserRolePermissionClass):
    allowed_user_roles = (UserProfile.UserRoles.ADMINISTRATOR, UserProfile.UserRoles.PRINCIPAL)


class IsTeacherOrPrincipal(BaseUserRolePermissionClass):
    allowed_user_roles = (UserProfile.UserRoles.TEACHER, UserProfile.UserRoles.PRINCIPAL)


class IsAdministratorOrSchoolEmployee(BaseUserRolePermissionClass):
    allowed_user_roles = (UserProfile.UserRoles.ADMINISTRATOR, UserProfile.UserRoles.PRINCIPAL, UserProfile.UserRoles.TEACHER)


class IsParentOrStudent(BaseUserRolePermissionClass):
    allowed_user_roles = (UserProfile.UserRoles.PARENT, UserProfile.UserRoles.STUDENT)
