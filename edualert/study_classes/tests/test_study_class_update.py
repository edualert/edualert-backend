import datetime
from copy import copy
from unittest.mock import patch

from dateutil import tz
from ddt import data, ddt
from django.urls import reverse
from rest_framework import status

from edualert.academic_calendars.factories import AcademicYearCalendarFactory
from edualert.academic_programs.factories import AcademicProgramFactory
from edualert.catalogs.factories import StudentCatalogPerYearFactory
from edualert.catalogs.models import StudentCatalogPerYear, StudentCatalogPerSubject, SubjectGrade
from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory, SchoolUnitCategoryFactory
from edualert.schools.models import SchoolUnitCategory
from edualert.study_classes.factories import StudyClassFactory, TeacherClassThroughFactory
from edualert.study_classes.models import StudyClass, TeacherClassThrough
from edualert.subjects.factories import SubjectFactory, ProgramSubjectThroughFactory


@ddt
class StudyClassUpdateTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.principal = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL)
        cls.school_unit = RegisteredSchoolUnitFactory(school_principal=cls.principal)

        cls.category1 = SchoolUnitCategoryFactory(category_level=SchoolUnitCategory.CategoryLevels.SECONDARY_SCHOOL)
        cls.category2 = SchoolUnitCategoryFactory(category_level=SchoolUnitCategory.CategoryLevels.HIGHSCHOOL)
        cls.school_unit.categories.add(cls.category1, cls.category2)

        cls.calendar = AcademicYearCalendarFactory()

        cls.subject1 = SubjectFactory()
        cls.subject2 = SubjectFactory()
        cls.coordination_subject = SubjectFactory(is_coordination=True)
        cls.academic_program = AcademicProgramFactory(school_unit=cls.school_unit)
        for class_grade, class_grade_arabic in zip(['VI', 'X'], [6, 10]):
            ProgramSubjectThroughFactory(academic_program=cls.academic_program, subject=cls.subject1,
                                         is_mandatory=False, class_grade=class_grade, class_grade_arabic=class_grade_arabic)
            ProgramSubjectThroughFactory(generic_academic_program=cls.academic_program.generic_academic_program,
                                         subject=cls.subject2, class_grade=class_grade, class_grade_arabic=class_grade_arabic)

        cls.teacher1 = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=cls.school_unit)
        cls.teacher2 = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=cls.school_unit)
        cls.teacher1.taught_subjects.add(cls.subject1, cls.subject2)
        cls.teacher2.taught_subjects.add(cls.subject1, cls.subject2)

        cls.study_class1 = StudyClassFactory(school_unit=cls.school_unit, class_master=cls.teacher1, academic_program=cls.academic_program,
                                             class_grade='X', class_grade_arabic=10, class_letter='A')
        TeacherClassThroughFactory(study_class=cls.study_class1, teacher=cls.teacher1, subject=cls.coordination_subject, is_class_master=True)
        cls.study_class2 = StudyClassFactory(school_unit=cls.school_unit, class_master=cls.teacher2, academic_program=cls.academic_program)
        TeacherClassThroughFactory(study_class=cls.study_class2, teacher=cls.teacher2, subject=cls.coordination_subject, is_class_master=True)

        TeacherClassThroughFactory(study_class=cls.study_class1, teacher=cls.teacher1, subject=cls.subject1, is_class_master=True)
        TeacherClassThroughFactory(study_class=cls.study_class1, teacher=cls.teacher2, subject=cls.subject2, is_class_master=False)
        TeacherClassThroughFactory(study_class=cls.study_class2, teacher=cls.teacher1, subject=cls.subject1, is_class_master=False)
        TeacherClassThroughFactory(study_class=cls.study_class2, teacher=cls.teacher2, subject=cls.subject2, is_class_master=True)

        cls.student1 = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=cls.school_unit, student_in_class=cls.study_class1)
        StudentCatalogPerYearFactory(student=cls.student1, study_class=cls.study_class1)
        cls.student2 = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=cls.school_unit, student_in_class=cls.study_class1)
        StudentCatalogPerYearFactory(student=cls.student2, study_class=cls.study_class1)
        cls.student3 = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=cls.school_unit, student_in_class=cls.study_class2)
        StudentCatalogPerYearFactory(student=cls.student3, study_class=cls.study_class2)

        cls.academic_program2 = AcademicProgramFactory(school_unit=cls.school_unit)
        for class_grade, class_grade_arabic in zip(['VII', 'XI'], [7, 11]):
            ProgramSubjectThroughFactory(academic_program=cls.academic_program2, subject=cls.subject1,
                                         is_mandatory=False, class_grade=class_grade, class_grade_arabic=class_grade_arabic)
            ProgramSubjectThroughFactory(generic_academic_program=cls.academic_program2.generic_academic_program,
                                         subject=cls.subject2, class_grade=class_grade, class_grade_arabic=class_grade_arabic)

        cls.new_teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=cls.school_unit)
        cls.new_student = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=cls.school_unit)

    @staticmethod
    def build_url(study_class_id):
        return reverse('study_classes:study-class-detail', kwargs={'id': study_class_id})

    def setUp(self):
        self.refresh_objects_from_db([self.study_class1, self.study_class2, self.academic_program2])

        self.highschool_request_data = {
            'class_grade': 'XI',
            'class_letter': 'B',
            'academic_program': self.academic_program2.id,
            "class_master": self.new_teacher.id,
            "teachers_class_through": [
                {
                    "teacher": self.teacher2.id,
                    "subject": self.subject1.id,
                },
                {
                    "teacher": self.teacher2.id,
                    "subject": self.subject2.id,
                }
            ],
            "students": [
                self.student1.id,
                self.new_student.id
            ]
        }
        self.secondary_school_request_data = {
            'class_grade': 'VII',
            'class_letter': 'B',
            'academic_program': self.academic_program2.id,
            "class_master": self.new_teacher.id,
            "teachers_class_through": [
                {
                    "teacher": self.teacher1.id,
                    "subject": self.subject1.id,
                },
                {
                    "teacher": self.teacher1.id,
                    "subject": self.subject2.id,
                }
            ],
            "students": [
                self.new_student.id
            ]
        }

    def test_study_class_update_unauthenticated(self):
        url = self.build_url(self.study_class1.id)
        response = self.client.put(url, self.highschool_request_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.TEACHER,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_study_class_update_wrong_user_type(self, user_role):
        user = UserProfileFactory(
            user_role=user_role,
            school_unit=RegisteredSchoolUnitFactory() if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )
        self.client.login(username=user.username, password='passwd')

        url = self.build_url(self.study_class1.id)
        response = self.client.put(url, self.highschool_request_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_study_class_update_not_found(self):
        self.client.login(username=self.principal.username, password='passwd')

        url = self.build_url(0)
        response = self.client.put(url, self.highschool_request_data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_study_class_update_no_calendar(self):
        self.client.login(username=self.principal.username, password='passwd')
        self.calendar.delete()

        url = self.build_url(self.study_class1.id)
        response = self.client.put(url, self.highschool_request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], 'No academic calendar defined.')

    def test_study_class_update_different_year(self):
        self.client.login(username=self.principal.username, password='passwd')
        self.study_class1.academic_year = 2010
        self.study_class1.save()

        url = self.build_url(self.study_class1.id)
        response = self.client.put(url, self.highschool_request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], 'Cannot update a study class from a previous year.')

    # @patch('django.utils.timezone.now')
    # def test_study_class_update_wrong_date(self, timezone_mock):
    #     timezone_mock.return_value = datetime.datetime(self.calendar.academic_year, 9, 16, tzinfo=tz.UTC)
    #     self.client.login(username=self.principal.username, password='passwd')
    #
    #     url = self.build_url(self.study_class1.id)
    #     response = self.client.put(url, self.highschool_request_data)
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertEqual(response.data['message'], 'Cannot update the study class.')

    @patch('django.utils.timezone.now')
    def test_study_class_update_missing_fields(self, timezone_mock):
        timezone_mock.return_value = datetime.datetime(self.calendar.academic_year, 9, 14, tzinfo=tz.UTC)
        self.client.login(username=self.principal.username, password='passwd')
        url = self.build_url(self.study_class1.id)

        required_fields = ['class_grade', 'class_letter', 'academic_program', 'class_master',
                           'teachers_class_through', 'students']

        request_data = copy(self.highschool_request_data)

        for field in required_fields:
            del request_data[field]
            response = self.client.put(url, request_data)

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data, {field: ['This field is required.']})

            request_data = copy(self.highschool_request_data)

    @patch('django.utils.timezone.now')
    def test_study_class_update_validate_class_grade(self, timezone_mock):
        timezone_mock.return_value = datetime.datetime(self.calendar.academic_year, 9, 14, tzinfo=tz.UTC)
        self.client.login(username=self.principal.username, password='passwd')

        for class_grade in ['P', 'IV', 'XX']:
            self.highschool_request_data['class_grade'] = class_grade

            url = self.build_url(self.study_class1.id)
            response = self.client.put(url, self.highschool_request_data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data['class_grade'], ['Invalid class grade.'])

        StudyClassFactory(school_unit=self.school_unit, class_master=self.teacher2, class_grade='V', class_grade_arabic=5,
                          academic_year=self.study_class2.academic_year - 1)
        url = self.build_url(self.study_class2.id)
        response = self.client.put(url, self.secondary_school_request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['class_grade'], ['Cannot change the class grade for a class that has previous catalog data.'])

    @patch('django.utils.timezone.now')
    def test_study_class_update_validate_class_letter(self, timezone_mock):
        timezone_mock.return_value = datetime.datetime(self.calendar.academic_year, 9, 14, tzinfo=tz.UTC)
        self.client.login(username=self.principal.username, password='passwd')

        self.highschool_request_data['class_letter'] = 'Aa1'

        url = self.build_url(self.study_class1.id)
        response = self.client.put(url, self.highschool_request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['class_letter'], ['This value can contain only uppercase letters and digits.'])

    @patch('django.utils.timezone.now')
    def test_study_class_update_validate_class_already_exists(self, timezone_mock):
        timezone_mock.return_value = datetime.datetime(self.calendar.academic_year, 9, 14, tzinfo=tz.UTC)
        self.client.login(username=self.principal.username, password='passwd')

        StudyClassFactory(school_unit=self.school_unit, class_grade='VII', class_grade_arabic=7, class_letter='B')

        url = self.build_url(self.study_class2.id)
        response = self.client.put(url, self.secondary_school_request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['general_errors'], ['This study class already exists.'])

    @patch('django.utils.timezone.now')
    def test_study_class_update_validate_class_master(self, timezone_mock):
        timezone_mock.return_value = datetime.datetime(self.calendar.academic_year, 9, 14, tzinfo=tz.UTC)
        self.client.login(username=self.principal.username, password='passwd')
        url = self.build_url(self.study_class2.id)

        # Not a teacher
        profile1 = UserProfileFactory(user_role=UserProfile.UserRoles.PARENT, school_unit=self.school_unit)
        # From a different school
        profile2 = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=RegisteredSchoolUnitFactory())
        # Already a class master
        profile3 = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=self.school_unit)
        StudyClassFactory(school_unit=self.school_unit, class_master=profile3, class_letter='B')
        # Inactive teacher
        profile4 = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=self.school_unit, is_active=False)

        for profile in [profile1, profile2, profile3, profile4]:
            self.highschool_request_data['class_master'] = profile.id

            response = self.client.put(url, self.highschool_request_data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data['class_master'], ['Invalid user.'])

        self.highschool_request_data['class_master'] = 0

        response = self.client.put(url, self.highschool_request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['class_master'], ['Invalid pk "0" - object does not exist.'])

    @patch('django.utils.timezone.now')
    def test_study_class_update_validate_academic_program(self, timezone_mock):
        timezone_mock.return_value = datetime.datetime(self.calendar.academic_year, 9, 14, tzinfo=tz.UTC)
        self.client.login(username=self.principal.username, password='passwd')

        program1 = AcademicProgramFactory(school_unit=self.school_unit, academic_year=2010)
        program2 = AcademicProgramFactory(school_unit=RegisteredSchoolUnitFactory())
        program3 = AcademicProgramFactory(school_unit=self.school_unit)
        program3.generic_academic_program.category.category_level = SchoolUnitCategory.CategoryLevels.PRIMARY_SCHOOL
        program3.generic_academic_program.category.save()

        for program in [program1, program2, program3]:
            self.highschool_request_data['academic_program'] = program.id

            url = self.build_url(self.study_class1.id)
            response = self.client.put(url, self.highschool_request_data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data, {'academic_program': ['Invalid academic program.']})

        StudyClassFactory(school_unit=self.school_unit, class_master=self.teacher1, class_grade='IX', class_grade_arabic=9,
                          academic_year=self.study_class1.academic_year - 1)
        self.highschool_request_data['academic_program'] = self.academic_program2.id
        self.highschool_request_data['class_grade'] = 'X'
        response = self.client.put(url, self.highschool_request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['academic_program'], ['Cannot change the academic program for a class that has previous catalog data.'])

    @patch('django.utils.timezone.now')
    def test_study_class_update_validate_subjects(self, timezone_mock):
        timezone_mock.return_value = datetime.datetime(self.calendar.academic_year, 9, 14, tzinfo=tz.UTC)
        self.client.login(username=self.principal.username, password='passwd')

        teachers_class_through1 = [
            {
                "teacher": self.teacher1.id,
                "subject": self.subject1.id
            },
            {
                "teacher": self.teacher2.id,
                "subject": self.subject2.id
            },
            {
                "teacher": self.teacher2.id,
                "subject": SubjectFactory().id
            }
        ]
        teachers_class_through2 = [
            {
                "teacher": self.teacher1.id,
                "subject": self.subject1.id
            }
        ]

        for teachers_class_through in [teachers_class_through1, teachers_class_through2]:
            self.highschool_request_data['teachers_class_through'] = teachers_class_through

            url = self.build_url(self.study_class1.id)
            response = self.client.put(url, self.highschool_request_data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data['teachers_class_through'], ['The subjects do not correspond with the academic program subjects.'])

    @patch('django.utils.timezone.now')
    def test_study_class_update_validate_teachers(self, timezone_mock):
        timezone_mock.return_value = datetime.datetime(self.calendar.academic_year, 9, 14, tzinfo=tz.UTC)
        self.client.login(username=self.principal.username, password='passwd')
        url = self.build_url(self.study_class1.id)

        # Not a teacher
        profile1 = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=self.school_unit)
        # Another school unit
        profile2 = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=RegisteredSchoolUnitFactory())
        # Inactive teacher
        profile3 = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=self.school_unit, is_active=False)

        for profile in [profile1, profile2, profile3]:
            self.highschool_request_data['teachers_class_through'] = [
                {
                    "teacher": profile.id,
                    "subject": self.subject1.id
                },
                {
                    "teacher": self.teacher2.id,
                    "subject": self.subject2.id
                }
            ]

            response = self.client.put(url, self.highschool_request_data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data['teachers_class_through'], ['At least one teacher is invalid.'])

        # Subject not in teacher's taught subjects
        profile2.school_unit = self.school_unit
        profile2.save()

        self.highschool_request_data['teachers_class_through'] = [
            {
                "teacher": self.teacher1.id,
                "subject": self.subject1.id
            },
            {
                "teacher": profile2.id,
                "subject": self.subject2.id
            }
        ]

        response = self.client.put(url, self.highschool_request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['teachers_class_through'], ['Teacher {} does not teach {}.'
                         .format(profile2.full_name, self.subject2.name)])

        # User not found
        self.highschool_request_data['teachers_class_through'] = [
            {
                "teacher": 0,
                "subject": self.subject1.id
            },
            {
                "teacher": self.teacher2.id,
                "subject": self.subject2.id
            }
        ]

        response = self.client.put(url, self.highschool_request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['teachers_class_through'][0]['teacher'], ['Invalid pk "0" - object does not exist.'])

    @patch('django.utils.timezone.now')
    def test_study_class_update_validate_students(self, timezone_mock):
        timezone_mock.return_value = datetime.datetime(self.calendar.academic_year, 9, 14, tzinfo=tz.UTC)
        self.client.login(username=self.principal.username, password='passwd')
        url = self.build_url(self.study_class2.id)

        # Not a student
        profile1 = UserProfileFactory(user_role=UserProfile.UserRoles.PARENT, school_unit=self.school_unit)
        # Inactive student
        profile2 = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=self.school_unit, is_active=False)

        for profile_id in [profile1.id, profile2.id, 0]:
            self.highschool_request_data['students'] = [profile_id, ]

            response = self.client.put(url, self.highschool_request_data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data['students'], [f'Invalid pk "{profile_id}" - object does not exist.'])

        # From a different school
        profile1 = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=RegisteredSchoolUnitFactory())
        # Already in a study class
        study_class = StudyClassFactory(school_unit=self.school_unit, class_letter='B')
        profile2 = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=self.school_unit, student_in_class=study_class)

        for profile_id in [profile1.id, profile2.id]:
            self.highschool_request_data['students'] = [profile_id, ]

            response = self.client.put(url, self.highschool_request_data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data['students'], ['At least one student is invalid.'])

    @patch('django.utils.timezone.now')
    def test_study_class_update_success_highschool(self, timezone_mock):
        timezone_mock.return_value = datetime.datetime(self.calendar.academic_year, 9, 14, tzinfo=tz.UTC)
        self.client.login(username=self.principal.username, password='passwd')

        self.refresh_objects_from_db([self.academic_program, self.academic_program2])
        self.assertEqual(self.academic_program.classes_count, 2)
        self.assertEqual(self.academic_program2.classes_count, 0)

        expected_fields = ['id', 'class_grade', 'class_letter', 'academic_year', 'academic_program', 'academic_program_name',
                           'class_master', 'teachers_class_through', 'students', 'has_previous_catalog_data']

        url = self.build_url(self.study_class1.id)
        response = self.client.put(url, self.highschool_request_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(response.data.keys(), expected_fields)
        self.assertEqual(list(response.data['class_master']), ['id', 'full_name'])
        self.assertEqual(list(response.data['teachers_class_through'][0]), ['id', 'teacher', 'subject_id', 'subject_name'])
        self.assertEqual(list(response.data['students'][0]), ['id', 'full_name'])

        study_class = StudyClass.objects.get(id=response.data['id'])
        self.assertEqual(study_class.school_unit_id, self.school_unit.id)
        self.assertEqual(study_class.academic_year, self.calendar.academic_year)
        self.assertEqual(study_class.class_grade_arabic, 11)
        self.assertEqual(study_class.academic_program_name, self.academic_program2.name)
        self.assertEqual(study_class.class_master_id, self.new_teacher.id)

        self.refresh_objects_from_db([self.academic_program, self.academic_program2])
        self.assertEqual(self.academic_program.classes_count, 1)
        self.assertEqual(self.academic_program2.classes_count, 1)

        for (teacher, subject, is_optional, is_class_master) in zip([self.teacher2, self.teacher2, self.new_teacher],
                                                                    [self.subject1, self.subject2, self.coordination_subject],
                                                                    [True, False, False], [False, False, True]):
            self.assertTrue(TeacherClassThrough.objects.filter(study_class=study_class, teacher=teacher, subject=subject,
                                                               is_class_master=is_class_master, is_optional_subject=is_optional,
                                                               is_coordination_subject=is_class_master).exists())

        self.student2.refresh_from_db()
        self.assertIsNone(self.student2.student_in_class_id)
        self.assertFalse(StudentCatalogPerYear.objects.filter(student=self.student2).exists())

        for student in [self.student1, self.new_student]:
            student.refresh_from_db()
            self.assertEqual(student.student_in_class_id, study_class.id)
            catalog_per_year = StudentCatalogPerYear.objects.filter(student=student, study_class=study_class).first()
            self.assertIsNotNone(catalog_per_year)
            self.assertEqual(catalog_per_year.behavior_grade_sem1, 10)
            self.assertEqual(catalog_per_year.behavior_grade_sem2, 10)
            self.assertEqual(catalog_per_year.behavior_grade_annual, 10)

            for (subject, is_enrolled) in zip([self.subject1, self.subject2], [False, True]):
                self.assertTrue(StudentCatalogPerSubject.objects.filter(student=student, teacher=self.teacher2,
                                                                        subject=subject, is_enrolled=is_enrolled).exists())
            coordination_catalog = StudentCatalogPerSubject.objects.filter(student=student, teacher=self.new_teacher,
                                                                           subject=self.coordination_subject, is_enrolled=True).first()
            self.assertIsNotNone(coordination_catalog)
            self.assertTrue(SubjectGrade.objects.filter(catalog_per_subject=coordination_catalog, student=student, semester=1, grade=10).exists())
            self.assertTrue(SubjectGrade.objects.filter(catalog_per_subject=coordination_catalog, student=student, semester=2, grade=10).exists())

    @patch('django.utils.timezone.now')
    def test_study_class_update_success_secondary_school(self, timezone_mock):
        timezone_mock.return_value = datetime.datetime(self.calendar.academic_year, 9, 14, tzinfo=tz.UTC)
        self.client.login(username=self.principal.username, password='passwd')
        self.academic_program2.generic_academic_program.category.category_level = SchoolUnitCategory.CategoryLevels.SECONDARY_SCHOOL
        self.academic_program2.generic_academic_program.category.save()

        expected_fields = ['id', 'class_grade', 'class_letter', 'academic_year', 'academic_program', 'academic_program_name',
                           'class_master', 'teachers_class_through', 'students', 'has_previous_catalog_data']

        url = self.build_url(self.study_class2.id)
        response = self.client.put(url, self.secondary_school_request_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(response.data.keys(), expected_fields)
        self.assertEqual(list(response.data['class_master']), ['id', 'full_name'])
        self.assertEqual(list(response.data['teachers_class_through'][0]), ['id', 'teacher', 'subject_id', 'subject_name'])
        self.assertEqual(list(response.data['students'][0]), ['id', 'full_name'])

        study_class = StudyClass.objects.get(id=response.data['id'])
        self.assertEqual(study_class.school_unit_id, self.school_unit.id)
        self.assertEqual(study_class.academic_year, self.calendar.academic_year)
        self.assertEqual(study_class.class_grade_arabic, 7)
        self.assertEqual(study_class.academic_program_name, self.academic_program2.name)
        self.assertEqual(study_class.class_master_id, self.new_teacher.id)

        for (teacher, subject, is_optional, is_class_master) in zip([self.teacher1, self.teacher1, self.new_teacher],
                                                                    [self.subject1, self.subject2, self.coordination_subject],
                                                                    [True, False, False], [False, False, True]):
            self.assertTrue(TeacherClassThrough.objects.filter(study_class=study_class, teacher=teacher, subject=subject,
                                                               is_class_master=is_class_master, is_optional_subject=is_optional,
                                                               is_coordination_subject=is_class_master).exists())

        self.refresh_objects_from_db([self.student3, self.new_student])
        self.assertIsNone(self.student3.student_in_class_id)
        self.assertEqual(self.new_student.student_in_class_id, study_class.id)
        catalog_per_year = StudentCatalogPerYear.objects.filter(student=self.new_student, study_class=study_class).first()
        self.assertIsNotNone(catalog_per_year)
        self.assertEqual(catalog_per_year.behavior_grade_sem1, 10)
        self.assertEqual(catalog_per_year.behavior_grade_sem2, 10)
        self.assertEqual(catalog_per_year.behavior_grade_annual, 10)

        for (subject, is_enrolled) in zip([self.subject1, self.subject2], [False, True]):
            self.assertTrue(StudentCatalogPerSubject.objects.filter(student=self.new_student, teacher=self.teacher1,
                                                                    subject=subject, is_enrolled=is_enrolled).exists())
        coordination_catalog = StudentCatalogPerSubject.objects.filter(student=self.new_student, teacher=self.new_teacher,
                                                                       subject=self.coordination_subject, is_enrolled=True).first()
        self.assertIsNotNone(coordination_catalog)
        self.assertTrue(SubjectGrade.objects.filter(catalog_per_subject=coordination_catalog, student=self.new_student, semester=1, grade=10).exists())
        self.assertTrue(SubjectGrade.objects.filter(catalog_per_subject=coordination_catalog, student=self.new_student, semester=2, grade=10).exists())
