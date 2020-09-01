import csv
import io

from ddt import data, ddt, unpack
from django.test.client import encode_multipart
from django.urls import reverse
from rest_framework import status

from edualert.common.api_tests import CommonAPITestCase
from edualert.common.utils import date
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory


@ddt
class UserProfileImportTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = UserProfileFactory(user_role=UserProfile.UserRoles.ADMINISTRATOR)
        cls.school_unit = RegisteredSchoolUnitFactory()
        cls.principal = cls.school_unit.school_principal
        cls.principal.school_unit = cls.school_unit
        cls.principal.save()

        cls.url = reverse('users:import-users')
        cls.file_name = 'file.csv'

    def setUp(self):
        self.admin_data = {
            'Name': 'John Doe',
            'Email address': 'john.doe@gmail.com',
            'Use phone as username': 'yes',
            'Phone number': '+40712999666',
            'User role': 'Administrator'
        }

        self.principal_data = {
            **self.admin_data,
            'User role': 'School Principal',
            'Phone number': '+40712999667',
        }

        self.teacher_data = {
            **self.admin_data,
            'User role': 'Teacher',
            'Phone number': '+40712999668',
        }

        self.student_data = {
            **self.admin_data,
            'Address': 'address',
            'Personal id number': '1900203099032',
            'Birth date': date(2000, 1, 1),
            'User role': 'Student',
            'Educator name': 'Educator',
            'Educator phone number': '+40712333444',
            'Educator email address': 'educator@edu.ro',
        }

        self.parent_data = {
            **self.admin_data,
            'Address': 'Address',
            'User role': 'Parent',
            'Phone number': '+40712999669',
        }

    @staticmethod
    def create_file(file_name):
        file = io.StringIO()
        file.name = file_name
        return file

    def get_response(self, file):
        file.seek(0)
        response = self.client.post(self.url, data={'file': file}, format='multipart')
        return response

    def test_user_profile_import_unauthenticated(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.TEACHER,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_user_profile_import_wrong_user_type(self, user_role):
        school_unit = RegisteredSchoolUnitFactory()
        profile = UserProfileFactory(user_role=user_role, school_unit=school_unit)
        self.client.login(username=profile.username, password='passwd')

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @data(
        'application/json',
        'text/html',
        'text/csv',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    def test_user_profile_import_wrong_content_type(self, content_type):
        self.client.login(username=self.admin, password='passwd')
        file = self.create_file(self.file_name)
        file.write('aaa')
        response = self.client.post(self.url, data={'file': file}, content_type=content_type)
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
        self.assertEqual(response.data, {'detail': f'Unsupported media type "{content_type}" in request.'})

    @data(
        'file.txt', 'file.docx', 'file.csvx'
    )
    def test_user_profile_import_invalid_extension(self, file_name):
        self.client.login(username=self.admin.username, password='passwd')
        file = self.create_file(file_name)
        file.write('aaa')
        response = self.get_response(file)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'file': ['File must be csv.']})

    def test_user_profile_import_invalid_file(self):
        # No file at all
        self.client.login(username=self.admin.username, password='passwd')
        no_file_sent_error = {'file': ['No file was submitted.']}
        response = self.client.post(self.url, format='multipart')
        self.assertEqual(response.data, no_file_sent_error)

        # Wrong key
        file = self.create_file(self.file_name)
        response = self.client.post(self.url, {'wrong_file': file}, format='multipart')
        self.assertEqual(response.data, no_file_sent_error)

        # Wrong boundary
        request_data = encode_multipart('==boundary', {'file': file})
        content_type = 'multipart/form-data; boundary=WrongBoundary'
        response = self.client.post(self.url, request_data, content_type=content_type)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, no_file_sent_error)

    @data(
        'file', 'file.ext.ext', 'file()'
    )
    def test_user_profile_import_invalid_file_name(self, file_name):
        self.client.login(username=self.admin.username, password='passwd')
        file = self.create_file(file_name)
        file.write('aaa')
        response = self.get_response(file)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'non_field_errors': ['Invalid file name.']})

    @data(
        ('admin_data', ['Name', 'Use phone as username']),
        ('principal_data', ['Name', 'Use phone as username']),
        ('teacher_data', ['Name', 'Use phone as username']),
        ('parent_data', ['Name', 'Use phone as username']),
        ('student_data', ['Name', 'Use phone as username']),
    )
    @unpack
    def test_user_profile_import_missing_fields(self, data_dict, required_fields):
        user = self.admin if data_dict in ['admin_data', 'principal_data'] else self.principal
        self.client.login(username=user.username, password='passwd')
        request_data = getattr(self, data_dict)

        file = self.create_file(self.file_name)
        writer = csv.DictWriter(file, fieldnames=request_data.keys())
        writer.writeheader()
        row = {
            field: request_data[field]
            for field in request_data.keys() if field not in required_fields
        }
        writer.writerow(row)

        response = self.get_response(file)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        errors = response.data['errors'][1]
        self.assertCountEqual(errors.keys(), required_fields)
        for key, value in errors.items():
            self.assertEqual(value, 'This field is required.')

    @data(
        (UserProfile.UserRoles.ADMINISTRATOR, ['admin_data', 'principal_data']),
        (UserProfile.UserRoles.PRINCIPAL, ['teacher_data', 'parent_data', 'student_data']),
    )
    @unpack
    def test_user_profile_import_success(self, user_role, data_dictionaries):
        self.client.login(username=UserProfile.objects.get(user_role=user_role).username, password='passwd')
        old_count = UserProfile.objects.count()
        data_dictionaries = [getattr(self, data_dict) for data_dict in data_dictionaries]
        keys = set()
        for data_dict in data_dictionaries:
            keys.update(data_dict.keys())

        file = self.create_file(self.file_name)
        writer = csv.DictWriter(file, fieldnames=keys)
        writer.writeheader()
        for data_dict in data_dictionaries:
            writer.writerow(data_dict)

        response = self.get_response(file)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.data['errors']), 0)
        self.assertEqual(response.data['report'], f'{len(data_dictionaries)} out of {len(data_dictionaries)} users saved successfully.')
        self.assertEqual(UserProfile.objects.count() - old_count, len(data_dictionaries))

    @data(
        ('Email address', ['invalid_email', 'invalid@email'], "Invalid format. Must be 150 characters at most and in the format username@domain.domainextension"),
        ('Phone number', ['letters', '0000', '++40890092'], "Invalid format. Must be minimum 10, maximum 20 digits or +."),
        ('User role', ['', '1', 'Invalid'], 'Must be one of the following options: Administrator, Principal, Teacher, Parent or Student.'),
        ('Educator email address', ['invalid_email', 'invalid@email'], "Invalid format. Must be 150 characters at most and in the format username@domain.domainextension"),
        ('Educator phone number', ['letters', '0000', '++40890092'], "Invalid format. Must be minimum 10, maximum 20 digits or +."),
        ('Personal id number', ['letters', '0000', '1233444556678889990'], 'Invalid format. Must be 13 digits, no spaces allowed.'),
        ('Birth date', [date(3000, 1, 1)], 'Birth date must be in the past.'),
        ('Birth date', ['2000-01-02', '20-20-20000'], 'Invalid date format. Must be DD-MM-YYYY.'),
        ('Use phone as username', ['true', 'True'], 'Must be either yes or no.')
    )
    @unpack
    def test_user_profile_import_validations(self, field, invalid_data, expected_error):
        self.client.login(username=self.principal.username, password='passwd')

        row = self.student_data
        for invalid_attr in invalid_data:
            row[field] = invalid_attr

            file = self.create_file(self.file_name)
            writer = csv.DictWriter(file, fieldnames=self.student_data.keys())
            writer.writeheader()
            writer.writerow(row)

            response = self.get_response(file)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            errors = response.data['errors'][1]
            self.assertEqual(len(errors), 1)
            self.assertEqual(response.data['report'], '0 out of 1 user saved successfully.')
            self.assertEqual(errors[field], expected_error)

    def test_user_profile_import_educator_validation(self):
        self.client.login(username=self.principal.username, password='passwd')
        self.student_data['Educator name'] = 'Educator'
        self.student_data['Educator phone number'] = ''
        self.student_data['Educator email address'] = ''

        file = self.create_file(self.file_name)
        writer = csv.DictWriter(file, fieldnames=self.student_data.keys())
        writer.writeheader()
        writer.writerow(self.student_data)

        response = self.get_response(file)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        errors = response.data['errors'][1]
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors['Educator name'], 'Either email or phone number is required for the educator.')

    @data(
        'yes', 'no'
    )
    def test_user_profile_import_username_validation(self, use_phone_as_username):
        self.client.login(username=self.admin.username, password='passwd')
        self.admin_data['Use phone as username'] = use_phone_as_username

        file = self.create_file(self.file_name)
        writer = csv.DictWriter(file, fieldnames=self.admin_data.keys())
        writer.writeheader()
        writer.writerow(self.admin_data)

        response = self.get_response(file)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['errors']), 0)
        username = self.admin_data['Phone number'] if use_phone_as_username == 'yes' else self.admin_data['Email address']
        self.assertTrue(UserProfile.objects.filter(username=username).exists())

    @data(
        (UserProfile.UserRoles.ADMINISTRATOR, ['student_data', 'parent_data', 'teacher_data']),
        (UserProfile.UserRoles.PRINCIPAL, ['admin_data', 'principal_data'])
    )
    @unpack
    def test_user_profile_import_invalid_user_role(self, request_user_role, data_dictionaries):
        self.client.login(
            username=UserProfile.objects.get(user_role=request_user_role).username,
            password='passwd'
        )

        for data_dict in data_dictionaries:
            file = self.create_file(self.file_name)
            writer = csv.DictWriter(file, fieldnames=self.student_data.keys())
            writer.writeheader()
            writer.writerow(getattr(self, data_dict))

            response = self.get_response(file)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            errors = response.data['errors'][1]
            self.assertEqual(len(errors), 1)
            self.assertEqual(errors['User role'], 'You don\'t have permission to create a user with this role.')

    @data(
        (UserProfile.UserRoles.ADMINISTRATOR, 'admin_data'),
        (UserProfile.UserRoles.PRINCIPAL, 'principal_data'),
        (UserProfile.UserRoles.PARENT, 'parent_data'),
        (UserProfile.UserRoles.TEACHER, 'teacher_data')
    )
    @unpack
    def test_user_profile_import_extra_fields(self, user_role, data_dict):
        # Check that any supplied fields that don't belong to the user role are ignored
        user = self.admin if data_dict in ['admin_data', 'principal_data'] else self.principal
        self.client.login(username=user.username, password='passwd')

        data_dict = getattr(self, data_dict)
        self.student_data['User role'] = data_dict['User role']
        self.student_data['Phone number'] = data_dict['Phone number']
        fieldnames = self.student_data.keys()

        file = self.create_file(self.file_name)
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(self.student_data)

        response = self.get_response(file)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['errors']), 0)

        username = data_dict['Phone number']
        if user_role in [UserProfile.UserRoles.PARENT, UserProfile.UserRoles.TEACHER]:
            username = '{}_{}'.format(self.principal.school_unit_id,username)
        user = UserProfile.objects.get(username=username)

        for field in ['Birth date', 'Educator phone number', 'Educator email', 'Educator name', 'Personal id number']:
            self.assertIsNone(getattr(user, field, None))


    @data(
        ('Name', 180, 181 * 'a'),
        ('Email address', 150, 145 * 'a' + '@gmail.com'),
        ('Educator email address', 150, 145 * 'a' + '@gmail.com'),
        ('Educator name', 180, 181 * 'a')
    )
    @unpack
    def test_user_profile_import_max_length(self, field_name, max_length, invalid_value):
        self.client.login(username=self.principal.username, password='passwd')
        self.student_data[field_name] = invalid_value

        fieldnames = self.student_data.keys()

        file = self.create_file(self.file_name)
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(self.student_data)

        response = self.get_response(file)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['errors']), 1)
        self.assertEqual(response.data['errors'][1][field_name], f'Write maximum {max_length} characters.')



