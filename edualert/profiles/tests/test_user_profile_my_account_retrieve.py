from django.urls import reverse
from rest_framework import status

from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory


class UserProfileMyAccountRetrieveTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('users:my-account')

    def test_user_profile_my_account_retrieve_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_profile_my_account_retrieve_expected_fields(self):
        rsu = RegisteredSchoolUnitFactory()

        for user_role in [UserProfile.UserRoles.ADMINISTRATOR, UserProfile.UserRoles.PRINCIPAL,
                          UserProfile.UserRoles.TEACHER, UserProfile.UserRoles.PARENT, UserProfile.UserRoles.STUDENT]:
            expected_fields = [
                'id', 'full_name', 'user_role', 'email', 'phone_number', 'use_phone_as_username',
                'email_notifications_enabled', 'sms_notifications_enabled', 'push_notifications_enabled', 'school_unit'
            ]
            if user_role == UserProfile.UserRoles.STUDENT:
                expected_fields += ['class_grade', 'class_letter', 'personal_id_number', 'birth_date', 'address']
            if user_role == UserProfile.UserRoles.PARENT:
                expected_fields += ['address', 'children']

            profile = UserProfileFactory(
                user_role=user_role,
                school_unit=rsu if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
            )

            self.client.login(username=profile.username, password='passwd')
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertCountEqual(response.data.keys(), expected_fields)
            self.assertEqual(response.data['id'], profile.id)
            self.assertEqual(response.data['school_unit'], profile.school_unit.id if profile.school_unit else None)
