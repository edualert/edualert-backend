from copy import copy
from unittest.mock import patch

from ddt import data, ddt, unpack
from django.urls import reverse
from rest_framework import status

from edualert.common.api_tests import CommonAPITestCase
from edualert.notifications.models import Notification, TargetUserThrough
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.study_classes.factories import StudyClassFactory, TeacherClassThroughFactory
from edualert.study_classes.models import TeacherClassThrough
from edualert.subjects.factories import SubjectFactory


@ddt
class SendMessageTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.principal = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL)
        cls.school_unit = RegisteredSchoolUnitFactory(school_principal=cls.principal)

        cls.teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=cls.school_unit)
        cls.study_class = StudyClassFactory(school_unit=cls.school_unit)
        cls.subject = SubjectFactory(name='Subject')
        cls.another_subject = SubjectFactory(name='Another subject')
        TeacherClassThroughFactory(teacher=cls.teacher, study_class=cls.study_class, subject=cls.subject)
        cls.teacher.taught_subjects.add(cls.subject, cls.another_subject)

        cls.parent = UserProfileFactory(user_role=UserProfile.UserRoles.PARENT, school_unit=cls.school_unit, sms_notifications_enabled=True)
        cls.student1 = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=cls.school_unit, student_in_class=cls.study_class, sms_notifications_enabled=True)
        cls.student1.parents.add(cls.parent)
        cls.student2 = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=cls.school_unit, student_in_class=cls.study_class, sms_notifications_enabled=True)

        cls.url = reverse('notifications:my-sent-message-list')
        cls.expected_fields = ['id', 'title', 'created', 'send_sms', 'status', 'receiver_type',
                               'target_users_role', 'target_study_class', 'target_user_through', 'body']

    def setUp(self):
        self.notification_for_class_students = {
            "title": "Notification for class students",
            "send_sms": True,
            "receiver_type": Notification.ReceiverTypes.CLASS_STUDENTS,
            "target_study_class": self.study_class.id,
            "body": "Body for class students"
        }
        self.notification_for_class_parents = {
            "title": "Notification for class parents",
            "send_sms": True,
            "receiver_type": Notification.ReceiverTypes.CLASS_PARENTS,
            "target_study_class": self.study_class.id,
            "body": "Body for class parents"
        }
        self.notification_for_one_student = {
            "title": "Notification for one student",
            "send_sms": True,
            "receiver_type": Notification.ReceiverTypes.ONE_STUDENT,
            "target_user": self.student1.id,
            "body": "Body for one student"
        }
        self.notification_for_one_parent = {
            "title": "Notification for one parent",
            "send_sms": True,
            "receiver_type": Notification.ReceiverTypes.ONE_PARENT,
            "target_user": self.parent.id,
            "body": "Body for one parent"
        }
        self.parent.refresh_from_db()

    def test_sent_message_unauthenticated(self):
        response = self.client.post(self.url, data=self.notification_for_class_students)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_send_message_wrong_user_type(self, user_role):
        profile = UserProfileFactory(
            user_role=user_role,
            school_unit=self.school_unit if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )
        self.client.login(username=profile.username, password='passwd')

        response = self.client.post(self.url, data=self.notification_for_class_students)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @data(
        ('notification_for_class_students', ['title', 'send_sms', 'receiver_type', 'target_study_class', 'body']),
        ('notification_for_class_parents', ['title', 'send_sms', 'receiver_type', 'target_study_class', 'body']),
        ('notification_for_one_student', ['title', 'send_sms', 'receiver_type', 'target_user', 'body']),
        ('notification_for_one_parent', ['title', 'send_sms', 'receiver_type', 'target_user', 'body']),
    )
    @unpack
    def test_send_message_missing_fields(self, request_data_param, required_fields):
        self.client.login(username=self.principal.username, password='passwd')

        request_data = copy(getattr(self, request_data_param))

        for field in required_fields:
            del request_data[field]
            response = self.client.post(self.url, request_data)

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data, {field: ['This field is required.']})

            request_data = copy(getattr(self, request_data_param))

    def test_send_message_incompatible_fields(self):
        self.client.login(username=self.principal.username, password='passwd')

        for request_data in [self.notification_for_class_students, self.notification_for_class_parents]:
            request_data['target_user'] = self.student1.id

            response = self.client.post(self.url, request_data)

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data, {'target_user': ['This field is incompatible with the receiver type.']})

        for request_data in [self.notification_for_one_student, self.notification_for_one_parent]:
            request_data['target_study_class'] = self.study_class.id

            response = self.client.post(self.url, request_data)

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data, {'target_study_class': ['This field is incompatible with the receiver type.']})

    @data(
        'notification_for_class_students', 'notification_for_class_parents'
    )
    def test_send_message_validate_target_study_class(self, request_data_param):
        self.client.login(username=self.principal.username, password='passwd')
        request_data = getattr(self, request_data_param)
        request_data['target_study_class'] = 0

        response = self.client.post(self.url, request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'target_study_class': ['Invalid pk "0" - object does not exist.']})

    def test_send_message_validate_target_user_student(self):
        self.client.login(username=self.principal.username, password='passwd')
        self.notification_for_one_student['target_user'] = 0

        response = self.client.post(self.url, self.notification_for_one_student)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'target_user': ['Invalid pk "0" - object does not exist.']})

        self.notification_for_one_student['target_user'] = self.parent.id
        response = self.client.post(self.url, self.notification_for_one_student)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'target_user': ['This user must be a student.']})

        self.student1.is_active = False
        self.student1.save()

        self.notification_for_one_student['target_user'] = self.student1.id
        response = self.client.post(self.url, self.notification_for_one_student)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'target_user': [f'Invalid pk "{self.student1.id}" - object does not exist.']})

        self.student1.is_active = True
        self.student1.save()

    def test_send_message_validate_target_user_parent(self):
        self.client.login(username=self.principal.username, password='passwd')
        self.notification_for_one_parent['target_user'] = 0

        response = self.client.post(self.url, self.notification_for_one_parent)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'target_user': ['Invalid pk "0" - object does not exist.']})

        self.notification_for_one_parent['target_user'] = self.student1.id
        response = self.client.post(self.url, self.notification_for_one_parent)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'target_user': ['This user must be a parent.']})

        self.parent.is_active = False
        self.parent.save()

        self.notification_for_one_parent['target_user'] = self.parent.id
        response = self.client.post(self.url, self.notification_for_one_parent)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'target_user': [f'Invalid pk "{self.parent.id}" - object does not exist.']})

        self.parent.is_active = True
        self.parent.save()

    def test_send_message_validate_body(self):
        self.client.login(username=self.principal.username, password='passwd')

        self.notification_for_class_students['body'] = 'x' * 501
        response = self.client.post(self.url, self.notification_for_class_students)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'body': ['Maximum characters numbers was exceeded.']})

        self.notification_for_class_students['body'] = 'x' * 161
        self.notification_for_class_students['send_sms'] = True
        response = self.client.post(self.url, self.notification_for_class_students)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'body': ['Maximum characters numbers was exceeded.']})

    @patch('edualert.notifications.tasks.send_mass_mail')
    @patch('edualert.notifications.tasks.send_mail')
    @patch('edualert.notifications.tasks.send_sms')
    def test_send_message_notifications_disabled(self, mocked_send_sms, mocked_send_mail, mocked_send_mass_mail):
        self.client.login(username=self.principal.username, password='passwd')
        self.parent.sms_notifications_enabled = False
        self.parent.save()

        response = self.client.post(self.url, self.notification_for_one_parent)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(mocked_send_mail.call_count, 1)
        self.assertEqual(mocked_send_mass_mail.call_count, 0)
        self.assertEqual(mocked_send_sms.call_count, 0)

        self.parent.email_notifications_enabled = False
        self.parent.save()

        response = self.client.post(self.url, self.notification_for_one_parent)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(mocked_send_mail.call_count, 1)
        self.assertEqual(mocked_send_mass_mail.call_count, 0)
        self.assertEqual(mocked_send_sms.call_count, 0)

    @patch('edualert.notifications.tasks.send_mass_mail')
    @patch('edualert.notifications.tasks.send_mail')
    @patch('edualert.notifications.tasks.send_sms')
    def test_send_message_missing_phone_number(self, mocked_send_sms, mocked_send_mail, mocked_send_mass_mail):
        self.client.login(username=self.principal.username, password='passwd')
        self.parent.phone_number = ''
        self.parent.save()

        response = self.client.post(self.url, self.notification_for_one_parent)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(mocked_send_mail.call_count, 1)
        self.assertEqual(mocked_send_mass_mail.call_count, 0)
        self.assertEqual(mocked_send_sms.call_count, 0)

    @patch('edualert.notifications.tasks.send_mass_mail')
    @patch('edualert.notifications.tasks.send_mail')
    @patch('edualert.notifications.tasks.send_sms')
    def test_send_message_missing_email(self, mocked_send_sms, mocked_send_mail, mocked_send_mass_mail):
        self.client.login(username=self.principal.username, password='passwd')
        self.parent.email = ''
        self.parent.save()

        response = self.client.post(self.url, self.notification_for_one_parent)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(mocked_send_mail.call_count, 0)
        self.assertEqual(mocked_send_mass_mail.call_count, 0)
        self.assertEqual(mocked_send_sms.call_count, 1)

    @data(
        'principal', 'teacher'
    )
    @patch('edualert.notifications.tasks.send_mass_mail')
    @patch('edualert.notifications.tasks.send_mail')
    @patch('edualert.notifications.tasks.send_sms')
    def test_send_message_for_class_students(self, profile_param, mocked_send_sms, mocked_send_mail, mocked_send_mass_mail):
        profile = getattr(self, profile_param)
        self.client.login(username=profile.username, password='passwd')

        # Create one more student who's not part of this class
        UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=self.school_unit)

        response = self.client.post(self.url, self.notification_for_class_students)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertCountEqual(response.data.keys(), self.expected_fields)

        message = Notification.objects.get(id=response.data['id'])
        self.assertEqual(message.from_user_id, profile.id)
        self.assertEqual(message.from_user_role, profile.user_role)
        if profile_param == 'principal':
            self.assertIsNone(message.from_user_subjects)
        else:
            self.assertEqual(message.from_user_subjects, self.subject.name)
        self.assertEqual(message.target_users_role, UserProfile.UserRoles.STUDENT)
        self.assertEqual(message.target_study_class_id, self.study_class.id)
        self.assertEqual(message.targets_count, 2)

        self.assertEqual(mocked_send_mail.call_count, 0)
        self.assertEqual(mocked_send_mass_mail.call_count, 1)
        self.assertEqual(mocked_send_sms.call_count, 1)
        self.assertEqual(len(mocked_send_sms.call_args), 2)
        self.assertEqual(TargetUserThrough.objects.filter(notification=message).count(), 2)

    @data(
        'principal', 'teacher'
    )
    @patch('edualert.notifications.tasks.send_mass_mail')
    @patch('edualert.notifications.tasks.send_mail')
    @patch('edualert.notifications.tasks.send_sms')
    def test_send_message_for_class_parents(self, profile_param, mocked_send_sms, mocked_send_mail, mocked_send_mass_mail):
        profile = getattr(self, profile_param)
        self.client.login(username=profile.username, password='passwd')
        TeacherClassThrough.objects.filter(teacher=self.teacher, study_class=self.study_class).delete()

        response = self.client.post(self.url, self.notification_for_class_parents)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertCountEqual(response.data.keys(), self.expected_fields)

        message = Notification.objects.get(id=response.data['id'])
        self.assertEqual(message.from_user_id, profile.id)
        self.assertEqual(message.from_user_role, profile.user_role)
        if profile_param == 'principal':
            self.assertIsNone(message.from_user_subjects)
        else:
            self.assertEqual(message.from_user_subjects, '')
        self.assertEqual(message.target_users_role, UserProfile.UserRoles.PARENT)
        self.assertEqual(message.target_study_class_id, self.study_class.id)
        self.assertEqual(message.targets_count, 1)

        self.assertEqual(mocked_send_mail.call_count, 1)
        self.assertEqual(mocked_send_mass_mail.call_count, 0)
        self.assertEqual(mocked_send_sms.call_count, 1)

        self.assertEqual(TargetUserThrough.objects.filter(notification=message).count(), 1)

    @data(
        'principal', 'teacher'
    )
    @patch('edualert.notifications.tasks.send_mass_mail')
    @patch('edualert.notifications.tasks.send_mail')
    @patch('edualert.notifications.tasks.send_sms')
    def test_send_message_for_one_student(self, profile_param, mocked_send_sms, mocked_send_mail, mocked_send_mass_mail):
        profile = getattr(self, profile_param)
        self.client.login(username=profile.username, password='passwd')

        subject2 = SubjectFactory(name='Subject 2')
        TeacherClassThroughFactory(teacher=self.teacher, study_class=self.study_class, subject=subject2)

        response = self.client.post(self.url, self.notification_for_one_student)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertCountEqual(response.data.keys(), self.expected_fields)

        message = Notification.objects.get(id=response.data['id'])
        self.assertEqual(message.from_user_id, profile.id)
        self.assertEqual(message.from_user_role, profile.user_role)
        if profile_param == 'principal':
            self.assertIsNone(message.from_user_subjects)
        else:
            self.assertEqual(message.from_user_subjects, self.subject.name + '__' + subject2.name)
        self.assertEqual(message.target_users_role, UserProfile.UserRoles.STUDENT)
        self.assertEqual(message.target_study_class_id, self.study_class.id)
        self.assertEqual(message.targets_count, 1)

        self.assertEqual(mocked_send_mail.call_count, 1)
        self.assertEqual(mocked_send_mass_mail.call_count, 0)
        self.assertEqual(mocked_send_sms.call_count, 1)

        self.assertEqual(TargetUserThrough.objects.filter(notification=message).count(), 1)

    @data(
        'principal', 'teacher'
    )
    @patch('edualert.notifications.tasks.send_mass_mail')
    @patch('edualert.notifications.tasks.send_mail')
    @patch('edualert.notifications.tasks.send_sms')
    def test_send_message_for_one_parent(self, profile_param, mocked_send_sms, mocked_send_mail, mocked_send_mass_mail):
        profile = getattr(self, profile_param)
        self.client.login(username=profile.username, password='passwd')

        another_study_class = StudyClassFactory(school_unit=self.school_unit)
        another_student = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=self.school_unit,
                                             student_in_class=another_study_class)
        another_student.parents.add(self.parent)

        response = self.client.post(self.url, self.notification_for_one_parent)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertCountEqual(response.data.keys(), self.expected_fields)

        message = Notification.objects.get(id=response.data['id'])
        self.assertEqual(message.from_user_id, profile.id)
        self.assertEqual(message.from_user_role, profile.user_role)
        if profile_param == 'principal':
            self.assertIsNone(message.from_user_subjects)
        else:
            self.assertEqual(message.from_user_subjects, self.subject.name)
        self.assertEqual(message.target_users_role, UserProfile.UserRoles.PARENT)
        self.assertIsNone(message.target_study_class)
        self.assertEqual(message.targets_count, 1)

        self.assertEqual(TargetUserThrough.objects.filter(notification=message).count(), 1)
        target_user_through = TargetUserThrough.objects.get(notification=message, user_profile=self.parent)
        if profile_param == 'principal':
            self.assertEqual(target_user_through.children.count(), 2)
        else:
            self.assertEqual(target_user_through.children.count(), 1)

        self.assertEqual(mocked_send_mail.call_count, 1)
        self.assertEqual(mocked_send_mass_mail.call_count, 0)
        self.assertEqual(mocked_send_sms.call_count, 1)

        if profile_param == 'teacher':
            # Add as teacher to the other class too
            TeacherClassThroughFactory(teacher=self.teacher, study_class=another_study_class, subject=self.another_subject)
            TeacherClassThroughFactory(teacher=self.teacher, study_class=another_study_class, subject=self.subject)

            response = self.client.post(self.url, self.notification_for_one_parent)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

            message = Notification.objects.get(id=response.data['id'])
            self.assertEqual(message.from_user_subjects, self.another_subject.name + '__' + self.subject.name)

            target_user_through = TargetUserThrough.objects.get(notification=message, user_profile=self.parent)
            self.assertEqual(target_user_through.children.count(), 2)

            self.assertEqual(mocked_send_mail.call_count, 2)
            self.assertEqual(mocked_send_mass_mail.call_count, 0)
            self.assertEqual(mocked_send_sms.call_count, 2)
