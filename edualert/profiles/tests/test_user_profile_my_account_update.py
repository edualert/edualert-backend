from ddt import data, ddt, unpack
from django.urls import reverse
from rest_framework import status

from edualert.common.api_tests import CommonAPITestCase
from edualert.common.utils import date
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory


@ddt
class UserProfileMyAccountUpdateTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('users:my-account')
        cls.administrator = UserProfileFactory(user_role=UserProfile.UserRoles.ADMINISTRATOR)
        cls.principal = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL)
        cls.teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER)
        cls.parent = UserProfileFactory(user_role=UserProfile.UserRoles.PARENT)
        cls.student = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT)
        cls.registered_school_unit = RegisteredSchoolUnitFactory(school_principal=cls.principal)

        for user in UserProfile.objects.exclude(user_role=UserProfile.UserRoles.ADMINISTRATOR):
            user.school_unit = cls.registered_school_unit
            user.save()

    def setUp(self):
        self.administrator.refresh_from_db()
        self.data = {
            'use_phone_as_username': True,
            'email': 'new_email@gmail.com',
            'phone_number': '+40700100200',
            'full_name': 'New Name',
            'email_notifications_enabled': True,
            'sms_notifications_enabled': True,
            'push_notifications_enabled': True,
            'current_password': 'passwd',
            'new_password': 'password',
            'user_role': 'ADMINISTRATOR'
        }
        self.parent_data = {
            **self.data,
            'address': 'address',
            'user_role': 'PARENT'
        }
        self.student_data = {
            **self.data,
            'address': 'address',
            'personal_id_number': '1900203044858',
            'birth_date': date(2000, 1, 1),
            'user_role': 'STUDENT'
        }

    def test_user_profile_my_account_update_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR, UserProfile.UserRoles.PRINCIPAL, UserProfile.UserRoles.TEACHER,
        UserProfile.UserRoles.STUDENT, UserProfile.UserRoles.PARENT
    )
    def test_user_profile_my_account_update_required_fields(self, user_role):
        self.client.login(username=UserProfile.objects.get(user_role=user_role).username, password='passwd')

        required_fields = [
            'phone_number', 'use_phone_as_username', 'full_name',
            'email_notifications_enabled', 'push_notifications_enabled',
            'sms_notifications_enabled'
        ]

        for field in required_fields:
            data_to_send = {
                field_name: self.data.get(field_name)
                for field_name in required_fields if field_name != field
            }
            data_to_send['user_role'] = user_role
            response = self.client.put(self.url, data_to_send)

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data, {field: ['This field is required.']})

    @data(
        (UserProfile.UserRoles.ADMINISTRATOR, ['id', 'full_name', 'user_role', 'email', 'phone_number',
                                               'use_phone_as_username', 'email_notifications_enabled',
                                               'sms_notifications_enabled', 'push_notifications_enabled', 'school_unit']),
        (UserProfile.UserRoles.PRINCIPAL, ['id', 'full_name', 'user_role', 'email', 'phone_number',
                                           'use_phone_as_username', 'email_notifications_enabled',
                                           'sms_notifications_enabled', 'push_notifications_enabled', 'school_unit']),
        (UserProfile.UserRoles.TEACHER, ['id', 'full_name', 'user_role', 'email', 'phone_number',
                                         'use_phone_as_username', 'email_notifications_enabled',
                                         'sms_notifications_enabled', 'push_notifications_enabled', 'school_unit']),
        (UserProfile.UserRoles.PARENT, ['id', 'full_name', 'user_role', 'email', 'phone_number',
                                        'use_phone_as_username', 'email_notifications_enabled',
                                        'sms_notifications_enabled', 'push_notifications_enabled',
                                        'address', 'school_unit', 'children']),
        (UserProfile.UserRoles.STUDENT, ['id', 'full_name', 'user_role', 'email', 'phone_number',
                                         'use_phone_as_username', 'email_notifications_enabled',
                                         'sms_notifications_enabled', 'push_notifications_enabled',
                                         'address', 'class_grade', 'class_letter', 'personal_id_number', 'birth_date', 'school_unit'])
    )
    @unpack
    def test_user_profile_my_account_update_expected_response_fields(self, user_role, expected_fields):
        profile = UserProfile.objects.get(user_role=user_role)
        self.client.login(username=profile.username, password='passwd')

        if user_role == UserProfile.UserRoles.PARENT:
            data_to_send = self.parent_data
        elif user_role == UserProfile.UserRoles.STUDENT:
            data_to_send = self.student_data
        else:
            data_to_send = self.data

        data_to_send['user_role'] = user_role.upper()
        response = self.client.put(self.url, data_to_send)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(response.data.keys(), expected_fields)

    def test_user_profile_my_account_update_password_validations(self):
        self.client.login(username=self.administrator.username, password='passwd')

        self.data['new_password'] = ''
        response = self.client.put(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'new_password': ['This field is required.']})

        for new_password in ['a' * 5, 'a' * 129, 'abcdefg h']:
            self.data['new_password'] = new_password
            response = self.client.put(self.url, self.data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data, {'new_password': ['Invalid format. Must be minimum 6, maximum 128 characters, no spaces allowed.']})

        self.data['new_password'] = 'passwd'
        self.data['current_password'] = ''
        response = self.client.put(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'current_password': ['This field is required.']})

        self.data['current_password'] = 'invalid_pass'
        response = self.client.put(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'current_password': ["Does not match the user's current password."]})

    def test_user_profile_my_account_update_success(self):
        self.client.login(username=self.administrator.username, password='passwd')

        response = self.client.put(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.refresh_objects_from_db([self.administrator, self.administrator.user])

        for field, value in self.data.items():
            if field not in ['user_role', 'new_password', 'current_password']:
                self.assertEqual(value, getattr(self.administrator, field))

        self.assertTrue(self.administrator.user.check_password(self.data['new_password']))
        self.assertEqual(self.administrator.username, self.data['phone_number'])

    def test_user_profile_my_account_update_username_validations(self):
        self.client.login(username=self.administrator.username, password='passwd')

        self.data['use_phone_as_username'] = False
        self.data['email'] = self.principal.email
        response = self.client.put(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'username': ['This username is already associated with another account.']})

        self.data['use_phone_as_username'] = True
        self.data['email'] = 'new_email@test.com'
        del self.data['phone_number']
        response = self.client.put(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'phone_number': ['This field is required.']})

        self.data['use_phone_as_username'] = False
        self.data['email'] = ''
        response = self.client.put(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'email': ['This field is required.']})

    @data(
        ('email', ['invalid_email', 'invalid@email'], ["Enter a valid email address."]),
        ('phone_number', ['letters', '0000', '++40890092'], ["Invalid format. Must be minimum 10, maximum 20 digits or +."]),
        ('personal_id_number', ['letters', '0000', '1233444556678889990'], ['Invalid format. Must be 13 digits, no spaces allowed.']),
        ('birth_date', [date(3000, 1, 1)], ['Birth date must be in the past.']),
        ('birth_date', ['2000-01-02', '20-20-20000'], ['Date has wrong format. Use one of these formats instead: DD-MM-YYYY.']),
    )
    @unpack
    def test_user_profile_my_account_update_validations(self, field, values, expected_error):
        self.client.login(username=self.student.username, password='passwd')

        for value in values:
            self.data[field] = value
            response = self.client.put(self.url, self.data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data[field], expected_error)
