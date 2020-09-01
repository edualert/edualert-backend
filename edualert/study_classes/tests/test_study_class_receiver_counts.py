from ddt import data, ddt
from django.urls import reverse
from rest_framework import status

from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.study_classes.factories import StudyClassFactory, TeacherClassThroughFactory


@ddt
class StudyClassReceiverCountsTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.principal = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL)
        cls.school_unit = RegisteredSchoolUnitFactory(school_principal=cls.principal)
        cls.teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=cls.school_unit)
        cls.study_class = StudyClassFactory(school_unit=cls.school_unit)
        TeacherClassThroughFactory(teacher=cls.teacher, study_class=cls.study_class)

    @staticmethod
    def build_url(study_class_id):
        return reverse('study_classes:study-class-receiver-counts', kwargs={'id': study_class_id})

    def test_study_class_receiver_counts_unauthenticated(self):
        response = self.client.get(self.build_url(self.study_class.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.PARENT,
        UserProfile.UserRoles.STUDENT
    )
    def test_study_class_receiver_counts_wrong_user_type(self, user_role):
        profile = UserProfileFactory(
            user_role=user_role,
            school_unit=RegisteredSchoolUnitFactory() if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )
        self.client.login(username=profile.username, password='passwd')

        response = self.client.get(self.build_url(self.study_class.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_study_class_receiver_counts_not_found(self):
        self.client.login(username=self.principal.username, password='passwd')

        response = self.client.get(self.build_url(0))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @data(
        'teacher', 'principal'
    )
    def test_study_class_receiver_counts_parents_list(self, profile_param):
        profile = getattr(self, profile_param)
        self.client.login(username=profile.username, password='passwd')

        # Create a parent without email and one without a phone_number
        student = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, student_in_class=self.study_class)
        parent = UserProfileFactory(user_role=UserProfile.UserRoles.PARENT, phone_number=None, use_phone_as_username=False)
        student.parents.add(parent)

        student1 = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, student_in_class=self.study_class)
        parent1 = UserProfileFactory(user_role=UserProfile.UserRoles.PARENT, username='username')
        parent1.email = None
        parent1.save()
        student1.parents.add(parent1)

        response = self.client.get(self.build_url(self.study_class.id), {'receiver_type': 'CLASS_PARENTS'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_count'], 2)
        self.assertEqual(response.data['emails_count'], 1)
        self.assertEqual(response.data['phone_numbers_count'], 1)

    @data(
        'teacher', 'principal'
    )
    def test_study_class_receiver_counts_students_list(self, profile_param):
        profile = getattr(self, profile_param)
        self.client.login(username=profile.username, password='passwd')

        # Create a student without email and one without a phone_number
        UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, student_in_class=self.study_class, phone_number=None, use_phone_as_username=False)
        profile = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, student_in_class=self.study_class, username='username')
        profile.email = None
        profile.save()

        response = self.client.get(self.build_url(self.study_class.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_count'], 2)
        self.assertEqual(response.data['emails_count'], 1)
        self.assertEqual(response.data['phone_numbers_count'], 1)

        # Create a student from another school
        school_unit = RegisteredSchoolUnitFactory()
        UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=school_unit)
        StudyClassFactory(school_unit=school_unit)

        response = self.client.get(self.build_url(self.study_class.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_count'], 2)

        # Create a student from another class
        other_class = StudyClassFactory(school_unit=self.school_unit)
        UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=self.school_unit, student_in_class=other_class)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_count'], 2)

    def test_study_class_receiver_counts_study_class_from_another_school(self):
        self.client.login(username=self.principal.username, password='passwd')
        school_unit = RegisteredSchoolUnitFactory()
        study_class = StudyClassFactory(school_unit=school_unit)

        response = self.client.get(self.build_url(study_class.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_study_class_receiver_counts_unassigned_study_class(self):
        self.client.login(username=self.teacher.username, password='passwd')
        study_class = StudyClassFactory(school_unit=self.school_unit)

        response = self.client.get(self.build_url(study_class.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
