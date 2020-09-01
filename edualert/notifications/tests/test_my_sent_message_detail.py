from ddt import data, ddt
from django.urls import reverse
from rest_framework import status

from edualert.common.api_tests import CommonAPITestCase
from edualert.notifications.factories import NotificationFactory, TargetUserThroughFactory
from edualert.notifications.models import Notification
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.study_classes.factories import StudyClassFactory, TeacherClassThroughFactory


@ddt
class MySentMessageListDetailTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.principal = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL)
        cls.school_unit = RegisteredSchoolUnitFactory(school_principal=cls.principal)
        cls.teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=cls.school_unit)
        cls.study_class = StudyClassFactory(school_unit=cls.school_unit)
        TeacherClassThroughFactory(teacher=cls.teacher, study_class=cls.study_class)
        cls.notification = NotificationFactory()
        cls.expected_fields = ['id', 'title', 'created', 'send_sms', 'status', 'receiver_type',
                               'target_users_role', 'target_study_class', 'target_user_through', 'body']
        cls.expected_study_class_fields = ['id', 'class_grade', 'class_letter']

    @staticmethod
    def build_url(message_id):
        return reverse('notifications:my-sent-message-detail', kwargs={'id': message_id})

    def test_my_sent_message_detail_unauthenticated(self):
        response = self.client.get(self.build_url(self.notification.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_my_sent_message_detail_wrong_user_type(self, user_role):
        profile = UserProfileFactory(
            user_role=user_role,
            school_unit=RegisteredSchoolUnitFactory() if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )
        self.client.login(username=profile.username, password='passwd')

        response = self.client.get(self.build_url(self.notification.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_my_sent_notification_detail_non_existent(self):
        self.client.login(username=self.principal.username, password='passwd')
        response = self.client.get(self.build_url(0))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_my_sent_notification_detail_from_another_sender(self):
        self.client.login(username=self.teacher.username, password='passwd')

        notification = NotificationFactory(from_user=self.principal)
        response = self.client.get(self.build_url(notification.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @data(
        'principal', 'teacher'
    )
    def test_my_sent_message_detail_class_students(self, profile_param):
        profile = getattr(self, profile_param)
        self.client.login(username=profile.username, password='passwd')

        notification = NotificationFactory(from_user=profile, receiver_type=Notification.ReceiverTypes.CLASS_STUDENTS,
                                           target_users_role=UserProfile.UserRoles.STUDENT, target_study_class=self.study_class, targets_count=25)
        for _ in range(5):
            TargetUserThroughFactory(notification=notification, is_read=True,
                                     user_profile=UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT,
                                                                     school_unit=self.school_unit, student_in_class=self.study_class))

        response = self.client.get(self.build_url(notification.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(response.data.keys(), self.expected_fields)

        self.assertEqual(response.data['status']['sent_to_count'], 25)
        self.assertEqual(response.data['status']['read_by_count'], 5)
        self.assertCountEqual(list(response.data['target_study_class']), self.expected_study_class_fields)

    @data(
        'principal', 'teacher'
    )
    def test_my_sent_message_detail_class_parents(self, profile_param):
        profile = getattr(self, profile_param)
        self.client.login(username=profile.username, password='passwd')

        notification = NotificationFactory(from_user=profile, receiver_type=Notification.ReceiverTypes.CLASS_PARENTS,
                                           target_users_role=UserProfile.UserRoles.PARENT, target_study_class=self.study_class, targets_count=15)
        for _ in range(7):
            TargetUserThroughFactory(notification=notification, is_read=True,
                                     user_profile=UserProfileFactory(user_role=UserProfile.UserRoles.PARENT, school_unit=self.school_unit))

        response = self.client.get(self.build_url(notification.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(response.data.keys(), self.expected_fields)

        self.assertEqual(response.data['status']['sent_to_count'], 15)
        self.assertEqual(response.data['status']['read_by_count'], 7)
        self.assertCountEqual(list(response.data['target_study_class']), self.expected_study_class_fields)

    @data(
        'principal', 'teacher'
    )
    def test_my_sent_message_detail_one_student(self, profile_param):
        profile = getattr(self, profile_param)
        self.client.login(username=profile.username, password='passwd')

        student = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=self.school_unit, student_in_class=self.study_class)
        notification = NotificationFactory(from_user=profile, receiver_type=Notification.ReceiverTypes.ONE_STUDENT,
                                           target_users_role=UserProfile.UserRoles.STUDENT, target_study_class=self.study_class, targets_count=1)
        TargetUserThroughFactory(notification=notification, user_profile=student)

        response = self.client.get(self.build_url(notification.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(response.data.keys(), self.expected_fields)

        self.assertEqual(response.data['status']['sent_to_count'], 1)
        self.assertEqual(response.data['status']['read_by_count'], 0)
        self.assertCountEqual(list(response.data['target_study_class']), self.expected_study_class_fields)
        self.assertCountEqual(list(response.data['target_user_through']), ['user_profile', 'user_profile_full_name'])
        self.assertEqual(response.data['target_user_through']['user_profile'], student.id)

    @data(
        'principal', 'teacher'
    )
    def test_my_sent_message_detail_one_parent(self, profile_param):
        profile = getattr(self, profile_param)
        self.client.login(username=profile.username, password='passwd')

        notification = NotificationFactory(from_user=profile, receiver_type=Notification.ReceiverTypes.ONE_PARENT,
                                           target_users_role=UserProfile.UserRoles.PARENT, targets_count=1, target_study_class=None)
        parent = UserProfileFactory(user_role=UserProfile.UserRoles.PARENT, school_unit=self.school_unit)
        student = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=self.school_unit, student_in_class=self.study_class)
        another_student = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=self.school_unit, student_in_class=self.study_class)
        target_user_through = TargetUserThroughFactory(notification=notification, user_profile=parent, is_read=True)
        target_user_through.children.add(student, another_student)

        response = self.client.get(self.build_url(notification.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(response.data.keys(), self.expected_fields)

        self.assertEqual(response.data['status']['sent_to_count'], 1)
        self.assertEqual(response.data['status']['read_by_count'], 1)
        self.assertIsNone(response.data['target_study_class'])
        target_user_through_data = response.data['target_user_through']
        self.assertCountEqual(list(target_user_through_data), ['user_profile', 'user_profile_full_name', 'children'])
        self.assertEqual(target_user_through_data['user_profile'], parent.id)
        self.assertEqual(len(target_user_through_data['children']), 2)
        self.assertCountEqual(list(target_user_through_data['children'][0]), ['id', 'full_name', 'study_class'])
        self.assertCountEqual(list(target_user_through_data['children'][0]['study_class']), self.expected_study_class_fields)
