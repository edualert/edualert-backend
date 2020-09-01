from ddt import data, ddt
from django.urls import reverse
from rest_framework import status

from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory, SchoolUnitCategoryFactory, SchoolUnitProfileFactory


@ddt
class RegisteredSchoolUnitListTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = UserProfileFactory(user_role=UserProfile.UserRoles.ADMINISTRATOR)
        cls.url = reverse('schools:school-unit-list')

    def test_registered_school_unit_list_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.TEACHER,
        UserProfile.UserRoles.PRINCIPAL,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_registered_school_unit_list_wrong_user_type(self, user_role):
        school_unit = RegisteredSchoolUnitFactory()
        user = UserProfileFactory(user_role=user_role, school_unit=school_unit)
        self.client.login(username=user.username, password='passwd')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_registered_school_unit_list_success(self):
        self.client.login(username=self.admin_user.username, password='passwd')
        # Create two active registered school units and two inactive ones
        rsu1 = RegisteredSchoolUnitFactory(is_active=True, name='c')
        rsu2 = RegisteredSchoolUnitFactory(is_active=True, name='d')
        rsu3 = RegisteredSchoolUnitFactory(is_active=False, name='b')
        rsu4 = RegisteredSchoolUnitFactory(is_active=False, name='a')

        # Also add a category for one of the school units
        category = SchoolUnitCategoryFactory()
        academic_profile = SchoolUnitProfileFactory(category=category)
        rsu1.categories.add(category)
        rsu1.academic_profile = academic_profile
        rsu1.save()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # The school units should be ordered by is_active, then name
        results = response.data['results']
        self.assertEqual(results[0]['id'], rsu1.id)
        self.assertEqual(results[1]['id'], rsu2.id)
        self.assertEqual(results[2]['id'], rsu4.id)
        self.assertEqual(results[3]['id'], rsu3.id)

        expected_fields = ['id', 'name', 'categories', 'academic_profile', 'is_active', 'district', 'city']
        for result in results:
            self.assertCountEqual(result.keys(), expected_fields)
            if result['id'] == rsu1.id:
                self.assertCountEqual(result['categories'], [{'name': category.name, 'id': category.id, 'category_level': category.category_level}])
                self.assertCountEqual(result['academic_profile'], {'name': academic_profile.name, 'id': academic_profile.id})

    def test_registered_school_unit_list_search(self):
        self.client.login(username=self.admin_user.username, password='passwd')
        RegisteredSchoolUnitFactory(name='rsu1')
        RegisteredSchoolUnitFactory(name='rsu2')

        response = self.client.get(self.url, {'search': 'rsu1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'rsu1')

    @data(
        {'city': 'Cluj'},
        {'district': 'Cluj'},
        {'academic_profile': None},
        {'categories': None},
    )
    def test_registered_school_unit_list_filter(self, filter_kwargs):
        self.client.login(username=self.admin_user.username, password='passwd')

        if list(filter_kwargs.keys())[0] == 'categories':
            rsu1 = RegisteredSchoolUnitFactory()
            category = SchoolUnitCategoryFactory()
            rsu1.categories.add(category)

            filter_kwargs = {'categories': category.id}
        elif list(filter_kwargs.keys())[0] == 'academic_profile':
            category = SchoolUnitCategoryFactory()
            academic_profile = SchoolUnitProfileFactory(category=category)
            rsu1 = RegisteredSchoolUnitFactory(academic_profile=academic_profile)

            filter_kwargs = {'academic_profile': academic_profile.id}
        else:
            rsu1 = RegisteredSchoolUnitFactory(**filter_kwargs)

        RegisteredSchoolUnitFactory()

        response = self.client.get(self.url, filter_kwargs)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], rsu1.id)
