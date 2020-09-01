from ddt import data, ddt
from django.urls import reverse
from rest_framework import status

from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory, SchoolUnitCategoryFactory, SchoolUnitProfileFactory


@ddt
class MySchoolUnitTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.principal = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL)
        cls.rsu = RegisteredSchoolUnitFactory(school_principal=cls.principal)
        cls.url = reverse('schools:my-school-unit')

    def test_my_school_unit_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_my_school_unit_no_school(self):
        self.client.login(username=UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL).username, password='passwd')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.TEACHER,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_registered_school_unit_detail_wrong_user_type(self, user_role):
        user = UserProfileFactory(user_role=user_role, school_unit=self.rsu)
        self.client.login(username=user.username, password='passwd')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_my_school_unit_success(self):
        self.client.login(username=self.principal.username, password='passwd')

        category = SchoolUnitCategoryFactory()
        academic_profile = SchoolUnitProfileFactory(category=category)
        self.rsu.categories.add(category)
        self.rsu.academic_profile = academic_profile
        self.rsu.save()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_fields = ['categories', 'academic_profile', 'phone_number', 'email', 'district', 'city', 'name', 'id', 'is_active',
                           'school_principal', 'address', ]

        self.assertCountEqual(response.data.keys(), expected_fields)
        for field in expected_fields:
            if field == 'categories':
                category_data = response.data[field][0]
                self.assertEqual(category.id, category_data['id'])
                self.assertEqual(category.name, category_data['name'])
            elif field == 'academic_profile':
                academic_profile_data = response.data[field]
                self.assertEqual(academic_profile.id, academic_profile_data['id'])
                self.assertEqual(academic_profile.name, academic_profile_data['name'])
            elif field == 'school_principal':
                principal_data = response.data[field]
                self.assertEqual(self.principal.id, principal_data['id'])
                self.assertEqual(self.principal.full_name, principal_data['full_name'])
            else:
                self.assertEqual(getattr(self.rsu, field), response.data[field])
