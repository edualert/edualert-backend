from ddt import ddt, data
from django.urls import reverse
from rest_framework import status

from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.study_classes.factories import StudyClassFactory, TeacherClassThroughFactory
from edualert.study_classes.constants import CLASS_GRADE_MAPPING
from edualert.subjects.factories import SubjectFactory


@ddt
class OwnStudyClassListTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.principal = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL)
        cls.school_unit = RegisteredSchoolUnitFactory(school_principal=cls.principal)
        cls.teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=cls.school_unit)
        cls.academic_year = 2020

    @staticmethod
    def build_url(academic_year):
        return reverse('study_classes:own-study-class-list', kwargs={'academic_year': academic_year})

    def test_own_study_class_list_unauthenticated(self):
        response = self.client.get(self.build_url(self.academic_year))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.PRINCIPAL,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_own_study_class_list_wrong_user_type(self, user_role):
        user = UserProfileFactory(
            user_role=user_role,
            school_unit=self.school_unit if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )
        self.client.login(username=user.username, password='passwd')

        response = self.client.get(self.build_url(self.academic_year))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_own_study_class_list(self):
        self.client.login(username=self.teacher.username, password='passwd')

        expected_class_through_fields = ['id', 'study_class_id', 'class_grade', 'class_letter', 'academic_program_name', 'subjects', 'is_class_master']
        subject_expected_fields = ['id', 'name']

        # Add a study class where the teacher is a class master and teaches one subject
        study_class = StudyClassFactory(
            class_grade='IX',
            class_grade_arabic=9,
            class_letter='A',
            school_unit=self.school_unit,
            class_master=self.teacher,
        )
        subject = SubjectFactory(name='Subject A')
        class_master_through = TeacherClassThroughFactory(
            teacher=self.teacher,
            academic_year=self.academic_year,
            is_class_master=True,
            class_grade='IX',
            class_letter='A',
            subject=subject,
            study_class=study_class
        )
        response = self.client.get(self.build_url(self.academic_year))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(response.data.keys(), ['class_master'])
        self.assertEqual(len(response.data['class_master']), 1)
        self.assertCountEqual(response.data['class_master'][0].keys(), expected_class_through_fields)
        self.assertEqual(len(response.data['class_master'][0]['subjects']), 1)

        subject_data = response.data['class_master'][0]['subjects'][0]
        self.assertCountEqual(subject_data.keys(), subject_expected_fields)
        self.assertEqual(subject_data['id'], class_master_through.subject.id)

        # Add another subject for the same study class
        subject2 = SubjectFactory(name='Subject B')
        TeacherClassThroughFactory(
            teacher=self.teacher,
            academic_year=self.academic_year,
            is_class_master=True,
            class_grade='IX',
            class_letter='A',
            subject=subject2,
            study_class=study_class
        )
        response = self.client.get(self.build_url(self.academic_year))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(response.data.keys(), ['class_master'])
        self.assertEqual(len(response.data['class_master']), 1)
        self.assertEqual(len(response.data['class_master'][0]['subjects']), 2)

        # Add a coordination subject
        coordination_subject = SubjectFactory(name='Subject C', is_coordination=True)
        TeacherClassThroughFactory(
            teacher=self.teacher,
            academic_year=self.academic_year,
            is_class_master=True,
            class_grade='IX',
            class_letter='B',
            subject=coordination_subject,
            study_class=study_class
        )
        response = self.client.get(self.build_url(self.academic_year))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(response.data.keys(), ['class_master'])
        self.assertEqual(len(response.data['class_master']), 1)
        self.assertEqual(len(response.data['class_master'][0]['subjects']), 2)

        # Make the teacher class master to another class from another academic year
        study_class_past = StudyClassFactory(
            class_grade='VIII',
            class_grade_arabic=8,
            class_letter='A',
            school_unit=self.school_unit,
            class_master=self.teacher,
            academic_year=self.academic_year - 1
        )
        TeacherClassThroughFactory(
            teacher=self.teacher,
            academic_year=self.academic_year - 1,
            is_class_master=True,
            class_grade='VIII',
            class_letter='A',
            subject=subject2,
            study_class=study_class_past
        )
        response = self.client.get(self.build_url(self.academic_year))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(response.data.keys(), ['class_master'])
        self.assertEqual(len(response.data['class_master']), 1)
        self.assertEqual(len(response.data['class_master'][0]['subjects']), 2)
        self.assertEqual(response.data['class_master'][0]['subjects'][0]['name'], subject.name)
        self.assertEqual(response.data['class_master'][0]['subjects'][1]['name'], subject2.name)

        # Create a few classes for the teacher where he isn't a class master
        study_class1 = StudyClassFactory(
            class_grade='XII',
            class_grade_arabic=12,
            class_letter='A',
            school_unit=self.school_unit,
            class_master=self.teacher,
            academic_year=self.academic_year
        )
        TeacherClassThroughFactory(
            teacher=self.teacher,
            academic_year=self.academic_year,
            is_class_master=False,
            class_grade='XII',
            class_letter='A',
            subject=subject,
            study_class=study_class1
        )
        study_class2 = StudyClassFactory(
            class_grade='XI',
            class_grade_arabic=11,
            class_letter='B',
            school_unit=self.school_unit,
            class_master=self.teacher,
            academic_year=self.academic_year
        )
        TeacherClassThroughFactory(
            teacher=self.teacher,
            academic_year=self.academic_year,
            is_class_master=False,
            class_grade='XI',
            class_letter='B',
            subject=subject,
            study_class=study_class2
        )
        TeacherClassThroughFactory(
            teacher=self.teacher,
            academic_year=self.academic_year,
            is_class_master=False,
            class_grade='XI',
            class_letter='B',
            subject=subject2,
            study_class=study_class2
        )
        response = self.client.get(self.build_url(self.academic_year))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertCountEqual(response.data.keys(), ['class_master', 'XI', 'XII'])
        self.assertEqual(len(response.data['class_master']), 1)
        self.assertCountEqual(response.data['XI'][0].keys(), expected_class_through_fields)
        self.assertCountEqual(response.data['XI'][0]['subjects'][0].keys(), subject_expected_fields)
        self.assertCountEqual(response.data['XII'][0].keys(), expected_class_through_fields)
        self.assertCountEqual(response.data['XII'][0]['subjects'][0].keys(), subject_expected_fields)
        self.assertEqual(len(response.data['XI'][0]['subjects']), 2)
        self.assertEqual(response.data['XI'][0]['subjects'][0]['name'], subject.name)
        self.assertEqual(response.data['XI'][0]['subjects'][1]['name'], subject2.name)
        self.assertEqual(len(response.data['XII'][0]['subjects']), 1)

    def test_own_study_class_list_ordering(self):
        self.client.login(username=self.teacher.username, password='passwd')

        subject = SubjectFactory(name='Subject')
        class_grades = ['IX', 'X', 'XI']
        class_letters = ['A', 'B', 'C']

        for class_grade in class_grades:
            for class_letter in class_letters:
                study_class = StudyClassFactory(
                    class_grade=class_grade,
                    class_grade_arabic=CLASS_GRADE_MAPPING[class_grade],
                    class_letter=class_letter,
                    school_unit=self.school_unit,
                )
                TeacherClassThroughFactory(
                    teacher=self.teacher,
                    academic_year=self.academic_year,
                    is_class_master=False,
                    class_grade=class_grade,
                    class_letter=class_letter,
                    subject=subject,
                    study_class=study_class
                )

        response = self.client.get(self.build_url(self.academic_year))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.data
        response_data.pop('class_master')

        for response_class_grade, class_grade in zip(response_data, class_grades):
            self.assertEqual(response_class_grade, class_grade)
            for subject_response, class_letter in zip(response_data[response_class_grade], class_letters):
                self.assertEqual(subject_response['class_letter'], class_letter)
