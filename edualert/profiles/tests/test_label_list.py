from ddt import ddt, data
from django.urls import reverse
from rest_framework import status

from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory, LabelFactory
from edualert.profiles.models import UserProfile, Label
from edualert.schools.factories import RegisteredSchoolUnitFactory


@ddt
class LabelListTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        Label.objects.all().delete()
        for role in UserProfile.UserRoles.values:
            LabelFactory(user_role=role)
            LabelFactory(user_role=role)

        cls.school_unit = RegisteredSchoolUnitFactory()
        cls.url = reverse('users:label-list')
        cls.expected_fields = ['id', 'text']

    def test_label_list_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.TEACHER,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_label_list_wrong_user_type(self, user_role):
        profile = UserProfileFactory(user_role=user_role, school_unit=self.school_unit)
        self.client.login(username=profile.username, password='passwd')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.PRINCIPAL
    )
    def test_label_list(self, user_role):
        profile = UserProfileFactory(
            user_role=user_role,
            school_unit=self.school_unit if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )
        self.client.login(username=profile.username, password='passwd')

        for role in UserProfile.UserRoles.values:
            response = self.client.get(self.url, {'user_role': role})
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data), 2)
            for result in response.data:
                self.assertCountEqual(result.keys(), self.expected_fields)
