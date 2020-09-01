from copy import copy

from ddt import data, ddt
from django.urls import reverse
from rest_framework import status

from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory, SchoolUnitProfileFactory, SchoolUnitCategoryFactory
from edualert.schools.models import RegisteredSchoolUnit, SchoolUnitCategory


@ddt
class RegisteredSchoolUnitUpdateTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = UserProfileFactory(user_role=UserProfile.UserRoles.ADMINISTRATOR)
        cls.principal = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL)
        cls.other_principal = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL)
        cls.academic_profile1 = SchoolUnitProfileFactory()
        category = SchoolUnitCategoryFactory(category_level=SchoolUnitCategory.CategoryLevels.SECONDARY_SCHOOL)
        cls.academic_profile2 = SchoolUnitProfileFactory(category=category)

        cls.school_unit = RegisteredSchoolUnitFactory(
            address='original address',
            phone_number='+890882333',
            email='jane.doe@gmail.com',
            district='original district',
            city='original city',
            name='original name',
            school_principal=cls.principal,
            academic_profile=cls.academic_profile1
        )
        cls.school_unit.categories.add(cls.academic_profile1.category)

        cls.url = reverse('schools:school-unit-detail', kwargs={'id': cls.school_unit.id})

    def setUp(self):
        self.request_data = {
            'categories': [self.academic_profile1.category.id, self.academic_profile2.category.id],
            'academic_profile': self.academic_profile2.id,
            'school_principal': self.other_principal.id,
            'address': 'address',
            'phone_number': '+0799111222',
            'email': 'john.doe@gmail.com'
        }

    def test_registered_school_unit_update_unauthenticated(self):
        response = self.client.put(self.url, self.request_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.TEACHER,
        UserProfile.UserRoles.PRINCIPAL,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_registered_school_unit_update_wrong_user_type(self, user_role):
        user = UserProfileFactory(user_role=user_role, school_unit=self.school_unit)
        self.client.login(username=user.username, password='passwd')

        response = self.client.put(self.url, self.request_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_registered_school_unit_update_missing_fields(self):
        self.client.login(username=self.admin_user.username, password='passwd')
        required_fields = ['categories', 'address', 'phone_number', 'email', 'school_principal', ]

        request_data = copy(self.request_data)

        for field in required_fields:
            del request_data[field]
            response = self.client.put(self.url, request_data)

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data, {field: ['This field is required.']})

            request_data = copy(self.request_data)

    def test_registered_school_unit_update_same_principal(self):
        self.client.login(username=self.admin_user.username, password='passwd')
        self.request_data['school_principal'] = self.principal.id

        response = self.client.put(self.url, self.request_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_registered_school_unit_update_validate_phone_number(self):
        self.client.login(username=self.admin_user.username, password='passwd')

        invalid_phone_numbers = [
            'abc',
            '+3232',
            '32324',
            '123456789123456789122'
            '++2392321234'
        ]
        for phone_number in invalid_phone_numbers:
            self.request_data['phone_number'] = phone_number

            response = self.client.put(self.url, self.request_data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data, {'phone_number': ['Invalid format. Must be minimum 10, maximum 20 digits or +.']})

    def test_registered_school_unit_update_validate_principal(self):
        self.client.login(username=self.admin_user.username, password='passwd')
        original_principal = self.school_unit.school_principal

        # Inexistent school principal
        self.request_data['school_principal'] = 0
        response = self.client.put(self.url, self.request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'school_principal': ['Invalid pk "0" - object does not exist.']})

        # Inactive principal
        self.principal.is_active = False
        self.principal.save()
        self.request_data['school_principal'] = self.principal.id

        response = self.client.put(self.url, self.request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'school_principal': ['Invalid user.']})

        self.principal.is_active = True
        self.principal.save()

        # The school principal is already assigned to another school
        self.request_data['school_principal'] = self.other_principal.id
        RegisteredSchoolUnitFactory(school_principal=self.other_principal)

        response = self.client.put(self.url, self.request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'school_principal': ['This field must be unique.']})

        self.school_unit.refresh_from_db()
        self.assertEqual(self.school_unit.school_principal, original_principal)

    def test_registered_school_unit_update_validate_categories(self):
        self.client.login(username=self.admin_user.username, password='passwd')
        current_categories = self.school_unit.categories.all()

        # Invalid categories
        self.request_data['categories'] = [0]
        response = self.client.put(self.url, self.request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'categories': ['Invalid pk "0" - object does not exist.']})

        # Multiple categories from the same level
        self.request_data['categories'] = [
            self.academic_profile1.category.id,
            self.academic_profile2.category.id,
            SchoolUnitCategoryFactory().id
        ]
        response = self.client.put(self.url, self.request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'categories': ['Cannot have multiple categories for the same school level.']})

        self.school_unit.refresh_from_db()
        self.assertCountEqual(current_categories, self.school_unit.categories.all())

    def test_registered_school_unit_update_validate_academic_profile(self):
        self.client.login(username=self.admin_user.username, password='passwd')

        academic_profile3 = SchoolUnitProfileFactory()

        self.request_data['academic_profile'] = academic_profile3.id
        response = self.client.put(self.url, self.request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'academic_profile': ['The academic profile does not correspond with the school category.']})

    def test_registered_school_unit_update_success(self):
        self.client.login(username=self.admin_user.username, password='passwd')
        expected_fields = ['id', 'is_active', 'categories', 'address', 'phone_number', 'email',
                           'school_principal', 'district', 'city', 'name', 'academic_profile', ]

        response = self.client.put(self.url, self.request_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(response.data.keys(), expected_fields)

        school_unit = RegisteredSchoolUnit.objects.filter(id=response.data['id']).first()
        self.assertIsNotNone(school_unit)

        for field in expected_fields:
            if field in self.request_data:
                if field == 'categories':
                    self.assertCountEqual(
                        school_unit.categories.values_list('id', flat=True),
                        self.request_data['categories']
                    )
                elif field == 'academic_profile':
                    self.assertEqual(school_unit.academic_profile.id, self.request_data['academic_profile'])
                elif field == 'school_principal':
                    self.assertEqual(school_unit.school_principal.id, self.request_data['school_principal'])
                else:
                    self.assertEqual(getattr(school_unit, field), self.request_data[field])

        self.refresh_objects_from_db([self.other_principal, self.principal])
        self.assertEqual(self.other_principal.school_unit, school_unit)
        self.assertIsNone(self.principal.school_unit)
        self.assertFalse(self.client.login(username=self.principal.username, password='passwd'))

    def test_registered_school_unit_update_no_academic_profile(self):
        self.client.login(username=self.admin_user.username, password='passwd')

        self.request_data['academic_profile'] = None
        response = self.client.put(self.url, self.request_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data['academic_profile'])
