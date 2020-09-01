from ddt import ddt, data
from django.urls import reverse
from rest_framework import status

from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import SchoolUnitCategoryFactory, RegisteredSchoolUnitFactory


@ddt
class SchoolUnitCategoryListTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = UserProfileFactory(user_role=UserProfile.UserRoles.ADMINISTRATOR)
        cls.url = reverse('schools:school-unit-category-list')

    def test_school_unit_category_list_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.TEACHER,
        UserProfile.UserRoles.PRINCIPAL,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_school_unit_category_list_wrong_user_type(self, user_role):
        school_unit = RegisteredSchoolUnitFactory()
        profile = UserProfileFactory(user_role=user_role, school_unit=school_unit)
        self.client.login(username=profile.username, password='passwd')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_school_unit_category_list_empty(self):
        self.client.login(username=self.admin_user.username, password='passwd')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_school_unit_category_list_success(self):
        self.client.login(username=self.admin_user.username, password='passwd')

        category1 = SchoolUnitCategoryFactory(name='c2')
        category2 = SchoolUnitCategoryFactory(name='c3')
        category3 = SchoolUnitCategoryFactory(name='c1')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data
        self.assertEqual(len(results), 3)
        self.assertEqual(category3.id, results[0]['id'])
        self.assertEqual(category1.id, results[1]['id'])
        self.assertEqual(category2.id, results[2]['id'])

        expected_fields = ['id', 'name', 'category_level']
        for result in results:
            self.assertCountEqual(result.keys(), expected_fields)
