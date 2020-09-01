from ddt import data, ddt
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from edualert.academic_calendars.factories import AcademicYearCalendarFactory
from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.statistics.factories import StudentAtRiskCountsFactory
from edualert.study_classes.factories import StudyClassFactory


@ddt
class StudentsRiskEvolutionTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        AcademicYearCalendarFactory()
        cls.admin = UserProfileFactory(user_role=UserProfile.UserRoles.ADMINISTRATOR)
        cls.school_unit = RegisteredSchoolUnitFactory()
        cls.principal = cls.school_unit.school_principal
        cls.principal.school_unit = cls.school_unit
        cls.principal.save()
        cls.teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=cls.school_unit)
        cls.today = timezone.now().date()
        cls.stats = StudentAtRiskCountsFactory(
            by_country=True,
            month=cls.today.month,
            year=cls.today.year,
        )
        cls.url = reverse('statistics:students-risk-evolution')

    def test_students_risk_evolution_absences_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.PARENT,
        UserProfile.UserRoles.STUDENT
    )
    def test_students_risk_evolution_wrong_user_type(self, user_role):
        school = RegisteredSchoolUnitFactory()
        user = UserProfileFactory(
            user_role=user_role,
            school_unit=school
        )
        self.client.login(username=user.username, password='passwd')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @data(
        13, 0, -1, 'november', '-'
    )
    def test_students_risk_evolution_invalid_month(self, month):
        self.client.login(username=self.admin.username, password='passwd')
        response = self.client.get(self.url, {'month': month})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_students_risk_evolution_admin_school_unit_validation(self):
        self.client.login(username=self.admin.username, password='passwd')
        response = self.client.get(self.url, {'school_unit': 'not a valid id'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_students_risk_evolution_admin(self):
        self.client.login(username=self.admin.username, password='passwd')
        StudentAtRiskCountsFactory(school_unit=self.school_unit, year=self.today.year, month=self.today.month)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        response = self.client.get(self.url, {'school_unit': 0})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        response = self.client.get(self.url, {'school_unit': self.school_unit.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_students_risk_evolution_principal(self):
        self.client.login(username=self.principal.username, password='passwd')
        StudentAtRiskCountsFactory(school_unit=RegisteredSchoolUnitFactory(), year=self.today.year, month=self.today.month)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        StudentAtRiskCountsFactory(school_unit=self.school_unit, year=self.today.year, month=self.today.month)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        response = self.client.get(self.url, {'school_unit': 0})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_students_risk_evolution_teacher(self):
        self.client.login(username=self.teacher.username, password='passwd')
        StudentAtRiskCountsFactory(study_class=StudyClassFactory(school_unit=self.school_unit), year=self.today.year, month=self.today.month)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        StudentAtRiskCountsFactory(study_class=StudyClassFactory(school_unit=self.school_unit, class_master=self.teacher),
                                   year=self.today.year, month=self.today.month)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_students_risk_evolution_expected_fields(self):
        self.client.login(username=self.admin.username, password='passwd')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        expected_fields = ['day', 'weekday', 'count']
        for stat in response.data:
            self.assertCountEqual(stat.keys(), expected_fields)
