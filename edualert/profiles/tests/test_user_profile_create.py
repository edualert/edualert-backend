from unittest import mock
from unittest.mock import patch, call

from ddt import data, ddt, unpack
from django.urls import reverse
from rest_framework import status

from edualert.academic_calendars.factories import AcademicYearCalendarFactory
from edualert.common.api_tests import CommonAPITestCase
from edualert.common.utils import date
from edualert.profiles.constants import TRANSFERRED_LABEL, SUPPORT_GROUP_LABEL, TRANSFERRED_TITLE, TRANSFERRED_BODY, \
    PROGRAM_ENROLLMENT_TITLE, PROGRAM_ENROLLMENT_BODY
from edualert.profiles.factories import UserProfileFactory, LabelFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.study_classes.factories import TeacherClassThroughFactory
from edualert.subjects.factories import SubjectFactory


@ddt
class UserProfileCreateTestCaste(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        AcademicYearCalendarFactory()
        cls.url = reverse('users:user-profile-list')
        cls.admin = UserProfileFactory(user_role=UserProfile.UserRoles.ADMINISTRATOR)
        cls.principal = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL)
        cls.school_unit = RegisteredSchoolUnitFactory(school_principal=cls.principal)

    def setUp(self):
        self.admin_data = {
            'full_name': 'John Doe',
            'email': 'john.doe@gmail.com',
            'use_phone_as_username': False,
            'phone_number': '+40712999666',
            'password': '8digitsandchar',
            'user_role': UserProfile.UserRoles.ADMINISTRATOR
        }

        self.principal_data = {
            **self.admin_data,
            'labels': [],
            'user_role': UserProfile.UserRoles.PRINCIPAL,
        }

        self.teacher_data = {
            **self.admin_data,
            'taught_subjects': [],
            'labels': [],
            'user_role': UserProfile.UserRoles.TEACHER
        }

        self.student_data = {
            **self.admin_data,
            'address': 'Address',
            'personal_id_number': '1900101044098',
            'birth_date': date(2000, 1, 1),
            'user_role': UserProfile.UserRoles.STUDENT,
            'educator_full_name': 'Educator',
            'educator_phone_number': '+40712333444',
            'educator_email': 'educator@edu.ro',
            'labels': [],
            'parents': [],
        }

        self.parent_data = {
            **self.admin_data,
            'address': 'Address',
            'labels': [],
            'user_role': UserProfile.UserRoles.PARENT
        }

    def test_user_profile_create_unauthenticated(self):
        response = self.client.post(self.url, self.admin_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.TEACHER,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_user_profile_create_wrong_user_type(self, user_role):
        profile = UserProfileFactory(user_role=user_role, school_unit=self.school_unit)
        self.client.login(username=profile.username, password='passwd')

        response = self.client.post(self.url, self.admin_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @data(
        [UserProfile.UserRoles.ADMINISTRATOR, [UserProfile.UserRoles.STUDENT, UserProfile.UserRoles.TEACHER, UserProfile.UserRoles.PARENT]],
        [UserProfile.UserRoles.PRINCIPAL, [UserProfile.UserRoles.ADMINISTRATOR, UserProfile.UserRoles.PRINCIPAL]]
    )
    @unpack
    def test_user_profile_create_forbidden_user_role(self, user_role, forbidden_roles):
        self.client.login(username=UserProfile.objects.get(user_role=user_role).username, password='passwd')
        for forbidden_role in forbidden_roles:
            self.admin_data['user_role'] = forbidden_role
            response = self.client.post(self.url, self.admin_data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data, {'user_role': ["You don't have permission to create a user with this role."]})

    @data(
        ('admin_data', []),
        ('principal_data', ['labels', 'school_unit']),
        ('teacher_data', ['labels', 'taught_subjects', 'assigned_study_classes']),
        ('parent_data', ['labels', 'address']),
        ('student_data', [
            'student_in_class', 'labels', 'risk_description', 'address', 'personal_id_number', 'birth_date',
            'parents', 'educator_full_name', 'educator_email', 'educator_phone_number'
        ])
    )
    @unpack
    def test_user_profile_create_expected_response_fields(self, data_dict, expected_fields):
        common_fields = ['id', 'full_name', 'user_role', 'email', 'phone_number', 'use_phone_as_username', 'is_active', 'last_online']

        request_data = getattr(self, data_dict)
        if request_data['user_role'] in [UserProfile.UserRoles.ADMINISTRATOR, UserProfile.UserRoles.PRINCIPAL]:
            self.client.login(username=self.admin.username, password='passwd')
        else:
            self.client.login(username=self.principal.username, password='passwd')

        response = self.client.post(self.url, request_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertCountEqual(response.data.keys(), common_fields + expected_fields)

    @data(
        ('admin_data', ['full_name', 'email', 'user_role', 'use_phone_as_username']),
        ('principal_data', ['full_name', 'labels', 'email', 'user_role', 'use_phone_as_username']),
        ('teacher_data', ['full_name', 'labels', 'taught_subjects', 'email', 'user_role', 'use_phone_as_username']),
        ('parent_data', ['full_name', 'email', 'user_role', 'labels', 'use_phone_as_username']),
        ('student_data', ['full_name', 'email', 'labels', 'parents', 'user_role', 'use_phone_as_username']),
    )
    @unpack
    def test_user_profile_create_missing_fields(self, data_dict, required_fields):
        request_data = getattr(self, data_dict)

        if request_data['user_role'] in [UserProfile.UserRoles.ADMINISTRATOR, UserProfile.UserRoles.PRINCIPAL]:
            self.client.login(username=self.admin.username, password='passwd')
        else:
            self.client.login(username=self.principal.username, password='passwd')

        request_data = getattr(self, data_dict)

        for field in required_fields:
            data_to_send = {
                required_field: request_data[required_field]
                for required_field in required_fields if required_field != field
            }
            response = self.client.post(self.url, data_to_send)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data, {field: ['This field is required.']})

        request_data['use_phone_as_username'] = True
        del request_data['phone_number']
        response = self.client.post(self.url, request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'phone_number': ['This field is required.']})

        request_data['use_phone_as_username'] = False
        del request_data['email']
        response = self.client.post(self.url, request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'email': ['This field is required.']})

    @data(
        (UserProfile.UserRoles.PRINCIPAL, 'principal_data'),
        (UserProfile.UserRoles.TEACHER, 'teacher_data'),
        (UserProfile.UserRoles.PARENT, 'parent_data'),
        (UserProfile.UserRoles.STUDENT, 'student_data'),
    )
    @unpack
    def test_user_profile_create_label_validations(self, user_role, data_dict):
        if user_role == UserProfile.UserRoles.PRINCIPAL:
            self.client.login(username=self.admin.username, password='passwd')
        else:
            self.client.login(username=self.principal.username, password='passwd')

        # Label doesn't exist
        data_to_send = getattr(self, data_dict)
        data_to_send['labels'] = [0]
        response = self.client.post(self.url, data_to_send)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'labels': ['Invalid pk "0" - object does not exist.']})

        # Label with the wrong user_role
        label = LabelFactory(user_role=UserProfile.UserRoles.PARENT if user_role != UserProfile.UserRoles.PARENT else UserProfile.UserRoles.STUDENT)

        data_to_send['labels'] = [label.id, ]
        response = self.client.post(self.url, data_to_send)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'labels': ['Labels do not correspond to the created user role.']})

    def test_user_profile_create_new_teachers_validation(self):
        self.client.login(username=self.principal.username, password='passwd')

        teacher_class_through = TeacherClassThroughFactory()
        self.teacher_data['new_teachers'] = [
            {
                "id": teacher_class_through.id,
                "teacher": teacher_class_through.teacher.id
            }
        ]

        response = self.client.post(self.url, self.teacher_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['new_teachers'], ['This field is incompatible with the request data.'])

    @data(
        '32840', '249124395385039850', '123456789123a'
    )
    def test_user_profile_create_student_personal_id_number_validation(self, bad_personal_id_number):
        self.client.login(username=self.principal.username, password='passwd')
        self.student_data['personal_id_number'] = bad_personal_id_number
        response = self.client.post(self.url, self.student_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'personal_id_number': ['Invalid format. Must be 13 digits, no spaces allowed.']})

    def test_user_profile_create_student_missing_educator_fields(self):
        self.client.login(username=self.principal.username, password='passwd')

        del self.student_data['educator_phone_number']
        del self.student_data['educator_email']
        self.student_data['educator_full_name'] = 'Educator'
        response = self.client.post(self.url, self.student_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, ({'educator_full_name': [
            'Either email or phone number is required for the educator.'
        ]}))

    def test_user_profile_create_student_parent_validations(self):
        self.client.login(username=self.principal.username, password='passwd')

        # Parents don't exist
        self.student_data['parents'] = [0]
        response = self.client.post(self.url, self.student_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'parents': ['Invalid pk "0" - object does not exist.']})

        # Parents don't belong to the same school
        other_school = RegisteredSchoolUnitFactory()
        parent = UserProfileFactory(user_role=UserProfile.UserRoles.PARENT, school_unit=other_school)
        self.student_data['parents'] = [parent.id]

        response = self.client.post(self.url, self.student_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'parents': ["Parents must belong to the user's school unit."]})

        # Parents don't have a school
        parent.school_unit = None
        parent.save()
        response = self.client.post(self.url, self.student_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'parents': ["Parents must belong to the user's school unit."]})

    @data(
        'a' * 5,
        'a' * 129,
        'abcdefg h'
    )
    def test_user_profile_create_validate_password(self, password):
        self.client.login(username=self.admin.username, password='passwd')

        self.admin_data['password'] = password
        response = self.client.post(self.url, self.admin_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['password'], ['Invalid format. Must be minimum 6, maximum 128 characters, no spaces allowed.'])

    def test_user_profile_create_username_not_unique(self):
        self.client.login(username=self.admin.username, password='passwd')

        self.admin_data['email'] = self.admin.email
        response = self.client.post(self.url, self.admin_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['username'], ['This username is already associated with another account.'])

        self.client.logout()
        self.client.login(username=self.principal.username, password='passwd')

        teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=self.school_unit, email='teacher@email.test',
                                     username='{}_{}'.format(self.school_unit.id, 'teacher@email.test'))

        self.teacher_data['email'] = teacher.email
        response = self.client.post(self.url, self.teacher_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['username'], ['This username is already associated with another account.'])

    def test_user_profile_create_principal_success(self):
        self.client.login(username=self.admin.username, password='passwd')

        # Create a label
        label = LabelFactory(user_role=UserProfile.UserRoles.PRINCIPAL)
        self.principal_data['labels'] = [label.id]

        response = self.client.post(self.url, self.principal_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        profile = UserProfile.objects.get(id=response.data['id'])
        for attr_name, value in self.principal_data.items():
            if attr_name not in ['labels', 'password']:
                self.assertEqual(getattr(profile, attr_name), value)

        self.assertCountEqual(profile.labels.values_list('id', flat=True), [label.id])

    def test_user_profile_create_teacher_success(self):
        self.client.login(username=self.principal.username, password='passwd')

        # Create a few taught subjects
        subject1 = SubjectFactory(name='Matematica')
        subject2 = SubjectFactory(name='Fizica')
        # Create a label
        label = LabelFactory(user_role=UserProfile.UserRoles.TEACHER)

        self.teacher_data['taught_subjects'] = [subject1.id, subject2.id]
        self.teacher_data['labels'] = [label.id]

        response = self.client.post(self.url, self.teacher_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        profile = UserProfile.objects.get(id=response.data['id'])
        for attr_name, value in self.teacher_data.items():
            if attr_name not in ['labels', 'taught_subjects', 'password']:
                self.assertEqual(getattr(profile, attr_name), value)

        self.assertCountEqual(profile.labels.values_list('id', flat=True), [label.id])
        self.assertCountEqual(profile.taught_subjects.values_list('id', flat=True), [subject1.id, subject2.id])

        # Teachers must have the school unit added to their profile
        self.assertEqual(profile.school_unit, self.school_unit)
        self.assertEqual(profile.user.username, '{}_{}'.format(self.school_unit.id, self.teacher_data['email']))
        self.assertEqual(profile.username, '{}_{}'.format(self.school_unit.id, self.teacher_data['email']))

    def test_user_profile_create_parent_success(self):
        self.client.login(username=self.principal.username, password='passwd')

        # Create a label
        label = LabelFactory(user_role=UserProfile.UserRoles.PARENT)
        self.parent_data['labels'] = [label.id]

        response = self.client.post(self.url, self.parent_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        profile = UserProfile.objects.get(id=response.data['id'])
        for attr_name, value in self.parent_data.items():
            if attr_name not in ['labels', 'password']:
                self.assertEqual(getattr(profile, attr_name), value)

        self.assertCountEqual(profile.labels.values_list('id', flat=True), [label.id])
        self.assertEqual(profile.school_unit, self.school_unit)
        self.assertEqual(profile.username, '{}_{}'.format(self.school_unit.id, self.parent_data['email']))
        self.assertEqual(profile.user.username, '{}_{}'.format(self.school_unit.id, self.parent_data['email']))

    @patch('edualert.profiles.tasks.format_and_send_notification_task')
    def test_user_profile_create_student_success(self, send_notification_mock):
        self.client.login(username=self.principal.username, password='passwd')

        # Create a label
        label1 = LabelFactory(user_role=UserProfile.UserRoles.STUDENT, text=TRANSFERRED_LABEL)
        label2 = LabelFactory(user_role=UserProfile.UserRoles.STUDENT, text=SUPPORT_GROUP_LABEL)
        self.student_data['labels'] = [label1.id, label2.id]

        # Create two parents
        mother = UserProfileFactory(user_role=UserProfile.UserRoles.PARENT, school_unit=self.school_unit)
        father = UserProfileFactory(user_role=UserProfile.UserRoles.PARENT, school_unit=self.school_unit)
        self.student_data['parents'] = [mother.id, father.id]

        response = self.client.post(self.url, self.student_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        student = UserProfile.objects.get(id=response.data['id'])
        self.assertCountEqual(student.parents.values_list('id', flat=True), [mother.id, father.id])
        self.assertCountEqual(student.labels.values_list('id', flat=True), [label1.id, label2.id])

        for attr_name, value in self.student_data.items():
            if attr_name not in ['labels', 'parents', 'password', 'birth_date']:
                self.assertEqual(getattr(student, attr_name), value)

        self.assertEqual(student.school_unit, self.school_unit)
        self.assertEqual(student.username, '{}_{}'.format(self.school_unit.id, self.student_data['email']))
        self.assertEqual(student.user.username, '{}_{}'.format(self.school_unit.id, self.student_data['email']))

        self.assertEqual(send_notification_mock.call_count, 2)
        calls = [call(TRANSFERRED_TITLE.format(student.full_name),
                      TRANSFERRED_BODY.format(student.full_name),
                      [father.id, mother.id, self.principal.id], False),
                 call(PROGRAM_ENROLLMENT_TITLE.format(student.full_name),
                      PROGRAM_ENROLLMENT_BODY.format(student.full_name, 'Proiect ORS - Grup Suport'),
                      [father.id, mother.id, self.principal.id], False),
                 ]
        send_notification_mock.assert_has_calls(calls, any_order=True)

    def test_user_profile_create_admin_username(self):
        self.client.login(username=self.admin.username, password='passwd')

        # Don't set use_phone_as_username. The username should be the email
        self.admin_data['use_phone_as_username'] = False
        self.admin_data['email'] = 'admin@edu.ro'

        response = self.client.post(self.url, self.admin_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        profile = UserProfile.objects.get(id=response.data['id'])
        self.assertEqual(profile.username, self.admin_data['email'])
        self.assertEqual(profile.user.username, self.admin_data['email'])

        # Set use_phone_as_username. The username should be the phone number
        self.admin_data['use_phone_as_username'] = True
        self.admin_data['phone_number'] = '+40754111222'

        response = self.client.post(self.url, self.admin_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        profile = UserProfile.objects.get(id=response.data['id'])
        self.assertEqual(profile.username, self.admin_data['phone_number'])
        self.assertEqual(profile.user.username, self.admin_data['phone_number'])

    @mock.patch('edualert.profiles.serializers.BaseUserProfileDetailSerializer.generate_password', return_value='password')
    def test_user_profile_create_generated_password(self, mocked_method):
        self.client.login(username=self.admin.username, password='passwd')

        # Test that the password is created if not sent
        del self.admin_data['password']
        response = self.client.post(self.url, self.admin_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mocked_method.assert_called_once()

        user = UserProfile.objects.get(id=response.data['id']).user
        self.assertTrue(user.check_password(mocked_method.return_value))
