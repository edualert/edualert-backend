import datetime

from ddt import data, ddt, unpack
from django.conf import settings
from django.urls import reverse
from pytz import utc
from rest_framework import status

from edualert.common.api_tests import CommonAPITestCase
from edualert.notifications.factories import NotificationFactory, TargetUserThroughFactory
from edualert.notifications.models import Notification
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.study_classes.factories import StudyClassFactory


@ddt
class MyReceivedMessageListTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.principal = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL)
        cls.school_unit = RegisteredSchoolUnitFactory(school_principal=cls.principal)
        cls.teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=cls.school_unit)
        cls.parent = UserProfileFactory(user_role=UserProfile.UserRoles.PARENT, school_unit=cls.school_unit)
        cls.student = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=cls.school_unit)
        cls.study_class = StudyClassFactory(school_unit=cls.school_unit)
        cls.url = reverse('notifications:my-received-message-list')

    def test_my_received_message_list_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.TEACHER,
        UserProfile.UserRoles.PRINCIPAL
    )
    def test_my_received_message_list_wrong_user_type(self, user_role):
        profile = UserProfileFactory(
            user_role=user_role,
            school_unit=RegisteredSchoolUnitFactory() if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )
        self.client.login(username=profile.username, password='passwd')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @data(
        ('student', 'teacher', Notification.ReceiverTypes.ONE_STUDENT, UserProfile.UserRoles.STUDENT,
         'English__Mathematics', ['English', 'Mathematics']),
        ('parent', 'teacher', Notification.ReceiverTypes.ONE_PARENT, UserProfile.UserRoles.PARENT, 'Mathematics', ['Mathematics']),
        ('parent', 'principal', Notification.ReceiverTypes.CLASS_PARENTS, UserProfile.UserRoles.PARENT, None, None),
    )
    @unpack
    def test_my_received_message_list_success(self, target_profile_param, sender_profile_param, receiver_type, target_users_role,
                                              from_user_subjects, from_user_displayed_subjects):
        target_profile = getattr(self, target_profile_param)
        self.client.login(username=target_profile.username, password='passwd')
        sender_profile = getattr(self, sender_profile_param)

        # Create a few notifications
        for _ in range(5):
            notification = NotificationFactory(from_user=sender_profile, receiver_type=receiver_type, from_user_subjects=from_user_subjects,
                                               target_users_role=target_users_role, target_study_class=self.study_class)
            TargetUserThroughFactory(notification=notification, is_read=True, user_profile=target_profile)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)

        expected_fields = ['id', 'title', 'created', 'from_user', 'from_user_full_name', 'from_user_role', 'from_user_subjects', 'is_read']
        received_notifications = response.data['results']
        for notification_data in received_notifications:
            self.assertCountEqual(notification_data.keys(), expected_fields)
            self.assertTrue(notification_data['is_read'])
            self.assertEqual(notification_data['from_user_subjects'], from_user_displayed_subjects)

    def test_my_received_message_list_search(self):
        self.client.login(username=self.parent.username, password='passwd')

        notification1 = NotificationFactory(title='title', from_user_subjects='English__Mathematics',
                                            from_user=self.teacher, receiver_type=Notification.ReceiverTypes.CLASS_PARENTS,
                                            target_users_role=UserProfile.UserRoles.PARENT, target_study_class=self.study_class)
        TargetUserThroughFactory(notification=notification1, is_read=True, user_profile=self.parent)

        notification2 = NotificationFactory(title='other', from_user=self.principal, receiver_type=Notification.ReceiverTypes.ONE_PARENT,
                                            target_users_role=UserProfile.UserRoles.PARENT, target_study_class=None)
        TargetUserThroughFactory(notification=notification2, is_read=True, user_profile=self.parent)

        response = self.client.get(self.url, {'search': 'other'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], notification2.title)

        response = self.client.get(self.url, {'search': self.teacher.full_name})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['from_user_full_name'], self.teacher.full_name)

    def test_my_received_message_list_filters(self):
        self.client.login(username=self.parent.username, password='passwd')

        notification1 = NotificationFactory(title='title', from_user_subjects='English__Mathematics',
                                            from_user=self.teacher, receiver_type=Notification.ReceiverTypes.CLASS_PARENTS,
                                            target_users_role=UserProfile.UserRoles.PARENT, target_study_class=self.study_class)
        TargetUserThroughFactory(notification=notification1, is_read=True, user_profile=self.parent)

        notification2 = NotificationFactory(title='other', from_user=self.principal, receiver_type=Notification.ReceiverTypes.ONE_PARENT,
                                            target_users_role=UserProfile.UserRoles.PARENT, target_study_class=None)
        TargetUserThroughFactory(notification=notification2, is_read=True, user_profile=self.parent)

        notification2.created = datetime.datetime(2020, 4, 1, tzinfo=utc)
        notification2.save()

        response = self.client.get(self.url, {'created': datetime.datetime.now().strftime(settings.DATE_FORMAT)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], notification1.title)
