from unittest.mock import patch

from ddt import data, ddt
from django.urls import reverse
from django.utils import timezone
from pytz import utc
from rest_framework import status

from edualert.catalogs.factories import SubjectAbsenceFactory, StudentCatalogPerSubjectFactory, SubjectGradeFactory, ExaminationGradeFactory
from edualert.catalogs.models import SubjectGrade, ExaminationGrade
from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.study_classes.factories import StudyClassFactory


@ddt
class OwnChildActivityHistoryTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.school_unit = RegisteredSchoolUnitFactory()
        cls.parent = UserProfileFactory(user_role=UserProfile.UserRoles.PARENT, school_unit=cls.school_unit)
        cls.student = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=cls.school_unit)
        cls.student.parents.add(cls.parent)
        cls.catalog = StudentCatalogPerSubjectFactory(student=cls.student)

    @staticmethod
    def build_url(child_id):
        return reverse('statistics:own-child-activity-history', kwargs={'id': child_id})

    def test_own_child_activity_history_unauthenticated(self):
        response = self.client.get(self.build_url(self.student.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.PRINCIPAL,
        UserProfile.UserRoles.TEACHER,
        UserProfile.UserRoles.STUDENT
    )
    def test_own_child_activity_history_wrong_user_type(self, user_role):
        user = UserProfileFactory(
            user_role=user_role,
            school_unit=self.school_unit if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )
        self.client.login(username=user.username, password='passwd')

        response = self.client.get(self.build_url(self.student.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_own_child_activity_history_not_own_child(self):
        self.client.login(username=self.parent.username, password='passwd')
        another_child = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=self.school_unit)
        response = self.client.get(self.build_url(another_child.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_own_child_activity_history_grades_and_absences(self):
        self.client.login(username=self.parent.username, password='passwd')
        today = timezone.now().date()
        yesterday = (timezone.now() - timezone.timedelta(days=1)).replace(tzinfo=utc)
        two_days_ago = (timezone.now() - timezone.timedelta(days=2)).date()
        three_days_ago = (timezone.now() - timezone.timedelta(days=3)).date()
        catalog = StudentCatalogPerSubjectFactory(student=self.student, is_coordination_subject=True)

        with patch('django.utils.timezone.now', return_value=yesterday) as mocked_method:
            SubjectAbsenceFactory(student=self.student, catalog_per_subject=self.catalog, is_founded=True, taken_at=yesterday.date())
            absence = SubjectAbsenceFactory(student=self.student, catalog_per_subject=self.catalog, is_founded=False, taken_at=yesterday.date())
            SubjectGradeFactory(student=self.student, catalog_per_subject=catalog, taken_at=three_days_ago)
            SubjectGradeFactory(student=self.student, catalog_per_subject=self.catalog, taken_at=two_days_ago,
                                grade_type=SubjectGrade.GradeTypes.THESIS, grade=9)

        # An absence & grade that were just taken
        SubjectAbsenceFactory(student=self.student, catalog_per_subject=self.catalog)
        SubjectGradeFactory(student=self.student, catalog_per_subject=self.catalog)

        absence.is_founded = True
        absence.save()

        response = self.client.get(self.build_url(self.student.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

        self.assertEqual(response.data[0]['date'], today.strftime('%d-%m-%Y'))
        self.assertEqual(response.data[0]['subject_name'], self.catalog.subject_name)
        self.assertEqual(response.data[0]['event_type'], 'ABSENCE_AUTHORIZATION')
        self.assertEqual(response.data[0]['event'], 'Authorized absence from {}'.format(yesterday.strftime('%d-%m')))

        self.assertEqual(response.data[1]['date'], yesterday.strftime('%d-%m-%Y'))
        self.assertEqual(response.data[1]['subject_name'], self.catalog.subject_name)
        self.assertEqual(response.data[1]['event_type'], 'NEW_AUTHORIZED_ABSENCE')
        self.assertEqual(response.data[1]['event'], 'Authorized absence')

        self.assertEqual(response.data[2]['date'], two_days_ago.strftime('%d-%m-%Y'))
        self.assertEqual(response.data[2]['subject_name'], self.catalog.subject_name)
        self.assertEqual(response.data[2]['event_type'], 'NEW_GRADE')
        self.assertEqual(response.data[2]['event'], 'Thesis grade 9')
        self.assertEqual(response.data[2]['grade_limit'], 5)
        self.assertEqual(response.data[2]['grade_value'], 9)

        self.assertEqual(response.data[3]['date'], three_days_ago.strftime('%d-%m-%Y'))
        self.assertEqual(response.data[3]['subject_name'], catalog.subject_name)
        self.assertEqual(response.data[3]['event_type'], 'NEW_GRADE')
        self.assertEqual(response.data[3]['event'], 'Grade 10')
        self.assertEqual(response.data[3]['grade_limit'], 6)
        self.assertEqual(response.data[3]['grade_value'], 10)

    def test_own_child_activity_history_exam_grades(self):
        self.client.login(username=self.parent.username, password='passwd')
        yesterday = (timezone.now() - timezone.timedelta(days=1)).replace(tzinfo=utc)
        two_days_ago = (timezone.now() - timezone.timedelta(days=2)).date()
        three_days_ago = (timezone.now() - timezone.timedelta(days=3)).date()
        four_days_ago = (timezone.now() - timezone.timedelta(days=3)).date()

        with patch('django.utils.timezone.now', return_value=yesterday) as mocked_method:
            # 2nd examinations
            ExaminationGradeFactory(student=self.student, catalog_per_subject=self.catalog, taken_at=yesterday.date())
            ExaminationGradeFactory(student=self.student, catalog_per_subject=self.catalog, taken_at=yesterday.date(),
                                    examination_type=ExaminationGrade.ExaminationTypes.ORAL)
            # difference for 1st semester
            ExaminationGradeFactory(student=self.student, catalog_per_subject=self.catalog, taken_at=three_days_ago,
                                    grade_type=ExaminationGrade.GradeTypes.DIFFERENCE, semester=1)
            ExaminationGradeFactory(student=self.student, catalog_per_subject=self.catalog, taken_at=three_days_ago,
                                    examination_type=ExaminationGrade.ExaminationTypes.ORAL,
                                    grade_type=ExaminationGrade.GradeTypes.DIFFERENCE, semester=1)
            # difference for 2nd semester
            ExaminationGradeFactory(student=self.student, catalog_per_subject=self.catalog, taken_at=two_days_ago,
                                    grade_type=ExaminationGrade.GradeTypes.DIFFERENCE, semester=2)
            ExaminationGradeFactory(student=self.student, catalog_per_subject=self.catalog, taken_at=two_days_ago,
                                    examination_type=ExaminationGrade.ExaminationTypes.ORAL,
                                    grade_type=ExaminationGrade.GradeTypes.DIFFERENCE, semester=2)
            # difference for whole year for a previous year
            study_class = StudyClassFactory(class_grade='V', class_grade_arabic=5, academic_year=2018)
            catalog2 = StudentCatalogPerSubjectFactory(student=self.student, study_class=study_class, is_coordination_subject=True)
            ExaminationGradeFactory(student=self.student, catalog_per_subject=catalog2, taken_at=four_days_ago,
                                    grade_type=ExaminationGrade.GradeTypes.DIFFERENCE, grade1=9, grade2=9)
            ExaminationGradeFactory(student=self.student, catalog_per_subject=catalog2, taken_at=four_days_ago,
                                    examination_type=ExaminationGrade.ExaminationTypes.ORAL,
                                    grade_type=ExaminationGrade.GradeTypes.DIFFERENCE)

        self.catalog.avg_after_2nd_examination = 10
        self.catalog.avg_annual = 10
        self.catalog.avg_sem1 = 10
        self.catalog.avg_sem2 = 10
        self.catalog.save()
        catalog2.avg_annual = 9.5
        catalog2.save()

        response = self.client.get(self.build_url(self.student.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

        self.assertEqual(response.data[0]['date'], yesterday.date().strftime('%d-%m-%Y'))
        self.assertEqual(response.data[0]['subject_name'], self.catalog.subject_name)
        self.assertEqual(response.data[0]['event_type'], 'SECOND_EXAMINATION_AVERAGE')
        self.assertEqual(response.data[0]['event'], 'Second examination average 10')
        self.assertEqual(response.data[0]['grade_limit'], 5)
        self.assertEqual(response.data[0]['grade_value'], 10)

        self.assertEqual(response.data[1]['date'], two_days_ago.strftime('%d-%m-%Y'))
        self.assertEqual(response.data[1]['subject_name'], self.catalog.subject_name)
        self.assertEqual(response.data[1]['event_type'], 'DIFFERENCE_AVERAGE')
        self.assertEqual(response.data[1]['event'], 'Difference average 10 for class VI, semester 2')
        self.assertEqual(response.data[1]['grade_limit'], 5)
        self.assertEqual(response.data[1]['grade_value'], 10)

        self.assertEqual(response.data[2]['date'], three_days_ago.strftime('%d-%m-%Y'))
        self.assertEqual(response.data[2]['subject_name'], self.catalog.subject_name)
        self.assertEqual(response.data[2]['event_type'], 'DIFFERENCE_AVERAGE')
        self.assertEqual(response.data[2]['event'], 'Difference average 10 for class VI, semester 1')
        self.assertEqual(response.data[2]['grade_limit'], 5)
        self.assertEqual(response.data[2]['grade_value'], 10)

        self.assertEqual(response.data[3]['date'], three_days_ago.strftime('%d-%m-%Y'))
        self.assertEqual(response.data[3]['subject_name'], catalog2.subject_name)
        self.assertEqual(response.data[3]['event_type'], 'DIFFERENCE_AVERAGE')
        self.assertEqual(response.data[3]['event'], 'Difference average 9.5 for class V')
        self.assertEqual(response.data[3]['grade_limit'], 6)
        self.assertEqual(response.data[3]['grade_value'], 9.5)
