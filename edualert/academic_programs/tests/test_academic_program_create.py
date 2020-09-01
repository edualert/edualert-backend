import datetime
from unittest.mock import patch

from ddt import data, ddt
from django.urls import reverse
from pytz import utc
from rest_framework import status

from edualert.academic_calendars.factories import AcademicYearCalendarFactory
from edualert.academic_programs.factories import GenericAcademicProgramFactory, AcademicProgramFactory
from edualert.academic_programs.models import AcademicProgram
from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory, SchoolUnitProfileFactory, SchoolUnitCategoryFactory
from edualert.schools.models import SchoolUnitCategory
from edualert.subjects.factories import SubjectFactory, ProgramSubjectThroughFactory
from edualert.subjects.models import ProgramSubjectThrough, Subject


@ddt
class AcademicProgramCreateTestCase(CommonAPITestCase):
    test_date = datetime.datetime(datetime.datetime.now().date().year, 8, 1).replace(tzinfo=utc)

    @classmethod
    def setUpTestData(cls):
        cls.principal = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL)
        cls.school_unit = RegisteredSchoolUnitFactory(school_principal=cls.principal, academic_profile=SchoolUnitProfileFactory(name='Sportiv'))
        cls.generic_academic_program = GenericAcademicProgramFactory(
            optional_subjects_weekly_hours={
                "IX": 10,
                "X": 1
            },
            academic_profile=cls.school_unit.academic_profile
        )
        cls.school_unit.categories.add(cls.generic_academic_program.category)
        cls.subject = SubjectFactory(name='Subject')
        cls.mandatory_subject = SubjectFactory(name='Mandatory')
        cls.mandatory_through = ProgramSubjectThroughFactory(
            generic_academic_program=cls.generic_academic_program, subject=cls.mandatory_subject,
            class_grade='IX', class_grade_arabic=9
        )
        cls.academic_year = 2020
        cls.academic_year_calendar = AcademicYearCalendarFactory(academic_year=cls.academic_year)

    def setUp(self):
        self.refresh_objects_from_db([self.school_unit, self.generic_academic_program])
        self.data = {
            "generic_academic_program": self.generic_academic_program.id,
            "core_subject": self.mandatory_subject.id,
            "optional_subjects": [
                {
                    "class_grade": "IX",
                    "subject": self.subject.name,
                    "weekly_hours_count": 10
                },
                {
                    "class_grade": "X",
                    "subject": self.subject.name,
                    "weekly_hours_count": 1
                }
            ]
        }

    @staticmethod
    def build_url(academic_year):
        return reverse('academic_programs:academic-program-list', kwargs={'academic_year': academic_year})

    def test_academic_program_create_unauthenticated(self):
        response = self.client.post(self.build_url(self.academic_year), self.data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR, UserProfile.UserRoles.TEACHER,
        UserProfile.UserRoles.PARENT, UserProfile.UserRoles.STUDENT
    )
    def test_academic_program_create_wrong_user_type(self, user_role):
        user = UserProfileFactory(
            user_role=user_role,
            school_unit=self.school_unit if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )

        self.client.login(username=user.user.username, password='passwd')
        response = self.client.post(self.build_url(self.academic_year), self.data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('django.utils.timezone.now', return_value=test_date)
    def test_academic_program_create_wrong_year(self, mocked_method):
        self.client.login(username=self.principal.username, password='passwd')
        response = self.client.post(self.build_url(0), self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'message': 'Invalid year, must be the current academic year.'})

        AcademicYearCalendarFactory(academic_year=self.academic_year + 1)
        response = self.client.post(self.build_url(self.academic_year), self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'message': 'Invalid year, must be the current academic year.'})

    # @patch('django.utils.timezone.now', return_value=datetime.datetime(datetime.datetime.now().date().year, 9, 16).replace(tzinfo=utc))
    # def test_academic_program_create_wrong_creation_date(self, mocked_method):
    #     self.client.login(username=self.principal.username, password='passwd')
    #     response = self.client.post(self.build_url(self.academic_year), self.data)
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertEqual(response.data, {'message': 'Academic programs must be created before 15th of september of the current year.'})

    @patch('django.utils.timezone.now', return_value=test_date)
    def test_academic_program_create_existing_program(self, mocked_method):
        self.client.login(username=self.principal.username, password='passwd')

        AcademicProgramFactory(generic_academic_program=self.generic_academic_program,
                               school_unit=self.school_unit, academic_year=self.academic_year)

        response = self.client.post(self.build_url(self.academic_year), self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'generic_academic_program': ['You already defined this program this year.']})

    @patch('django.utils.timezone.now', return_value=test_date)
    def test_academic_program_create_invalid_academic_profile(self, mocked_method):
        self.client.login(username=self.principal.username, password='passwd')

        self.generic_academic_program.academic_profile = SchoolUnitProfileFactory()
        self.generic_academic_program.save()

        response = self.client.post(self.build_url(self.academic_year), self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'generic_academic_program': ['Invalid generic academic program.']})

    @patch('django.utils.timezone.now', return_value=test_date)
    def test_academic_program_create_invalid_category(self, mocked_method):
        self.client.login(username=self.principal.username, password='passwd')
        self.generic_academic_program.category = SchoolUnitCategoryFactory()
        self.generic_academic_program.save()

        response = self.client.post(self.build_url(self.academic_year), self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'generic_academic_program': ['Invalid generic academic program.']})

    @patch('django.utils.timezone.now', return_value=test_date)
    def test_academic_program_create_invalid_core_subject(self, mocked_method):
        self.client.login(username=self.principal.username, password='passwd')

        del self.data['core_subject']

        response = self.client.post(self.build_url(self.academic_year), self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'core_subject': ['This academic program must have a core subject.']})

        self.data['core_subject'] = 0

        response = self.client.post(self.build_url(self.academic_year), self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'core_subject': ['Invalid pk "0" - object does not exist.']})

        self.data['core_subject'] = SubjectFactory().id

        response = self.client.post(self.build_url(self.academic_year), self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'core_subject': ['Invalid core subject.']})

        self.generic_academic_program.academic_profile = None
        self.generic_academic_program.save()
        self.school_unit.academic_profile = None
        self.school_unit.save()
        self.data['core_subject'] = self.mandatory_subject.id

        response = self.client.post(self.build_url(self.academic_year), self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'core_subject': ['This academic program does not have a core subject.']})

    @patch('django.utils.timezone.now', return_value=test_date)
    def test_academic_program_create_weekly_hours_count_validation(self, mocked_method):
        self.client.login(username=self.principal.username, password='passwd')

        self.data['optional_subjects'] = [
            {
                "class_grade": "IX",
                "subject": self.subject.name,
                "weekly_hours_count": 0
            }
        ]

        response = self.client.post(self.build_url(self.academic_year), self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['optional_subjects'][0]['weekly_hours_count'],
                         ['The number of hours must be greater than 0.'])

        self.data['optional_subjects'] = [
            {
                "class_grade": "V",
                "subject": self.subject.name,
                "weekly_hours_count": 1
            },
            {
                "class_grade": "IX",
                "subject": self.subject.name,
                "weekly_hours_count": 11
            },
            {
                "class_grade": "X",
                "subject": "Another subject",
                "weekly_hours_count": 2
            }
        ]

        response = self.client.post(self.build_url(self.academic_year), self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['optional_subjects'], {
            'V': "This program does not accept optionals for this class grade.",
            'IX': "Each optional's weekly hours should not be greater than 10.",
            'X': "Each optional's weekly hours should not be greater than 1.",
        })

    @patch('django.utils.timezone.now', return_value=test_date)
    def test_academic_program_create_invalid_subject_name(self, mocked_method):
        self.client.login(username=self.principal.username, password='passwd')
        self.data['optional_subjects'] = [
            {
                "class_grade": "IX",
                "subject": self.subject.name,
                "weekly_hours_count": 10
            },
            {
                "class_grade": "X",
                "subject": "x" * 101,
                "weekly_hours_count": 1
            }
        ]

        response = self.client.post(self.build_url(self.academic_year), self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['optional_subjects'][1]['subject'], ['Ensure this field has no more than 100 characters.'])

    @patch('django.utils.timezone.now', return_value=test_date)
    def test_academic_program_create_unique_subjects(self, mocked_method):
        self.client.login(username=self.principal.username, password='passwd')
        self.data['optional_subjects'].append({
            "class_grade": "IX",
            "subject": self.subject.name,
            "weekly_hours_count": 10
        })
        response = self.client.post(self.build_url(self.academic_year), self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['optional_subjects'], {'IX': 'Subjects must be unique per class grade.'})

    @patch('django.utils.timezone.now', return_value=test_date)
    def test_academic_program_create_invalid_class_grade(self, mocked_method):
        self.client.login(username=self.principal.username, password='passwd')
        self.data['optional_subjects'] = [{
            "class_grade": "k",
            "subject": self.subject.name,
            "weekly_hours_count": 10
        }]
        response = self.client.post(self.build_url(self.academic_year), self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'optional_subjects': [{'class_grade': ['Invalid class grade.']}]})

    @patch('django.utils.timezone.now', return_value=test_date)
    def test_academic_program_detail_expected_fields(self, mocked_method):
        self.client.login(username=self.principal.username, password='passwd')

        expected_fields = ['id', 'name', 'classes_count', 'academic_year', 'core_subject', 'optional_subjects_weekly_hours', 'subjects']
        subjects_expected_fields = ['mandatory_subjects', 'optional_subjects']
        subject_expected_fields = ['subject_id', 'subject_name', 'id', 'weekly_hours_count']

        response = self.client.post(self.build_url(self.academic_year), self.data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertCountEqual(response.data.keys(), expected_fields)
        self.assertEqual(len(response.data['subjects']), 2)
        self.assertCountEqual(response.data['subjects']['IX'].keys(), subjects_expected_fields)
        for subject in response.data['subjects']['IX']['optional_subjects']:
            self.assertCountEqual(subject.keys(), subject_expected_fields)
        for subject in response.data['subjects']['IX']['mandatory_subjects']:
            self.assertCountEqual(subject.keys(), subject_expected_fields)

    @patch('django.utils.timezone.now', return_value=test_date)
    def test_academic_program_create_success(self, mocked_method):
        self.client.login(username=self.principal.username, password='passwd')

        self.data['optional_subjects'] = [
            {
                "class_grade": "IX",
                "subject": self.subject.name,
                "weekly_hours_count": 3
            },
            {
                "class_grade": "IX",
                "subject": "Another subject",
                "weekly_hours_count": 8
            },
            {
                "class_grade": "X",
                "subject": self.subject.name,
                "weekly_hours_count": 1
            }
        ]

        response = self.client.post(self.build_url(self.academic_year), self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        academic_program = AcademicProgram.objects.get(id=response.data['id'])
        self.assertEqual(academic_program.name, self.generic_academic_program.name)
        self.assertEqual(academic_program.school_unit, self.school_unit)
        self.assertEqual(academic_program.academic_year, self.academic_year)
        self.assertEqual(academic_program.core_subject, self.mandatory_subject)
        self.assertEqual(ProgramSubjectThrough.objects.filter(academic_program=academic_program).count(), 3)

        self.assertCountEqual(response.data['subjects'].keys(), ['IX', 'X'])
        self.assertEqual(len(response.data['subjects']['IX']['mandatory_subjects']), 1)
        self.assertEqual(len(response.data['subjects']['IX']['optional_subjects']), 2)
        self.assertEqual(len(response.data['subjects']['X']['mandatory_subjects']), 0)
        self.assertEqual(len(response.data['subjects']['X']['optional_subjects']), 1)

        optional_through1 = ProgramSubjectThrough.objects.get(id=response.data['subjects']['IX']['optional_subjects'][0]['id'])
        self.assertEqual(optional_through1.class_grade, 'IX')
        self.assertEqual(optional_through1.class_grade_arabic, 9)
        self.assertFalse(optional_through1.is_mandatory)
        subject = Subject.objects.get(name='Another subject')
        self.assertEqual(optional_through1.subject, subject)
        self.assertFalse(subject.should_be_in_taught_subjects)

        optional_through2 = ProgramSubjectThrough.objects.get(id=response.data['subjects']['IX']['optional_subjects'][1]['id'])
        self.assertEqual(optional_through2.class_grade, 'IX')
        self.assertEqual(optional_through2.class_grade_arabic, 9)
        self.assertFalse(optional_through2.is_mandatory)
        self.assertEqual(optional_through2.subject, self.subject)

        optional_through3 = ProgramSubjectThrough.objects.get(id=response.data['subjects']['X']['optional_subjects'][0]['id'])
        self.assertEqual(optional_through3.class_grade, 'X')
        self.assertEqual(optional_through3.class_grade_arabic, 10)
        self.assertFalse(optional_through3.is_mandatory)
        self.assertEqual(optional_through3.subject, self.subject)

    @patch('django.utils.timezone.now', return_value=test_date)
    def test_academic_program_create_secondary_school_success(self, mocked_method):
        self.client.login(username=self.principal.username, password='passwd')
        category = SchoolUnitCategoryFactory(category_level=SchoolUnitCategory.CategoryLevels.SECONDARY_SCHOOL)
        generic_academic_program = GenericAcademicProgramFactory(
            category=category,
            optional_subjects_weekly_hours={
                "VI": 1,
                "VII": 1
            }
        )
        self.school_unit.categories.add(category)
        self.school_unit.academic_profile = None
        self.school_unit.save()

        self.data = {
            "generic_academic_program": generic_academic_program.id,
            "optional_subjects": [
                {
                    "class_grade": "VI",
                    "subject": self.subject.name,
                    "weekly_hours_count": 1
                },
                {
                    "class_grade": "VII",
                    "subject": self.subject.name,
                    "weekly_hours_count": 1
                }
            ]
        }

        response = self.client.post(self.build_url(self.academic_year), self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        academic_program = AcademicProgram.objects.get(id=response.data['id'])
        self.assertEqual(academic_program.name, generic_academic_program.name)
        self.assertEqual(academic_program.school_unit, self.school_unit)
        self.assertEqual(academic_program.academic_year, self.academic_year)
        self.assertEqual(ProgramSubjectThrough.objects.filter(academic_program=academic_program).count(), 2)

        self.assertCountEqual(response.data['subjects'].keys(), ['VI', 'VII'])
        self.assertEqual(len(response.data['subjects']['VI']['mandatory_subjects']), 0)
        self.assertEqual(len(response.data['subjects']['VI']['optional_subjects']), 1)
        self.assertEqual(len(response.data['subjects']['VII']['mandatory_subjects']), 0)
        self.assertEqual(len(response.data['subjects']['VII']['optional_subjects']), 1)
