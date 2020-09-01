import csv
import datetime
import io

from ddt import data, ddt
from django.urls import reverse
from rest_framework import status

from edualert.academic_calendars.factories import AcademicYearCalendarFactory
from edualert.catalogs.factories import StudentCatalogPerSubjectFactory, SubjectGradeFactory, SubjectAbsenceFactory, ExaminationGradeFactory
from edualert.catalogs.models import SubjectGrade, ExaminationGrade
from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory, LabelFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.study_classes.factories import StudyClassFactory, TeacherClassThroughFactory
from edualert.subjects.factories import SubjectFactory


@ddt
class CatalogExportTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.school = RegisteredSchoolUnitFactory()
        cls.teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=cls.school)
        cls.study_class = StudyClassFactory(school_unit=cls.school)
        cls.subject = SubjectFactory()
        cls.teacher_class_through = TeacherClassThroughFactory(study_class=cls.study_class, teacher=cls.teacher, subject=cls.subject)
        cls.catalog = StudentCatalogPerSubjectFactory(study_class=cls.study_class, teacher=cls.teacher, subject=cls.subject, student__full_name='a')
        cls.current_calendar = AcademicYearCalendarFactory()

    def setUp(self):
        self.study_class.refresh_from_db()
        self.teacher_class_through.refresh_from_db()

    @staticmethod
    def build_url(study_class_id, subject_id):
        return reverse('catalogs:export-subject-catalogs', kwargs={'study_class_id': study_class_id, 'subject_id': subject_id})

    @staticmethod
    def get_csv_rows_from_response(response):
        buffer = io.StringIO()
        buffer.write(response.content.decode('utf-8'))
        buffer.seek(0)

        return csv.DictReader(buffer)

    def test_catalog_export_unauthenticated(self):
        response = self.client.get(self.build_url(self.study_class.id, self.subject.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.PRINCIPAL,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_catalog_export_wrong_user_type(self, user_role):
        user = UserProfileFactory(
            user_role=user_role,
            school_unit=self.school if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )
        self.client.login(username=user.username, password='passwd')

        response = self.client.get(self.build_url(self.study_class.id, self.subject.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_catalog_export_does_not_teach_class(self):
        self.client.login(username=self.teacher.username, password='passwd')
        self.teacher_class_through.study_class = StudyClassFactory()
        self.teacher_class_through.save()

        response = self.client.get(self.build_url(self.study_class.id, self.subject.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_catalog_export_subject_not_taught_in_study_class(self):
        self.client.login(username=self.teacher.username, password='passwd')

        response = self.client.get(self.build_url(self.study_class.id, SubjectFactory().id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_catalog_export_does_not_teach_subject(self):
        self.client.login(username=self.teacher.username, password='passwd')
        self.teacher_class_through.subject = SubjectFactory()
        self.teacher_class_through.save()
        response = self.client.get(self.build_url(self.study_class.id, self.subject.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_catalog_export_subject_file_download(self):
        self.client.login(username=self.teacher.username, password='passwd')

        response = self.client.get(self.build_url(self.study_class.id, self.subject.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.get('Content-Disposition').startswith('attachment; filename="raport_'))
        self.assertTrue(response.get('Content-Disposition').endswith('.csv"'))

    def test_catalog_export_success(self):
        self.client.login(username=self.teacher.username, password='passwd')
        expected_fields = [
            'Nume', 'Clasă', 'Etichete', 'Note sem. I', 'Teză sem. I', 'Medie sem. I', 'Note sem. II', 'Teză sem. II',
            'Medie sem. II', 'Medie anuală', 'Absențe motivate sem. I', 'Absențe nemotivate sem. I', 'Absențe motivate sem. II',
            'Absențe nemotivate sem. II', 'Observații', 'Teste inițiale / finale', 'Teză', 'Simulări', 'Scutit', 'Înregistrat opțional',
            'Corigență Oral Prof. I', 'Corigență Oral Prof. II', 'Corigență Scris Prof. II', 'Corigență Scris Prof. I',
            'Diferență sem. I Oral Prof. I', 'Diferență sem. I Oral Prof. II', 'Diferență sem. I Scris Prof. I', 'Diferență sem. I Scris Prof. II',
            'Diferență sem. II Oral Prof. I', 'Diferență sem. II Oral Prof. II', 'Diferență sem. II Scris Prof. I', 'Diferență sem. II Scris Prof. II',
            'Diferență anuală Oral Prof. I', 'Diferență anuală Oral Prof. II', 'Diferență anuală Scris Prof. I', 'Diferență anuală Scris Prof. II'
        ]
        boolean_fields = ['Teste inițiale / finale', 'Teză', 'Simulări', 'Scutit', 'Înregistrat opțional']

        response = self.client.get(self.build_url(self.study_class.id, self.subject.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        row_nr = 0
        for index, row in enumerate(self.get_csv_rows_from_response(response)):
            self.assertCountEqual(row.keys(), expected_fields)
            for key, value in row.items():
                self.assertNotEqual(value, '')
                if key not in ['Nume', 'Clasă', 'Etichete', *boolean_fields]:
                    self.assertEqual(value, '-')

            row_nr += 1

        self.assertEqual(row_nr, 1)

        catalog = StudentCatalogPerSubjectFactory(
            study_class=self.study_class,
            teacher=self.teacher,
            subject=self.subject,
            student__full_name='b',
            remarks='very good',
            avg_sem1=2,
            avg_sem2=2,
            avg_final=2,
            abs_count_sem1=2,
            abs_count_sem2=2,
            abs_count_annual=2,
        )

        catalog.student.labels.add(LabelFactory(user_role=UserProfile.UserRoles.STUDENT))

        SubjectGradeFactory(student=catalog.student, catalog_per_subject=catalog, semester=1, grade=10, grade_type=SubjectGrade.GradeTypes.REGULAR)
        SubjectGradeFactory(student=catalog.student, catalog_per_subject=catalog, semester=1, grade=9, grade_type=SubjectGrade.GradeTypes.REGULAR)
        SubjectGradeFactory(student=catalog.student, catalog_per_subject=catalog, semester=2, grade=10, grade_type=SubjectGrade.GradeTypes.REGULAR)
        SubjectGradeFactory(student=catalog.student, catalog_per_subject=catalog, semester=2, grade=9, grade_type=SubjectGrade.GradeTypes.REGULAR)

        SubjectGradeFactory(student=catalog.student, catalog_per_subject=catalog, semester=1, grade=10, grade_type=SubjectGrade.GradeTypes.THESIS)
        SubjectGradeFactory(student=catalog.student, catalog_per_subject=catalog, semester=2, grade=7, grade_type=SubjectGrade.GradeTypes.THESIS)

        SubjectAbsenceFactory(student=catalog.student, catalog_per_subject=catalog, is_founded=True, taken_at=datetime.date(2019, 12, 12), semester=1)
        SubjectAbsenceFactory(student=catalog.student, catalog_per_subject=catalog, is_founded=True, taken_at=datetime.date(2019, 12, 13), semester=1)
        SubjectAbsenceFactory(student=catalog.student, catalog_per_subject=catalog, is_founded=False, taken_at=datetime.date(2019, 12, 12), semester=1)
        SubjectAbsenceFactory(student=catalog.student, catalog_per_subject=catalog, is_founded=False, taken_at=datetime.date(2019, 12, 13), semester=1)

        SubjectAbsenceFactory(student=catalog.student, catalog_per_subject=catalog, is_founded=True, taken_at=datetime.date(2020, 4, 2), semester=2)
        SubjectAbsenceFactory(student=catalog.student, catalog_per_subject=catalog, is_founded=True, taken_at=datetime.date(2020, 4, 3), semester=2)
        SubjectAbsenceFactory(student=catalog.student, catalog_per_subject=catalog, is_founded=False, taken_at=datetime.date(2020, 4, 2), semester=2)
        SubjectAbsenceFactory(student=catalog.student, catalog_per_subject=catalog, is_founded=False, taken_at=datetime.date(2020, 4, 3), semester=2)

        ExaminationGradeFactory(
            student=catalog.student,
            catalog_per_subject=catalog,
            taken_at=datetime.date(2020, 4, 3),
            grade1=5,
            grade2=6,
            grade_type=ExaminationGrade.GradeTypes.SECOND_EXAMINATION,
            examination_type=ExaminationGrade.ExaminationTypes.WRITTEN
        )
        ExaminationGradeFactory(
            student=catalog.student,
            catalog_per_subject=catalog,
            taken_at=datetime.date(2020, 4, 3),
            grade1=7,
            grade2=8,
            grade_type=ExaminationGrade.GradeTypes.SECOND_EXAMINATION,
            examination_type=ExaminationGrade.ExaminationTypes.ORAL
        )
        ExaminationGradeFactory(
            student=catalog.student,
            catalog_per_subject=catalog,
            taken_at=datetime.date(2019, 12, 12),
            grade1=7,
            grade2=8,
            semester=1,
            grade_type=ExaminationGrade.GradeTypes.DIFFERENCE,
            examination_type=ExaminationGrade.ExaminationTypes.WRITTEN
        )
        ExaminationGradeFactory(
            student=catalog.student,
            catalog_per_subject=catalog,
            taken_at=datetime.date(2019, 12, 12),
            grade1=7,
            grade2=8,
            semester=2,
            grade_type=ExaminationGrade.GradeTypes.DIFFERENCE,
            examination_type=ExaminationGrade.ExaminationTypes.WRITTEN
        )
        ExaminationGradeFactory(
            student=catalog.student,
            catalog_per_subject=catalog,
            taken_at=datetime.date(2020, 4, 3),
            grade1=7,
            grade2=8,
            semester=1,
            grade_type=ExaminationGrade.GradeTypes.DIFFERENCE,
            examination_type=ExaminationGrade.ExaminationTypes.ORAL
        )
        ExaminationGradeFactory(
            student=catalog.student,
            catalog_per_subject=catalog,
            taken_at=datetime.date(2020, 4, 3),
            grade1=7,
            grade2=8,
            semester=2,
            grade_type=ExaminationGrade.GradeTypes.DIFFERENCE,
            examination_type=ExaminationGrade.ExaminationTypes.ORAL
        )
        ExaminationGradeFactory(
            student=catalog.student,
            catalog_per_subject=catalog,
            taken_at=datetime.date(2019, 12, 12),
            grade1=7,
            grade2=8,
            grade_type=ExaminationGrade.GradeTypes.DIFFERENCE,
            examination_type=ExaminationGrade.ExaminationTypes.WRITTEN
        )
        ExaminationGradeFactory(
            student=catalog.student,
            catalog_per_subject=catalog,
            taken_at=datetime.date(2020, 4, 3),
            grade1=7,
            grade2=8,
            grade_type=ExaminationGrade.GradeTypes.DIFFERENCE,
            examination_type=ExaminationGrade.ExaminationTypes.ORAL
        )

        response = self.client.get(self.build_url(self.study_class.id, self.subject.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        row_nr = 0
        for index, row in enumerate(self.get_csv_rows_from_response(response)):
            row_nr += 1
            self.assertCountEqual(row.keys(), expected_fields)

            if row_nr == 1:
                self.assertEqual(row['Nume'], 'a')
                for key, value in row.items():
                    self.assertNotEqual(value, '')

            if row_nr == 2:
                self.assertEqual(row['Nume'], 'b')
                for field in ['Note sem. I', 'Note sem. II', 'Absențe motivate sem. I', 'Absențe nemotivate sem. I', 'Absențe motivate sem. II', 'Absențe nemotivate sem. II']:
                    self.assertEqual(len(row[field].split(';')), 2)
                for field in [
                    'Diferență sem. I Oral Prof. I', 'Diferență sem. I Oral Prof. II', 'Diferență sem. I Scris Prof. I', 'Diferență sem. I Scris Prof. II',
                    'Diferență sem. II Oral Prof. I', 'Diferență sem. II Oral Prof. II', 'Diferență sem. II Scris Prof. I', 'Diferență sem. II Scris Prof. II',
                    'Diferență anuală Oral Prof. I', 'Diferență anuală Oral Prof. II', 'Diferență anuală Scris Prof. I', 'Diferență anuală Scris Prof. II'
                ]:
                    self.assertEqual(len(row[field].split(';')), 1)

                for field in ['Teză', 'Scutit', 'Simulări', 'Scutit', 'Teste inițiale / finale']:
                    self.assertEqual(row[field], 'Nu')

                self.assertEqual(row['Înregistrat opțional'], 'Da')
                self.assertEqual(len([value for value in row.values() if value != '-']), len(row.values()))

        self.assertEqual(row_nr, 2)
