import datetime
from copy import copy
from unittest.mock import patch

from dateutil import tz
from ddt import data, ddt, unpack
from django.urls import reverse
from rest_framework import status

from edualert.academic_calendars.factories import AcademicYearCalendarFactory
from edualert.academic_programs.factories import AcademicProgramFactory
from edualert.catalogs.models import StudentCatalogPerYear, StudentCatalogPerSubject, SubjectGrade
from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory, SchoolUnitCategoryFactory
from edualert.schools.models import SchoolUnitCategory
from edualert.statistics.models import StudentAtRiskCounts
from edualert.study_classes.factories import StudyClassFactory
from edualert.study_classes.models import StudyClass, TeacherClassThrough
from edualert.subjects.factories import SubjectFactory, ProgramSubjectThroughFactory


@ddt
class StudyClassCreateTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.principal = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL)
        cls.school_unit = RegisteredSchoolUnitFactory(school_principal=cls.principal)

        cls.category1 = SchoolUnitCategoryFactory(category_level=SchoolUnitCategory.CategoryLevels.PRIMARY_SCHOOL)
        cls.category2 = SchoolUnitCategoryFactory(category_level=SchoolUnitCategory.CategoryLevels.SECONDARY_SCHOOL)
        cls.category3 = SchoolUnitCategoryFactory(category_level=SchoolUnitCategory.CategoryLevels.HIGHSCHOOL)
        cls.school_unit.categories.add(cls.category1, cls.category2, cls.category3)

        cls.calendar = AcademicYearCalendarFactory()

        cls.subject1 = SubjectFactory()
        cls.subject2 = SubjectFactory()
        cls.coordination_subject = SubjectFactory(is_coordination=True)
        cls.academic_program = AcademicProgramFactory(school_unit=cls.school_unit)
        for class_grade, class_grade_arabic in zip(['I', 'VI', 'IX'], [1, 6, 9]):
            ProgramSubjectThroughFactory(academic_program=cls.academic_program, subject=cls.subject1, is_mandatory=False,
                                         class_grade=class_grade, class_grade_arabic=class_grade_arabic)
            ProgramSubjectThroughFactory(generic_academic_program=cls.academic_program.generic_academic_program, subject=cls.subject2,
                                         class_grade=class_grade, class_grade_arabic=class_grade_arabic)

        cls.teacher1 = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=cls.school_unit)
        cls.teacher2 = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=cls.school_unit)
        cls.teacher1.taught_subjects.add(cls.subject1)
        cls.teacher2.taught_subjects.add(cls.subject2)

        cls.student1 = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=cls.school_unit)
        cls.student2 = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=cls.school_unit)

        cls.url = reverse('study_classes:study-class-list', kwargs={'academic_year': cls.calendar.academic_year})

        cls.class_master = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=cls.school_unit)
        cls.primary_school_request_data = {
            'class_grade': 'I',
            'class_letter': 'A',
            'academic_program': cls.academic_program.id,
            "class_master": cls.class_master.id,
            "teachers_class_through": [
                {
                    "teacher": cls.teacher1.id,
                    "subject": cls.subject1.id
                },
                {
                    "teacher": cls.teacher2.id,
                    "subject": cls.subject2.id
                }
            ],
            "students": [
                cls.student1.id,
                cls.student2.id
            ]
        }
        cls.secondary_school_request_data = {
            'class_grade': 'VI',
            'class_letter': 'A1',
            'academic_program': cls.academic_program.id,
            "class_master": cls.class_master.id,
            "teachers_class_through": [
                {
                    "teacher": cls.teacher1.id,
                    "subject": cls.subject1.id
                },
                {
                    "teacher": cls.teacher2.id,
                    "subject": cls.subject2.id
                }
            ],
            "students": [
                cls.student1.id,
                cls.student2.id
            ]
        }

    def setUp(self):
        self.highschool_request_data = {
            'class_grade': 'IX',
            'class_letter': 'A',
            'academic_program': self.academic_program.id,
            "class_master": self.class_master.id,
            "teachers_class_through": [
                {
                    "teacher": self.teacher1.id,
                    "subject": self.subject1.id
                },
                {
                    "teacher": self.teacher2.id,
                    "subject": self.subject2.id
                }
            ],
            "students": [
                self.student1.id,
                self.student2.id
            ]
        }

    def test_study_class_create_unauthenticated(self):
        response = self.client.post(self.url, self.highschool_request_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.TEACHER,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_study_class_create_wrong_user_type(self, user_role):
        user = UserProfileFactory(
            user_role=user_role,
            school_unit=RegisteredSchoolUnitFactory() if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )
        self.client.login(username=user.username, password='passwd')

        response = self.client.post(self.url, self.highschool_request_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_study_class_create_no_calendar(self):
        self.client.login(username=self.principal.username, password='passwd')
        self.calendar.delete()

        response = self.client.post(self.url, self.highschool_request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], 'No academic calendar defined.')

    def test_study_class_create_different_year(self):
        self.client.login(username=self.principal.username, password='passwd')
        url = reverse('study_classes:study-class-list', kwargs={'academic_year': self.calendar.academic_year - 1})

        response = self.client.post(url, self.highschool_request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], 'A new study class can be added only for the current academic year.')

    # @patch('django.utils.timezone.now')
    # def test_study_class_create_wrong_date(self, timezone_mock):
    #     timezone_mock.return_value = datetime.datetime(self.calendar.academic_year, 9, 16, tzinfo=tz.UTC)
    #     self.client.login(username=self.principal.username, password='passwd')
    #
    #     response = self.client.post(self.url, self.highschool_request_data)
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertEqual(response.data['message'], 'Cannot create a study class anymore.')

    @patch('django.utils.timezone.now')
    def test_study_class_create_missing_fields(self, timezone_mock):
        timezone_mock.return_value = datetime.datetime(self.calendar.academic_year, 9, 14, tzinfo=tz.UTC)
        self.client.login(username=self.principal.username, password='passwd')

        required_fields = ['class_grade', 'class_letter', 'academic_program', 'class_master',
                           'teachers_class_through', 'students']

        request_data = copy(self.highschool_request_data)

        for field in required_fields:
            del request_data[field]
            response = self.client.post(self.url, request_data)

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data, {field: ['This field is required.']})

            request_data = copy(self.highschool_request_data)

    @data(
        'P', 'IV', 'XX'
    )
    @patch('django.utils.timezone.now')
    def test_study_class_create_validate_class_grade(self, class_grade, timezone_mock):
        timezone_mock.return_value = datetime.datetime(self.calendar.academic_year, 9, 14, tzinfo=tz.UTC)
        self.client.login(username=self.principal.username, password='passwd')

        self.school_unit.categories.remove(self.category1)
        self.highschool_request_data['class_grade'] = class_grade

        response = self.client.post(self.url, self.highschool_request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['class_grade'], ['Invalid class grade.'])

    @data(
        'Aa', 'ABa', '1a'
    )
    @patch('django.utils.timezone.now')
    def test_study_class_create_validate_class_letter(self, class_letter, timezone_mock):
        timezone_mock.return_value = datetime.datetime(self.calendar.academic_year, 9, 14, tzinfo=tz.UTC)
        self.client.login(username=self.principal.username, password='passwd')

        self.school_unit.categories.remove(self.category1)
        self.highschool_request_data['class_letter'] = class_letter

        response = self.client.post(self.url, self.highschool_request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['class_letter'], ['This value can contain only uppercase letters and digits.'])

    @patch('django.utils.timezone.now')
    def test_study_class_create_validate_class_already_exists(self, timezone_mock):
        timezone_mock.return_value = datetime.datetime(self.calendar.academic_year, 9, 14, tzinfo=tz.UTC)
        self.client.login(username=self.principal.username, password='passwd')

        StudyClassFactory(school_unit=self.school_unit, class_grade='IX', class_grade_arabic=9)

        response = self.client.post(self.url, self.highschool_request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['general_errors'], ['This study class already exists.'])

    @patch('django.utils.timezone.now')
    def test_study_class_create_validate_class_master(self, timezone_mock):
        timezone_mock.return_value = datetime.datetime(self.calendar.academic_year, 9, 14, tzinfo=tz.UTC)
        self.client.login(username=self.principal.username, password='passwd')

        # Not a teacher
        profile1 = UserProfileFactory(user_role=UserProfile.UserRoles.PARENT, school_unit=self.school_unit)
        # From a different school
        profile2 = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=RegisteredSchoolUnitFactory())
        # Already a class master
        profile3 = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=self.school_unit)
        StudyClassFactory(school_unit=self.school_unit, class_master=profile3)
        # Inactive teacher
        profile4 = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=self.school_unit, is_active=False)

        for profile in [profile1, profile2, profile3, profile4]:
            self.highschool_request_data['class_master'] = profile.id

            response = self.client.post(self.url, self.highschool_request_data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data['class_master'], ['Invalid user.'])

        self.highschool_request_data['class_master'] = 0

        response = self.client.post(self.url, self.highschool_request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['class_master'], ['Invalid pk "0" - object does not exist.'])

    @patch('django.utils.timezone.now')
    def test_study_class_create_validate_academic_program(self, timezone_mock):
        timezone_mock.return_value = datetime.datetime(self.calendar.academic_year, 9, 14, tzinfo=tz.UTC)
        self.client.login(username=self.principal.username, password='passwd')

        program1 = AcademicProgramFactory(school_unit=self.school_unit, academic_year=2010)
        program2 = AcademicProgramFactory(school_unit=RegisteredSchoolUnitFactory())

        for program in [program1, program2]:
            self.highschool_request_data['academic_program'] = program.id

            response = self.client.post(self.url, self.highschool_request_data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data['academic_program'], ['Invalid academic program.'])

    @patch('django.utils.timezone.now')
    def test_study_class_create_validate_subjects(self, timezone_mock):
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

            response = self.client.post(self.url, self.highschool_request_data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data['teachers_class_through'], ['The subjects do not correspond with the academic program subjects.'])

    @patch('django.utils.timezone.now')
    def test_study_class_create_validate_teachers(self, timezone_mock):
        timezone_mock.return_value = datetime.datetime(self.calendar.academic_year, 9, 14, tzinfo=tz.UTC)
        self.client.login(username=self.principal.username, password='passwd')

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

            response = self.client.post(self.url, self.highschool_request_data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data['teachers_class_through'], ['At least one teacher is invalid.'])

        # Subject not in teacher's taught subjects
        self.highschool_request_data['teachers_class_through'] = [
            {
                "teacher": self.teacher1.id,
                "subject": self.subject1.id
            },
            {
                "teacher": self.teacher1.id,
                "subject": self.subject2.id
            }
        ]

        response = self.client.post(self.url, self.highschool_request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['teachers_class_through'], ['Teacher {} does not teach {}.'
                         .format(self.teacher1.full_name, self.subject2.name)])

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

        response = self.client.post(self.url, self.highschool_request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['teachers_class_through'][0]['teacher'], ['Invalid pk "0" - object does not exist.'])

    @patch('django.utils.timezone.now')
    def test_study_class_create_validate_students(self, timezone_mock):
        timezone_mock.return_value = datetime.datetime(self.calendar.academic_year, 9, 14, tzinfo=tz.UTC)
        self.client.login(username=self.principal.username, password='passwd')

        # Not a student
        profile1 = UserProfileFactory(user_role=UserProfile.UserRoles.PARENT, school_unit=self.school_unit)
        # Already in a study class
        study_class = StudyClassFactory(school_unit=self.school_unit)
        profile2 = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=self.school_unit, student_in_class=study_class)
        # Inactive student
        profile3 = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=self.school_unit, is_active=False)

        for profile_id in [profile1.id, profile2.id, profile3.id, 0]:
            self.highschool_request_data['students'] = [profile_id, ]

            response = self.client.post(self.url, self.highschool_request_data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data['students'], [f'Invalid pk "{profile_id}" - object does not exist.'])

        # From a different school
        profile = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=RegisteredSchoolUnitFactory())
        self.highschool_request_data['students'] = [profile.id, ]

        response = self.client.post(self.url, self.highschool_request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['students'], ['At least one student is invalid.'])

    @data(
        ('highschool_request_data', 9, SchoolUnitCategory.CategoryLevels.HIGHSCHOOL),
        ('secondary_school_request_data', 6, SchoolUnitCategory.CategoryLevels.SECONDARY_SCHOOL),
        ('primary_school_request_data', 1, SchoolUnitCategory.CategoryLevels.PRIMARY_SCHOOL)
    )
    @unpack
    @patch('django.utils.timezone.now')
    def test_study_class_create_success(self, request_data_param, class_grade_arabic, category_level, timezone_mock):
        timezone_mock.return_value = datetime.datetime(self.calendar.academic_year, 9, 14, tzinfo=tz.UTC)
        request_data = getattr(self, request_data_param)
        self.client.login(username=self.principal.username, password='passwd')

        self.academic_program.refresh_from_db()
        self.assertEqual(self.academic_program.classes_count, 0)
        self.academic_program.generic_academic_program.category.category_level = category_level
        self.academic_program.generic_academic_program.category.save()

        expected_fields = ['id', 'class_grade', 'class_letter', 'academic_year', 'academic_program', 'academic_program_name',
                           'class_master', 'teachers_class_through', 'students', 'has_previous_catalog_data']

        response = self.client.post(self.url, request_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertCountEqual(response.data.keys(), expected_fields)
        self.assertEqual(list(response.data['class_master']), ['id', 'full_name'])
        self.assertEqual(list(response.data['teachers_class_through'][0]), ['id', 'teacher', 'subject_id', 'subject_name'])
        self.assertEqual(list(response.data['students'][0]), ['id', 'full_name'])

        study_class = StudyClass.objects.get(id=response.data['id'])
        self.assertEqual(study_class.school_unit_id, self.school_unit.id)
        self.assertEqual(study_class.academic_year, self.calendar.academic_year)
        self.assertEqual(study_class.class_grade_arabic, class_grade_arabic)
        self.assertEqual(study_class.academic_program_name, self.academic_program.name)
        self.academic_program.refresh_from_db()
        self.assertEqual(self.academic_program.classes_count, 1)
        self.assertTrue(StudentAtRiskCounts.objects.filter(study_class=study_class).exists())

        is_optional_values = [True, False] if request_data.get('academic_program') is not None else [False, False]
        for (teacher, subject, is_optional) in zip([self.teacher1, self.teacher2], [self.subject1, self.subject2], is_optional_values):
            self.assertTrue(TeacherClassThrough.objects.filter(study_class=study_class, teacher=teacher, subject=subject, is_class_master=False,
                                                               is_optional_subject=is_optional, is_coordination_subject=False).exists())

        self.assertTrue(TeacherClassThrough.objects.filter(study_class=study_class, teacher=self.class_master, subject=self.coordination_subject,
                                                           is_class_master=True, is_optional_subject=False, is_coordination_subject=True).exists())

        is_enrolled_values = [False, True] if request_data.get('academic_program') is not None else [True, True]
        for student in [self.student1, self.student2]:
            student.refresh_from_db()
            self.assertEqual(student.student_in_class_id, study_class.id)
            catalog_per_year = StudentCatalogPerYear.objects.filter(student=student, study_class=study_class).first()
            self.assertIsNotNone(catalog_per_year)
            self.assertEqual(catalog_per_year.behavior_grade_sem1, 10)
            self.assertEqual(catalog_per_year.behavior_grade_sem2, 10)
            self.assertEqual(catalog_per_year.behavior_grade_annual, 10)

            for (teacher, subject, is_enrolled) in zip([self.teacher1, self.teacher2], [self.subject1, self.subject2], is_enrolled_values):
                self.assertTrue(StudentCatalogPerSubject.objects.filter(student=student, teacher=teacher,
                                                                        subject=subject, is_enrolled=is_enrolled).exists())

            coordination_catalog = StudentCatalogPerSubject.objects.filter(student=student, teacher=self.class_master,
                                                                           subject=self.coordination_subject, is_enrolled=True).first()
            self.assertIsNotNone(coordination_catalog)
            self.assertEqual(coordination_catalog.avg_sem1, 10)
            self.assertEqual(coordination_catalog.avg_sem2, 10)
            self.assertEqual(coordination_catalog.avg_annual, 10)
            self.assertTrue(SubjectGrade.objects.filter(catalog_per_subject=coordination_catalog, student=student, semester=1, grade=10).exists())
            self.assertTrue(SubjectGrade.objects.filter(catalog_per_subject=coordination_catalog, student=student, semester=2, grade=10).exists())
