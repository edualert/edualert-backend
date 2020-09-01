from ddt import ddt, data, unpack
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from edualert.academic_calendars.factories import AcademicYearCalendarFactory
from edualert.common.api_tests import CommonAPITestCase
from edualert.notifications.factories import NotificationFactory, TargetUserThroughFactory
from edualert.notifications.models import Notification
from edualert.profiles.factories import UserProfileFactory, LabelFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.study_classes.factories import StudyClassFactory, TeacherClassThroughFactory
from edualert.subjects.factories import SubjectFactory


@ddt
class UserProfileDetailTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        AcademicYearCalendarFactory()
        cls.admin = UserProfileFactory(user_role=UserProfile.UserRoles.ADMINISTRATOR)
        cls.principal = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL)
        cls.school_unit = RegisteredSchoolUnitFactory(school_principal=cls.principal)
        cls.teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=cls.school_unit)
        cls.parent = UserProfileFactory(user_role=UserProfile.UserRoles.PARENT, school_unit=cls.school_unit)
        cls.student = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=cls.school_unit,
                                         student_in_class=StudyClassFactory(school_unit=cls.school_unit))
        cls.subject = SubjectFactory()

    @staticmethod
    def build_url(profile_id):
        return reverse('users:user-profile-detail', kwargs={'id': profile_id})

    def test_user_profile_detail_unauthenticated(self):
        response = self.client.get(self.build_url(self.admin.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        'admin', 'principal', 'teacher', 'parent', 'student'
    )
    def test_user_profile_detail_not_found(self, profile):
        self.client.login(username=getattr(self, profile).username, password='passwd')

        response = self.client.get(self.build_url(0))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @data(
        ('admin', ['teacher', 'parent', 'student']),
        ('principal', ['admin', 'principal']),
        ('teacher', ['admin', 'principal']),
        ('parent', ['admin', 'parent', 'student']),
        ('student', ['admin', 'parent', 'student']),
    )
    @unpack
    def test_user_profile_detail_wrong_user_type(self, login_user, request_users):
        self.client.login(username=getattr(self, login_user).username, password='passwd')

        for profile_param in request_users:
            response = self.client.get(self.build_url(getattr(self, profile_param).id))
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_detail(self):
        self.client.login(username=self.admin.username, password='passwd')
        another_admin = UserProfileFactory(user_role=UserProfile.UserRoles.ADMINISTRATOR)

        response = self.client.get(self.build_url(another_admin.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_fields = ['id', 'full_name', 'user_role', 'email', 'phone_number',
                           'use_phone_as_username', 'is_active', 'last_online']
        self.assertCountEqual(response.data.keys(), expected_fields)

    @data(
        'admin', 'parent', 'student'
    )
    def test_principal_detail(self, profile_param):
        self.client.login(username=getattr(self, profile_param).username, password='passwd')
        self.principal.labels.add(LabelFactory(user_role=UserProfile.UserRoles.PRINCIPAL))

        response = self.client.get(self.build_url(self.principal.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_fields = ['id', 'full_name', 'user_role', 'email', 'phone_number', 'use_phone_as_username',
                           'is_active', 'last_online', 'labels', 'school_unit']
        self.assertCountEqual(response.data.keys(), expected_fields)
        self.assertCountEqual(response.data['labels'][0].keys(), ['id', 'text'])
        self.assertCountEqual(response.data['school_unit'].keys(), ['id', 'name'])
        self.assertEqual(response.data['school_unit']['id'], self.school_unit.id)

    @data(
        'principal', 'teacher', 'parent', 'student'
    )
    def test_teacher_detail(self, profile_param):
        self.client.login(username=getattr(self, profile_param).username, password='passwd')

        profile = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=self.school_unit)
        profile.labels.add(LabelFactory(user_role=UserProfile.UserRoles.TEACHER))
        profile.taught_subjects.add(self.subject)

        study_class1 = StudyClassFactory(school_unit=self.school_unit, class_master=profile, class_grade='IX', class_grade_arabic=9)
        teacher_class_through1 = TeacherClassThroughFactory(study_class=study_class1, teacher=profile, is_class_master=True,
                                                            subject=SubjectFactory(name='A subject'))
        teacher_class_through2 = TeacherClassThroughFactory(study_class=study_class1, teacher=profile, is_class_master=True,
                                                            subject=SubjectFactory(name='Dirigentie', is_coordination=True))
        study_class2 = StudyClassFactory(school_unit=self.school_unit)
        teacher_class_through3 = TeacherClassThroughFactory(study_class=study_class2, teacher=profile)
        study_class3 = StudyClassFactory(school_unit=self.school_unit, academic_year=2019)
        TeacherClassThroughFactory(study_class=study_class3, teacher=profile)

        response = self.client.get(self.build_url(profile.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_fields = ['id', 'full_name', 'user_role', 'email', 'phone_number', 'use_phone_as_username',
                           'is_active', 'last_online', 'labels', 'taught_subjects', 'assigned_study_classes']
        self.assertCountEqual(response.data.keys(), expected_fields)
        self.assertCountEqual(response.data['labels'][0].keys(), ['id', 'text'])
        self.assertCountEqual(response.data['taught_subjects'][0].keys(), ['id', 'name'])
        self.assertEqual(len(response.data['assigned_study_classes']), 3)
        self.assertCountEqual(response.data['assigned_study_classes'][0].keys(), ['id', 'study_class_id', 'class_grade', 'class_letter',
                                                                                  'subject_id', 'subject_name', 'is_optional_subject'])
        self.assertEqual(response.data['assigned_study_classes'][0]['id'], teacher_class_through3.id)
        self.assertEqual(response.data['assigned_study_classes'][1]['id'], teacher_class_through1.id)
        self.assertEqual(response.data['assigned_study_classes'][2]['id'], teacher_class_through2.id)

    @data(
        'principal', 'teacher'
    )
    def test_parent_detail(self, profile_param):
        self.client.login(username=getattr(self, profile_param).username, password='passwd')
        self.parent.labels.add(LabelFactory(user_role=UserProfile.UserRoles.PARENT))

        response = self.client.get(self.build_url(self.parent.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_fields = ['id', 'full_name', 'user_role', 'email', 'phone_number',
                           'use_phone_as_username', 'is_active', 'last_online', 'labels', 'address']
        self.assertCountEqual(response.data.keys(), expected_fields)
        self.assertCountEqual(response.data['labels'][0].keys(), ['id', 'text'])

    @data(
        'principal', 'teacher'
    )
    def test_student_detail(self, profile_param):
        self.client.login(username=getattr(self, profile_param).username, password='passwd')
        self.student.labels.add(LabelFactory(user_role=UserProfile.UserRoles.STUDENT))
        self.student.parents.add(UserProfileFactory(user_role=UserProfile.UserRoles.PARENT))

        response = self.client.get(self.build_url(self.student.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_fields = ['id', 'full_name', 'user_role', 'email', 'phone_number',
                           'use_phone_as_username', 'is_active', 'last_online', 'labels', 'risk_description',
                           'student_in_class', 'address', 'personal_id_number', 'birth_date',
                           'parents', 'educator_full_name', 'educator_email', 'educator_phone_number']
        self.assertCountEqual(response.data.keys(), expected_fields)
        self.assertCountEqual(response.data['labels'][0].keys(), ['id', 'text'])
        self.assertCountEqual(response.data['parents'][0].keys(), ['id', 'full_name', 'phone_number', 'email', 'address'])
        self.assertCountEqual(response.data['student_in_class'].keys(), ['id', 'class_grade', 'class_letter'])

    @data(
        'principal', 'teacher'
    )
    def test_student_detail_include_risk_alerts(self, profile_param):
        self.client.login(username=getattr(self, profile_param).username, password='passwd')
        self.student.labels.add(LabelFactory(user_role=UserProfile.UserRoles.STUDENT))
        self.student.parents.add(self.parent)

        notification1 = NotificationFactory()
        target_user_through1 = TargetUserThroughFactory(notification=notification1, user_profile=self.student, sent_at_email='abc@test.com')
        notification2 = NotificationFactory(receiver_type=Notification.ReceiverTypes.ONE_PARENT,
                                            target_users_role=UserProfile.UserRoles.PARENT, send_sms=True)
        target_user_through2 = TargetUserThroughFactory(notification=notification2, user_profile=self.parent, sent_at_phone_number='0712345678')
        target_user_through2.children.add(self.student)

        response = self.client.get(self.build_url(self.student.id), {'include_risk_alerts': 'true'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_fields = ['id', 'full_name', 'user_role', 'email', 'phone_number',
                           'use_phone_as_username', 'is_active', 'last_online', 'labels', 'risk_description',
                           'student_in_class', 'address', 'personal_id_number', 'birth_date',
                           'parents', 'educator_full_name', 'educator_email', 'educator_phone_number', 'risk_alerts']
        self.assertCountEqual(response.data.keys(), expected_fields)
        self.assertCountEqual(response.data['labels'][0].keys(), ['id', 'text'])
        self.assertCountEqual(response.data['parents'][0].keys(), ['id', 'full_name', 'phone_number', 'email', 'address'])
        self.assertCountEqual(response.data['student_in_class'].keys(), ['id', 'class_grade', 'class_letter'])

        risk_alerts = response.data['risk_alerts']
        self.assertEqual(risk_alerts['dates'], {timezone.now().date()})
        self.assertEqual(risk_alerts['alerted_users'][0], {
            'id': self.student.id,
            'user_role': UserProfile.UserRoles.STUDENT,
            'full_name': self.student.full_name,
            'email': target_user_through1.sent_at_email,
            'phone_number': None
        })
        self.assertEqual(risk_alerts['alerted_users'][1], {
            'id': self.parent.id,
            'user_role': UserProfile.UserRoles.PARENT,
            'full_name': self.parent.full_name,
            'email': None,
            'phone_number': target_user_through2.sent_at_phone_number
        })
