from ddt import data, ddt, unpack
from django.urls import reverse
from rest_framework import status

from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory


@ddt
class UserProfileActivateTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = UserProfileFactory(user_role=UserProfile.UserRoles.ADMINISTRATOR)
        cls.principal = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL)
        cls.school_unit = RegisteredSchoolUnitFactory(school_principal=cls.principal)

    @staticmethod
    def build_url(profile_id):
        return reverse('users:user-profile-activate', kwargs={'id': profile_id})

    def test_activate_user_unauthenticated(self):
        response = self.client.post(self.build_url(self.admin.id), data={})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.TEACHER,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_activate_user_wrong_user_type(self, user_role):
        profile = UserProfileFactory(user_role=user_role, school_unit=self.school_unit)
        self.client.login(username=profile.username, password='passwd')

        response = self.client.post(self.build_url(self.principal.id), data={})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @data(
        'admin', 'principal'
    )
    def test_activate_user_not_found(self, profile):
        self.client.login(username=getattr(self, profile).username, password='passwd')

        response = self.client.post(self.build_url(0), data={})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @unpack
    @data(
        ('admin', UserProfile.UserRoles.TEACHER),
        ('admin', UserProfile.UserRoles.STUDENT),
        ('admin', UserProfile.UserRoles.PARENT),
        ('principal', UserProfile.UserRoles.ADMINISTRATOR),
        ('principal', UserProfile.UserRoles.PRINCIPAL),
    )
    def test_activate_user_wrong_requested_user_type(self, login_user, user_role):
        self.client.login(username=getattr(self, login_user).username, password='passwd')
        profile = UserProfileFactory(user_role=user_role)

        response = self.client.post(self.build_url(profile.id), data={})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_activate_user_already_active(self):
        self.client.login(username=self.admin.username, password='passwd')

        response = self.client.post(self.build_url(self.principal.id), data={})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], 'This user is already active.')

    @unpack
    @data(
        ('admin', UserProfile.UserRoles.ADMINISTRATOR),
        ('admin', UserProfile.UserRoles.PRINCIPAL),
        ('principal', UserProfile.UserRoles.TEACHER),
        ('principal', UserProfile.UserRoles.STUDENT),
        ('principal', UserProfile.UserRoles.PARENT),
    )
    def test_activate_user_success(self, login_user, user_role):
        self.client.login(username=getattr(self, login_user).username, password='passwd')
        profile = UserProfileFactory(
            user_role=user_role, is_active=False,
            school_unit=self.school_unit if user_role not in [UserProfile.UserRoles.ADMINISTRATOR, UserProfile.UserRoles.PRINCIPAL] else None
        )
        profile.user.is_active = False
        profile.user.save()

        response = self.client.post(self.build_url(profile.id), data={})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        profile.refresh_from_db()
        self.assertTrue(profile.is_active)
        self.assertTrue(profile.user.is_active)
