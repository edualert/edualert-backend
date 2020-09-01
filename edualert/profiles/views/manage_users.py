from methodtools import lru_cache

from django.db.models import Case, When, BooleanField
from django.db.models.functions import Lower
from django.utils.translation import gettext as _, get_language_from_request
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status, views
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from edualert.academic_calendars.utils import get_current_academic_calendar
from edualert.catalogs.models import SubjectGrade, SubjectAbsence, ExaminationGrade
from edualert.common.constants import PUT, POST, GET, DELETE, HEAD, OPTIONS
from edualert.common.pagination import CommonPagination
from edualert.common.permissions import IsAdministratorOrPrincipal
from edualert.common.search_and_filters import CommonSearchFilter
from edualert.notifications.tasks import format_and_send_notification_task
from edualert.profiles.constants import ACCOUNT_CHANGED_TITLE, ACCOUNT_ACTIVATED_BODY, ACCOUNT_DEACTIVATED_BODY
from edualert.profiles.import_user_profiles import UserProfileImporter
from edualert.profiles.models import UserProfile
from edualert.profiles.permissions import UserDetailPermissionClass
from edualert.profiles.serializers import UserProfileListSerializer, BaseUserProfileDetailSerializer, \
    SchoolPrincipalSerializer, SchoolTeacherSerializer, ParentSerializer, StudentSerializer, \
    StudentWithRiskAlertsSerializer, DeactivateUserSerializer
from edualert.common.serializers import CsvUploadSerializer


class UserProfileList(generics.ListCreateAPIView):
    permission_classes = (IsAdministratorOrPrincipal,)
    pagination_class = CommonPagination
    search_fields = ['full_name', ]
    filterset_fields = ['user_role', 'is_active']
    filter_backends = [DjangoFilterBackend, CommonSearchFilter]

    def get_serializer_class(self):
        if self.request.method == POST:
            return BaseUserProfileDetailSerializer
        return UserProfileListSerializer

    def get_queryset(self):
        profile = self.request.user.user_profile

        school_filter = {}
        if profile.user_role == UserProfile.UserRoles.ADMINISTRATOR:
            user_roles = [UserProfile.UserRoles.ADMINISTRATOR, UserProfile.UserRoles.PRINCIPAL]
        else:
            user_roles = [UserProfile.UserRoles.TEACHER, UserProfile.UserRoles.PARENT, UserProfile.UserRoles.STUDENT]
            school_filter['school_unit'] = profile.school_unit_id

        return UserProfile.objects.select_related('user') \
            .prefetch_related('labels') \
            .filter(user_role__in=user_roles, user__is_staff=False, **school_filter) \
            .exclude(id=profile.id) \
            .annotate(is_inactive=Case(When(last_online__isnull=True, then=True),
                                       default=False,
                                       output_field=BooleanField())) \
            .order_by('-is_active', 'is_inactive', Lower('full_name'))


class UserProfileDetailBase(generics.GenericAPIView):
    permission_classes = (UserDetailPermissionClass,)
    lookup_field = 'id'

    def get_queryset(self):
        profile = self.request.user.user_profile

        school_filter = {}
        if profile.user_role == UserProfile.UserRoles.ADMINISTRATOR:
            user_roles = [UserProfile.UserRoles.ADMINISTRATOR, UserProfile.UserRoles.PRINCIPAL]
        else:
            user_roles = [UserProfile.UserRoles.TEACHER, UserProfile.UserRoles.PARENT, UserProfile.UserRoles.STUDENT]
            school_filter['school_unit'] = profile.school_unit_id

        return UserProfile.objects.select_related('user', 'student_in_class') \
            .filter(user_role__in=user_roles, user__is_staff=False, **school_filter) \
            .exclude(id=profile.id)

    @lru_cache(maxsize=None)
    def get_object(self):
        return super().get_object()

    def get_serializer_class(self):
        if self.request.method == PUT:
            return BaseUserProfileDetailSerializer

        requested_profile = self.get_object()

        if requested_profile.user_role == UserProfile.UserRoles.PRINCIPAL:
            return SchoolPrincipalSerializer
        if requested_profile.user_role == UserProfile.UserRoles.TEACHER:
            return SchoolTeacherSerializer
        if requested_profile.user_role == UserProfile.UserRoles.PARENT:
            return ParentSerializer
        if requested_profile.user_role == UserProfile.UserRoles.STUDENT:
            if self.request.query_params.get('include_risk_alerts') == 'true':
                return StudentWithRiskAlertsSerializer
            return StudentSerializer

        return BaseUserProfileDetailSerializer


class UserProfileDetail(UserProfileDetailBase, generics.RetrieveUpdateDestroyAPIView):
    http_method_names = [GET.lower(), PUT.lower(), DELETE.lower(), HEAD.lower(), OPTIONS.lower()]

    def get_queryset(self):
        if self.request.method in [PUT, DELETE]:
            return super().get_queryset()

        profile = self.request.user.user_profile

        school_filter = {}
        if profile.user_role == UserProfile.UserRoles.ADMINISTRATOR:
            user_roles = [UserProfile.UserRoles.ADMINISTRATOR, UserProfile.UserRoles.PRINCIPAL]
        else:
            school_filter['school_unit'] = profile.school_unit_id
            if profile.user_role == UserProfile.UserRoles.PRINCIPAL:
                user_roles = [UserProfile.UserRoles.TEACHER, UserProfile.UserRoles.PARENT, UserProfile.UserRoles.STUDENT]
            elif profile.user_role == UserProfile.UserRoles.TEACHER:
                user_roles = [UserProfile.UserRoles.TEACHER, UserProfile.UserRoles.PARENT, UserProfile.UserRoles.STUDENT]
            else:
                user_roles = [UserProfile.UserRoles.PRINCIPAL, UserProfile.UserRoles.TEACHER]

        return UserProfile.objects.select_related('user', 'student_in_class') \
            .filter(user_role__in=user_roles, user__is_staff=False, **school_filter)

    @staticmethod
    def has_assigned_study_classes(teacher):
        current_academic_calendar = get_current_academic_calendar()
        if current_academic_calendar is None:
            return False

        return teacher.teacher_class_through.filter(academic_year=current_academic_calendar.academic_year).exists()

    def delete(self, request, *args, **kwargs):
        requested_profile = self.get_object()
        if requested_profile.last_online or \
                (requested_profile.user_role == UserProfile.UserRoles.TEACHER and
                 self.has_assigned_study_classes(requested_profile)) or \
                (requested_profile.user_role == UserProfile.UserRoles.STUDENT and
                 (SubjectGrade.objects.filter(student=requested_profile).exists() or
                  SubjectAbsence.objects.filter(student=requested_profile).exists() or
                  ExaminationGrade.objects.filter(student=requested_profile).exists())):
            return Response({'message': _("This user cannot be deleted because it's either active or has data.")},
                            status=status.HTTP_400_BAD_REQUEST)

        user = requested_profile.user
        requested_profile.delete()
        user.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class UserProfileActivate(UserProfileDetailBase):
    def post(self, request, *args, **kwargs):
        requested_profile = self.get_object()

        if requested_profile.is_active:
            return Response({'message': _('This user is already active.')}, status=status.HTTP_400_BAD_REQUEST)

        requested_profile.is_active = True
        requested_profile.save()
        requested_profile.user.is_active = True
        requested_profile.user.save()

        format_and_send_notification_task.delay(ACCOUNT_CHANGED_TITLE, ACCOUNT_ACTIVATED_BODY, [requested_profile.id], False, False)

        serializer = self.get_serializer(requested_profile)
        return Response(serializer.data)


class UserProfileDeactivate(UserProfileDetailBase):
    def get_serializer_class(self):
        return DeactivateUserSerializer

    def post(self, request, *args, **kwargs):
        requested_profile = self.get_object()

        if not requested_profile.is_active:
            return Response({'message': _('This user is already inactive.')}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(requested_profile, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        format_and_send_notification_task.delay(ACCOUNT_CHANGED_TITLE, ACCOUNT_DEACTIVATED_BODY, [requested_profile.id], False, False)

        return Response(serializer.data)


class ImportProfiles(views.APIView):
    permission_classes = [IsAdministratorOrPrincipal, ]
    parser_classes = [MultiPartParser, ]

    @staticmethod
    def post(request, *args, **kwargs):
        serializer = CsvUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data['file']

        language = get_language_from_request(request)

        importer = UserProfileImporter(file=file, request_user_profile=request.user.user_profile, language=language)
        return Response(
            data=importer.import_users_and_get_report()
        )
