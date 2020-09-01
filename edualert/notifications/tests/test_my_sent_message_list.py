import datetime

from ddt import data, ddt
from django.urls import reverse
from pytz import utc
from rest_framework import status

from edualert.common.api_tests import CommonAPITestCase
from edualert.notifications.factories import NotificationFactory, TargetUserThroughFactory
from edualert.notifications.models import Notification
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.study_classes.factories import StudyClassFactory, TeacherClassThroughFactory


@ddt
class MySentMessageListTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.principal = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL)
        cls.school_unit = RegisteredSchoolUnitFactory(school_principal=cls.principal)
        cls.teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=cls.school_unit)
        cls.url = reverse('notifications:my-sent-message-list')

    def test_my_sent_message_list_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_my_sent_message_list_wrong_user_type(self, user_role):
        profile = UserProfileFactory(
            user_role=user_role,
            school_unit=RegisteredSchoolUnitFactory() if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )
        self.client.login(username=profile.username, password='passwd')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @data(
        'principal', 'teacher'
    )
    def test_my_sent_message_list_success(self, profile_param):
        profile = getattr(self, profile_param)
        self.client.login(username=profile.username, password='passwd')

        study_class = StudyClassFactory(school_unit=self.school_unit)

        # Target = Class students
        notification1 = NotificationFactory(title='title 1', from_user=profile, receiver_type=Notification.ReceiverTypes.CLASS_STUDENTS,
                                            target_users_role=UserProfile.UserRoles.STUDENT, target_study_class=study_class, targets_count=25)
        for _ in range(5):
            TargetUserThroughFactory(notification=notification1, is_read=True,
                                     user_profile=UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT,
                                                                     school_unit=self.school_unit, student_in_class=study_class))

        # Target = Class parents
        notification2 = NotificationFactory(title='title 2', from_user=profile, receiver_type=Notification.ReceiverTypes.CLASS_PARENTS,
                                            target_users_role=UserProfile.UserRoles.PARENT, target_study_class=study_class, targets_count=15)
        for _ in range(7):
            TargetUserThroughFactory(notification=notification2, is_read=True,
                                     user_profile=UserProfileFactory(user_role=UserProfile.UserRoles.PARENT, school_unit=self.school_unit))

        # Target = One student
        student = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=self.school_unit,
                                     student_in_class=study_class, full_name='Student full name')
        notification3 = NotificationFactory(title='title 3', from_user=profile, receiver_type=Notification.ReceiverTypes.ONE_STUDENT,
                                            target_users_role=UserProfile.UserRoles.STUDENT, target_study_class=study_class, targets_count=1)
        TargetUserThroughFactory(notification=notification3, user_profile=student)

        # Target = One parent
        notification4 = NotificationFactory(title='title 4', from_user=profile, receiver_type=Notification.ReceiverTypes.ONE_PARENT,
                                            target_users_role=UserProfile.UserRoles.PARENT, targets_count=1, target_study_class=None)
        parent = UserProfileFactory(user_role=UserProfile.UserRoles.PARENT, school_unit=self.school_unit, full_name='Parent full name')
        another_student = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=self.school_unit, student_in_class=study_class)
        target_user_through = TargetUserThroughFactory(notification=notification4, user_profile=parent, is_read=True)
        target_user_through.children.add(student, another_student)
        if profile.user_role == UserProfile.UserRoles.TEACHER:
            TeacherClassThroughFactory(teacher=profile, study_class=study_class)

        # A notification from another sender
        NotificationFactory(title='notification from another user', from_user=UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER),
                            receiver_type=Notification.ReceiverTypes.CLASS_STUDENTS, target_users_role=UserProfile.UserRoles.STUDENT,
                            target_study_class=study_class, targets_count=25)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 4)
        results = response.data['results']
        expected_fields = ['id', 'title', 'created', 'send_sms', 'status', 'receiver_type', 'target_users_role',
                           'target_study_class', 'target_user_through']
        expected_study_class_fields = ['id', 'class_grade', 'class_letter']

        # Check 1st notification data
        self.assertCountEqual(list(results[0]), expected_fields)
        self.assertEqual(results[0]['id'], notification4.id)
        self.assertEqual(results[0]['status']['sent_to_count'], 1)
        self.assertEqual(results[0]['status']['read_by_count'], 1)
        self.assertIsNone(results[0]['target_study_class'])
        target_user_through_data = results[0]['target_user_through']
        self.assertCountEqual(list(target_user_through_data), ['user_profile', 'user_profile_full_name', 'children'])
        self.assertEqual(target_user_through_data['user_profile'], parent.id)
        self.assertEqual(len(target_user_through_data['children']), 2)
        self.assertCountEqual(list(target_user_through_data['children'][0]), ['id', 'full_name', 'study_class'])
        self.assertCountEqual(list(target_user_through_data['children'][0]['study_class']), expected_study_class_fields)

        # Check 2nd notification data
        self.assertCountEqual(list(results[1]), expected_fields)
        self.assertEqual(results[1]['id'], notification3.id)
        self.assertEqual(results[1]['status']['sent_to_count'], 1)
        self.assertEqual(results[1]['status']['read_by_count'], 0)
        self.assertCountEqual(list(results[1]['target_study_class']), expected_study_class_fields)
        self.assertCountEqual(list(results[1]['target_user_through']), ['user_profile', 'user_profile_full_name'])
        self.assertEqual(results[1]['target_user_through']['user_profile'], student.id)

        # Check 3rd notification data
        self.assertCountEqual(list(results[2]), expected_fields)
        self.assertEqual(results[2]['id'], notification2.id)
        self.assertEqual(results[2]['status']['sent_to_count'], 15)
        self.assertEqual(results[2]['status']['read_by_count'], 7)
        self.assertCountEqual(list(results[2]['target_study_class']), expected_study_class_fields)

        # Check 4th notification data
        self.assertCountEqual(list(results[3]), expected_fields)
        self.assertEqual(results[3]['id'], notification1.id)
        self.assertEqual(results[3]['status']['sent_to_count'], 25)
        self.assertEqual(results[3]['status']['read_by_count'], 5)
        self.assertCountEqual(list(results[3]['target_study_class']), expected_study_class_fields)

        # Search by title
        response = self.client.get(self.url, {'search': 'title 4'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], notification4.id)

        # Search by receiver name
        response = self.client.get(self.url, {'search': 'Student full'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], notification3.id)

        # Filter by created
        notification1.created = datetime.datetime(2020, 1, 1, tzinfo=utc)
        notification1.save()
        response = self.client.get(self.url, {'created': '01-01-2020'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], notification1.id)

        response = self.client.get(self.url, {'created': '2020-01-01'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 4)
