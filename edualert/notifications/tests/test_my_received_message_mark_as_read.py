from ddt import data, ddt, unpack
from django.urls import reverse
from rest_framework import status

from edualert.common.api_tests import CommonAPITestCase
from edualert.notifications.factories import NotificationFactory, TargetUserThroughFactory
from edualert.notifications.models import Notification
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.study_classes.factories import StudyClassFactory


@ddt
class MyReceivedMessageMarkAsReadTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.principal = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL)
        cls.school_unit = RegisteredSchoolUnitFactory(school_principal=cls.principal)
        cls.teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=cls.school_unit)
        cls.parent = UserProfileFactory(user_role=UserProfile.UserRoles.PARENT, school_unit=cls.school_unit)
        cls.student = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=cls.school_unit)
        cls.study_class = StudyClassFactory(school_unit=cls.school_unit)
        cls.notification = NotificationFactory()
        cls.target_user_through = TargetUserThroughFactory(notification=cls.notification, user_profile=cls.parent)

    @staticmethod
    def build_url(message_id):
        return reverse('notifications:my-received-message-mark-as-read', kwargs={'id': message_id})

    def test_my_received_message_mark_as_read_unauthenticated(self):
        response = self.client.post(self.build_url(self.target_user_through.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.PRINCIPAL,
        UserProfile.UserRoles.TEACHER
    )
    def test_my_received_message_mark_as_read_wrong_user_type(self, user_role):
        profile = UserProfileFactory(
            user_role=user_role,
            school_unit=RegisteredSchoolUnitFactory() if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )
        self.client.login(username=profile.username, password='passwd')

        response = self.client.post(self.build_url(self.target_user_through.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_my_received_message_mark_as_read_non_existent(self):
        self.client.login(username=self.parent.username, password='passwd')
        response = self.client.post(self.build_url(0))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @data(
        ('student', Notification.ReceiverTypes.CLASS_STUDENTS),
        ('parent', Notification.ReceiverTypes.CLASS_PARENTS)
    )
    @unpack
    def test_my_received_message_mark_as_read_not_own_notification(self, profile_param, receiver_type):
        profile = getattr(self, profile_param)
        self.client.login(username=profile.username, password='passwd')

        other_profile = UserProfileFactory(user_role=profile.user_role)
        notification = NotificationFactory(from_user=self.principal, receiver_type=receiver_type,
                                           target_users_role=other_profile.user_role, target_study_class=self.study_class)
        target_through = TargetUserThroughFactory(notification=notification, is_read=False, user_profile=other_profile)

        response = self.client.post(self.build_url(target_through.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @data(
        ('student', 'teacher', Notification.ReceiverTypes.ONE_STUDENT, UserProfile.UserRoles.STUDENT,
         'English__Mathematics', ['English', 'Mathematics']),
        ('parent', 'teacher', Notification.ReceiverTypes.ONE_PARENT, UserProfile.UserRoles.PARENT, 'Mathematics', ['Mathematics']),
        ('parent', 'principal', Notification.ReceiverTypes.CLASS_PARENTS, UserProfile.UserRoles.PARENT, None, None),
    )
    @unpack
    def test_my_received_notification_mark_as_read_success(self, target_profile_param, sender_profile_param, receiver_type, target_users_role,
                                                           from_user_subjects, from_user_displayed_subjects):
        target_profile = getattr(self, target_profile_param)
        self.client.login(username=target_profile.username, password='passwd')
        sender_profile = getattr(self, sender_profile_param)

        expected_fields = ['id', 'title', 'created', 'is_read', 'from_user', 'from_user_full_name', 'from_user_role', 'from_user_subjects', 'body']
        notification = NotificationFactory(from_user=sender_profile, receiver_type=receiver_type, from_user_subjects=from_user_subjects,
                                           target_users_role=target_users_role, target_study_class=self.study_class)
        target_through = TargetUserThroughFactory(notification=notification, is_read=False, user_profile=target_profile)

        response = self.client.post(self.build_url(target_through.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(response.data.keys(), expected_fields)
        self.assertEqual(response.data['from_user_subjects'], from_user_displayed_subjects)
        target_through.refresh_from_db()
        self.assertEqual(target_through.is_read, True)
