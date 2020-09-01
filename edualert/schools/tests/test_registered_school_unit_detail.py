from ddt import data, ddt
from django.urls import reverse
from rest_framework import status

from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory, SchoolUnitCategoryFactory, SchoolUnitProfileFactory


@ddt
class RegisteredSchoolUnitsDetailTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = UserProfileFactory(user_role=UserProfile.UserRoles.ADMINISTRATOR)
        cls.rsu = RegisteredSchoolUnitFactory()
        cls.url = reverse('schools:school-unit-detail', kwargs={'id': cls.rsu.id})

    def test_registered_school_unit_detail_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.TEACHER,
        UserProfile.UserRoles.PRINCIPAL,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_registered_school_unit_detail_wrong_user_type(self, user_role):
        user = UserProfileFactory(user_role=user_role, school_unit=self.rsu)
        self.client.login(username=user.username, password='passwd')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_registered_school_unit_detail_not_found(self):
        self.client.login(username=self.admin_user.username, password='passwd')
        url = reverse('schools:school-unit-detail', kwargs={'id': 0})

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_registered_school_unit_detail_success(self):
        self.client.login(username=self.admin_user.username, password='passwd')

        category = SchoolUnitCategoryFactory()
        academic_profile = SchoolUnitProfileFactory(category=category)
        self.rsu.categories.add(category)
        principal = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL)
        self.rsu.school_principal = principal
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
                self.assertEqual(category.category_level, category_data['category_level'])
            elif field == 'academic_profile':
                academic_profile_data = response.data[field]
                self.assertEqual(academic_profile.id, academic_profile_data['id'])
                self.assertEqual(academic_profile.name, academic_profile_data['name'])
            elif field == 'school_principal':
                principal_data = response.data[field]
                self.assertEqual(principal.id, principal_data['id'])
                self.assertEqual(principal.full_name, principal_data['full_name'])
            else:
                self.assertEqual(getattr(self.rsu, field), response.data[field])
