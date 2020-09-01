from ddt import ddt, data
from django.urls import reverse
from rest_framework import status

from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.study_classes.factories import StudyClassFactory, TeacherClassThroughFactory
from edualert.subjects.factories import SubjectFactory


@ddt
class OwnStudyClassDetailTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.school_unit = RegisteredSchoolUnitFactory()
        cls.teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=cls.school_unit)
        cls.academic_year = 2020
        cls.study_class = StudyClassFactory(school_unit=cls.school_unit, class_master=cls.teacher,
                                            class_grade='IX', class_grade_arabic=9)
        cls.coordination_subject = SubjectFactory(name='Dirigentie', is_coordination=True)
        TeacherClassThroughFactory(study_class=cls.study_class, teacher=cls.teacher, subject=cls.coordination_subject, is_class_master=True)

        cls.subject1 = SubjectFactory(name='Subject')
        cls.subject2 = SubjectFactory(name='Another Subject')

        cls.expected_fields = ['id', 'class_grade', 'class_letter', 'academic_year', 'academic_program_name',
                               'class_master', 'taught_subjects', 'is_class_master']
        cls.class_master_fields = ['id', 'full_name']
        cls.taught_subject_fields = ['id', 'name', 'is_coordination', 'allows_exemption', 'is_optional']

    @staticmethod
    def build_url(study_class_id):
        return reverse('study_classes:own-study-class-detail', kwargs={'id': study_class_id})

    def test_own_study_class_detail_unauthenticated(self):
        response = self.client.get(self.build_url(self.study_class.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.PRINCIPAL,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_own_study_class_detail_wrong_user_type(self, user_role):
        user = UserProfileFactory(
            user_role=user_role,
            school_unit=self.school_unit if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )
        self.client.login(username=user.username, password='passwd')

        response = self.client.get(self.build_url(self.study_class.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_own_study_class_detail_not_own_class(self):
        self.client.login(username=self.teacher.username, password='passwd')

        study_class = StudyClassFactory(school_unit=self.school_unit)
        response = self.client.get(self.build_url(study_class.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_own_study_class_detail_is_class_master(self):
        self.client.login(username=self.teacher.username, password='passwd')

        TeacherClassThroughFactory(study_class=self.study_class, teacher=self.teacher, subject=self.subject1, is_class_master=True)
        TeacherClassThroughFactory(study_class=self.study_class, teacher=self.teacher, subject=self.subject2, is_class_master=True,
                                   is_optional_subject=True)

        response = self.client.get(self.build_url(self.study_class.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertCountEqual(response.data.keys(), self.expected_fields)
        self.assertCountEqual(response.data['class_master'].keys(), self.class_master_fields)
        self.assertEqual(len(response.data['taught_subjects']), 3)
        self.assertCountEqual(response.data['taught_subjects'][0].keys(), self.taught_subject_fields)
        self.assertTrue(response.data['is_class_master'])

        self.assertEqual(response.data['taught_subjects'][0]['id'], self.coordination_subject.id)
        self.assertFalse(response.data['taught_subjects'][0]['is_optional'])
        self.assertEqual(response.data['taught_subjects'][1]['id'], self.subject2.id)
        self.assertTrue(response.data['taught_subjects'][1]['is_optional'])
        self.assertEqual(response.data['taught_subjects'][2]['id'], self.subject1.id)
        self.assertFalse(response.data['taught_subjects'][2]['is_optional'])

    def test_own_study_class_detail_not_class_master(self):
        self.client.login(username=self.teacher.username, password='passwd')

        study_class = StudyClassFactory(school_unit=self.school_unit)
        TeacherClassThroughFactory(study_class=study_class, teacher=self.teacher, subject=self.subject1, is_class_master=True)
        TeacherClassThroughFactory(study_class=study_class, teacher=self.teacher, subject=self.subject2, is_class_master=True,
                                   is_optional_subject=True)

        response = self.client.get(self.build_url(study_class.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertCountEqual(response.data.keys(), self.expected_fields)
        self.assertCountEqual(response.data['class_master'].keys(), self.class_master_fields)
        self.assertEqual(len(response.data['taught_subjects']), 2)
        self.assertCountEqual(response.data['taught_subjects'][0].keys(), self.taught_subject_fields)
        self.assertFalse(response.data['is_class_master'])

        self.assertEqual(response.data['taught_subjects'][0]['id'], self.subject2.id)
        self.assertTrue(response.data['taught_subjects'][0]['is_optional'])
        self.assertEqual(response.data['taught_subjects'][1]['id'], self.subject1.id)
        self.assertFalse(response.data['taught_subjects'][1]['is_optional'])
