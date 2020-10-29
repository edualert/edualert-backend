import datetime
from unittest.mock import patch

from ddt import data, ddt, unpack
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from pytz import utc
from rest_framework import status

from edualert.academic_calendars.factories import AcademicYearCalendarFactory
from edualert.catalogs.factories import StudentCatalogPerSubjectFactory, SubjectGradeFactory, StudentCatalogPerYearFactory
from edualert.catalogs.models import SubjectGrade, StudentCatalogPerSubject
from edualert.common.api_tests import CommonAPITestCase
from edualert.common.utils import date
from edualert.profiles.constants import FAILING_1_SUBJECT_LABEL, FAILING_2_SUBJECTS_LABEL
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile, Label
from edualert.schools.factories import RegisteredSchoolUnitFactory, SchoolUnitProfileFactory
from edualert.statistics.factories import SchoolUnitStatsFactory
from edualert.study_classes.factories import StudyClassFactory, TeacherClassThroughFactory
from edualert.subjects.factories import SubjectFactory, ProgramSubjectThroughFactory


@ddt
class GradeCreateTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_calendar = AcademicYearCalendarFactory()
        cls.school_unit = RegisteredSchoolUnitFactory()
        cls.school_stats = SchoolUnitStatsFactory(school_unit=cls.school_unit)

        cls.teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=cls.school_unit)
        cls.study_class = StudyClassFactory(school_unit=cls.school_unit)
        cls.subject = SubjectFactory()
        cls.teacher_class_through = TeacherClassThroughFactory(study_class=cls.study_class, teacher=cls.teacher, subject=cls.subject)
        ProgramSubjectThroughFactory(generic_academic_program=cls.study_class.academic_program.generic_academic_program,
                                     subject=cls.subject, weekly_hours_count=1, class_grade=cls.study_class.class_grade,
                                     class_grade_arabic=cls.study_class.class_grade_arabic)

        cls.student = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, student_in_class=cls.study_class)
        cls.catalog = StudentCatalogPerSubjectFactory(
            subject=cls.subject,
            teacher=cls.teacher,
            student=cls.student,
            study_class=cls.study_class
        )
        cls.catalog_per_year = StudentCatalogPerYearFactory(
            student=cls.student,
            study_class=cls.study_class
        )

    def setUp(self):
        self.refresh_objects_from_db([self.student, self.catalog, self.catalog_per_year])
        self.data = {
            'grade': 10,
            'grade_type': SubjectGrade.GradeTypes.REGULAR,
            'taken_at': date(2020, 3, 3)
        }

    @staticmethod
    def build_url(catalog_id):
        return reverse('catalogs:grade-create', kwargs={'id': catalog_id})

    def test_grade_create_unauthenticated(self):
        response = self.client.post(self.build_url(self.catalog.id), self.data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.PRINCIPAL,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_grade_create_wrong_user_type(self, user_role):
        user = UserProfileFactory(
            user_role=user_role,
            school_unit=self.school_unit if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )
        self.client.login(username=user.username, password='passwd')

        response = self.client.post(self.build_url(self.catalog.id), self.data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_grade_create_catalog_does_not_exist(self):
        self.client.login(username=self.teacher.username, password='passwd')
        response = self.client.post(self.build_url(0), self.data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_grade_create_teacher_not_assigned(self):
        self.client.login(username=self.teacher.username, password='passwd')
        self.catalog.teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER)
        self.catalog.save()
        response = self.client.post(self.build_url(self.catalog.id), self.data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_grade_create_is_not_enrolled(self):
        self.client.login(username=self.teacher.username, password='passwd')
        self.catalog.is_enrolled = False
        self.catalog.save()
        response = self.client.post(self.build_url(self.catalog.id), self.data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_grade_create_is_not_active(self):
        self.client.login(username=self.teacher.username, password='passwd')
        self.student.is_active = False
        self.student.save()
        response = self.client.post(self.build_url(self.catalog.id), self.data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_grade_create_is_exempted(self):
        self.client.login(username=self.teacher.username, password='passwd')
        self.catalog.is_exempted = True
        self.catalog.save()

        response = self.client.post(self.build_url(self.catalog.id), self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], "Can't add grades for an exempted student.")

    def test_grade_create_coordination_subject(self):
        self.client.login(username=self.teacher.username, password='passwd')
        self.catalog.is_coordination_subject = True
        self.catalog.save()

        response = self.client.post(self.build_url(self.catalog.id), self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'message': "Can't add grades for coordination subject."})

    @data(
        (11, {'grade': ['Grade must be between 1 and 10.']}),
        (0, {'grade': ['Grade must be between 1 and 10.']}),
        (-1, {'grade': ['Ensure this value is greater than or equal to 0.']}),
        (None, {'grade': ['This field may not be null.']}),
        ('', {'grade': ['A valid integer is required.']}),
    )
    @unpack
    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 5, 5).replace(tzinfo=utc))
    def test_grade_create_grade_validation(self, grade, expected_response, mocked_method):
        self.client.login(username=self.teacher.username, password='passwd')
        self.data['grade'] = grade
        response = self.client.post(self.build_url(self.catalog.id), self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, expected_response)

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 4, 4).replace(tzinfo=utc))
    def test_grade_create_grade_in_the_future(self, mocked_method):
        self.client.login(username=self.teacher.username, password='passwd')
        self.data['taken_at'] = date(2020, 4, 5)
        response = self.client.post(self.build_url(self.catalog.id), self.data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'taken_at': ["Can't set grade date in the future."]})

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 4, 5).replace(tzinfo=utc))
    def test_grade_create_does_not_want_thesis(self, mocked_method):
        self.client.login(username=self.teacher.username, password='passwd')
        self.data['grade_type'] = SubjectGrade.GradeTypes.THESIS
        self.catalog.wants_thesis = False
        self.catalog.save()

        response = self.client.post(self.build_url(self.catalog.id), self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'grade_type': ["You cannot add a thesis grade for this student."]})

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 4, 5).replace(tzinfo=utc))
    def test_grade_create_max_one_thesis_grade(self, mocked_method):
        self.client.login(username=self.teacher.username, password='passwd')
        self.data['grade_type'] = SubjectGrade.GradeTypes.THESIS
        self.catalog.wants_thesis = True
        self.catalog.save()

        grade = SubjectGradeFactory(
            catalog_per_subject=self.catalog,
            student=self.catalog.student,
            semester=1,
            academic_year=2020,
            grade_type=SubjectGrade.GradeTypes.THESIS
        )
        self.data['taken_at'] = date(2019, 11, 10)
        with patch(
                'django.utils.timezone.now', return_value=timezone.datetime(2019, 11, 11).replace(tzinfo=utc)
        ) as mocked_method:
            response = self.client.post(self.build_url(self.catalog.id), self.data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'grade_type': ['There can be only one thesis grade per subject per semester.']})

        grade.delete()
        grade = SubjectGradeFactory(
            catalog_per_subject=self.catalog,
            student=self.catalog.student,
            semester=2,
            academic_year=2020,
            grade_type=SubjectGrade.GradeTypes.THESIS
        )
        self.data['taken_at'] = date(2020, 4, 4)
        with patch(
                'django.utils.timezone.now', return_value=timezone.datetime(2020, 4, 5).replace(tzinfo=utc)
        ) as mocked_method:
            response = self.client.post(self.build_url(self.catalog.id), self.data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'grade_type': ['There can be only one thesis grade per subject per semester.']})

        grade.grade_type = SubjectGrade.GradeTypes.REGULAR
        grade.save()
        with patch(
                'django.utils.timezone.now', return_value=timezone.datetime(2020, 4, 5).replace(tzinfo=utc)
        ) as mocked_method:
            response = self.client.post(self.build_url(self.catalog.id), self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @data(
        (date(2019, 11, 10), 'grades_sem1'),
        (date(2020, 4, 4), 'grades_sem2'),
    )
    @unpack
    def test_grade_create_success(self, taken_at, semester):
        self.client.login(username=self.teacher.username, password='passwd')
        self.data['taken_at'] = taken_at
        taken_at_date = datetime.datetime.strptime(taken_at, settings.DATE_FORMAT)

        with patch(
                'django.utils.timezone.now',
                return_value=taken_at_date.replace(tzinfo=utc)
        ) as mocked_method:
            response = self.client.post(self.build_url(self.catalog.id), self.data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        catalog_expected_fields = [
            'id', 'student', 'avg_sem1', 'avg_sem2', 'avg_annual', 'avg_after_2nd_examination', 'avg_limit', 'abs_count_sem1', 'abs_count_sem2',
            'abs_count_annual', 'founded_abs_count_sem1', 'founded_abs_count_sem2', 'founded_abs_count_annual', 'unfounded_abs_count_sem1',
            'unfounded_abs_count_sem2', 'unfounded_abs_count_annual', 'grades_sem1', 'grades_sem2', 'abs_sem1', 'abs_sem2',
            'second_examination_grades', 'difference_grades_sem1', 'difference_grades_sem2', 'wants_thesis', 'is_exempted',
            'third_of_hours_count_sem1', 'third_of_hours_count_sem2', 'third_of_hours_count_annual', 'is_coordination_subject'
        ]
        grade_fields = ['id', 'grade', 'taken_at', 'grade_type', 'created']
        self.assertCountEqual(response.data.keys(), catalog_expected_fields)
        for grade_data in response.data['grades_sem1'] + response.data['grades_sem2']:
            self.assertCountEqual(grade_data.keys(), grade_fields)

        self.assertEqual(len(response.data[semester]), 1)
        self.assertEqual(response.data[semester][0]['grade'], 10)

        self.teacher.refresh_from_db()
        self.assertEqual(self.teacher.last_change_in_catalog, taken_at_date.replace(tzinfo=utc))
        self.assertEqual(self.teacher.school_unit.last_change_in_catalog, taken_at_date.replace(tzinfo=utc))

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2019, 11, 10).replace(tzinfo=utc))
    def test_grade_create_secondary_school_averages(self, mocked_method):
        # This is for a subject with weekly hours count = 1 and no thesis (1st semester)
        self.client.login(username=self.teacher.username, password='passwd')
        # Add a few more catalogs per subject for this student
        StudentCatalogPerSubjectFactory(student=self.student, study_class=self.study_class, avg_sem1=9)
        StudentCatalogPerSubjectFactory(student=self.student, study_class=self.study_class, is_enrolled=False)
        StudentCatalogPerSubjectFactory(student=self.student, study_class=self.study_class, is_exempted=True)
        # Add year catalog for a different student
        StudentCatalogPerYearFactory(study_class=self.study_class, avg_sem1=9)

        self.data['taken_at'] = date(2019, 11, 10)

        response = self.client.post(self.build_url(self.catalog.id), self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # because the student doesn't have enough grades, the average shouldn't be computed yet
        self.catalog.refresh_from_db()
        self.assertIsNone(self.catalog.avg_sem1)
        self.assertIsNone(self.catalog.avg_sem2)
        self.assertIsNone(self.catalog.avg_annual)
        self.assertIsNone(self.catalog.avg_final)

        # Add another grade, so we can compute the average
        self.data['grade'] = 9

        response = self.client.post(self.build_url(self.catalog.id), self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.refresh_objects_from_db([self.catalog, self.catalog_per_year, self.study_class, self.school_stats])
        self.assertEqual(self.catalog.avg_sem1, 10)
        self.assertEqual(self.catalog_per_year.avg_sem1, 9.5)
        for catalog in [self.catalog, self.catalog_per_year]:
            self.assertIsNone(catalog.avg_sem2)
            self.assertIsNone(catalog.avg_annual)
            self.assertIsNone(catalog.avg_final)
        for obj in [self.study_class, self.school_stats]:
            self.assertEqual(obj.avg_sem1, 9.25)
            self.assertIsNone(obj.avg_sem2)
            self.assertIsNone(obj.avg_annual)

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 4, 5).replace(tzinfo=utc))
    def test_grade_create_highschool_averages(self, mocked_method):
        # This is for a required subject with weekly hours count = 3 and with thesis (2nd semester)
        self.study_class.class_grade = 'IX'
        self.study_class.class_grade_arabic = 9
        self.study_class.save()
        ProgramSubjectThroughFactory(generic_academic_program=self.study_class.academic_program.generic_academic_program,
                                     subject=self.subject, weekly_hours_count=3)
        self.catalog.avg_sem1 = 10
        self.catalog.wants_thesis = True
        self.catalog.save()

        for i in range(3):
            SubjectGradeFactory(student=self.student, catalog_per_subject=self.catalog, semester=2, grade=9)

        self.client.login(username=self.teacher.username, password='passwd')
        self.data['taken_at'] = date(2020, 4, 5)
        self.data['grade_type'] = SubjectGrade.GradeTypes.THESIS

        response = self.client.post(self.build_url(self.catalog.id), self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.refresh_objects_from_db([self.catalog, self.catalog_per_year, self.study_class,
                                      self.study_class.academic_program, self.school_stats])
        for catalog in [self.catalog, self.catalog_per_year]:
            self.assertEqual(catalog.avg_sem1, 10)
            self.assertEqual(catalog.avg_sem2, 9)
            self.assertEqual(catalog.avg_annual, 9.5)
            self.assertEqual(catalog.avg_final, 9.5)
        for obj in [self.study_class, self.study_class.academic_program, self.school_stats]:
            self.assertEqual(obj.avg_sem1, 10)
            self.assertEqual(obj.avg_sem2, 9)
            self.assertEqual(obj.avg_annual, 9.5)

    @patch('django.utils.timezone.now', return_value=timezone.datetime(2020, 4, 5).replace(tzinfo=utc))
    def test_grade_create_second_examinations_count(self, timezone_mock):
        for avg in [4, 5, 6, 10]:
            StudentCatalogPerSubjectFactory(student=self.student, study_class=self.study_class, avg_sem1=avg, avg_sem2=avg)

        self.school_unit.academic_profile = SchoolUnitProfileFactory(name='Artistic')
        self.school_unit.save()
        self.study_class.class_grade = 'IX'
        self.study_class.class_grade_arabic = 9
        self.study_class.save()
        ProgramSubjectThroughFactory(generic_academic_program=self.study_class.academic_program.generic_academic_program,
                                     subject=self.subject, weekly_hours_count=1)
        self.study_class.academic_program.core_subject = self.subject
        self.study_class.academic_program.save()
        self.catalog.avg_sem1 = 5
        self.catalog.save()

        self.client.login(username=self.teacher.username, password='passwd')
        self.data['taken_at'] = date(2020, 4, 5)

        response = self.client.post(self.build_url(self.catalog.id), self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.catalog_per_year.refresh_from_db()
        self.assertEqual(self.catalog_per_year.second_examinations_count, 3)

        # Check labels
        catalog = StudentCatalogPerSubject.objects.get(student=self.student, study_class=self.study_class, avg_sem1=4, avg_sem2=4)
        catalog.avg_sem1 = 5
        catalog.save()

        response = self.client.post(self.build_url(self.catalog.id), self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.catalog_per_year.refresh_from_db()
        self.assertEqual(self.catalog_per_year.second_examinations_count, 2)
        self.assertCountEqual(self.student.labels.all(), Label.objects.filter(text=FAILING_2_SUBJECTS_LABEL))

        catalog.avg_sem2 = 5
        catalog.save()

        response = self.client.post(self.build_url(self.catalog.id), self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.catalog_per_year.refresh_from_db()
        self.assertEqual(self.catalog_per_year.second_examinations_count, 1)
        self.assertCountEqual(self.student.labels.all(), Label.objects.filter(text=FAILING_1_SUBJECT_LABEL))

        self.catalog.avg_sem1 = 6
        self.catalog.save()

        response = self.client.post(self.build_url(self.catalog.id), self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.catalog_per_year.refresh_from_db()
        self.assertEqual(self.catalog_per_year.second_examinations_count, 0)
        self.assertEqual(self.student.labels.count(), 0)
