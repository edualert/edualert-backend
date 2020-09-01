import csv
import datetime
import io
from copy import copy
from decimal import Decimal

from ddt import data, ddt, unpack
from django.test.client import encode_multipart
from django.urls import reverse
from rest_framework import status

from edualert.academic_calendars.factories import AcademicYearCalendarFactory, SchoolEventFactory
from edualert.academic_calendars.models import SchoolEvent
from edualert.catalogs.factories import StudentCatalogPerSubjectFactory, SubjectGradeFactory, ExaminationGradeFactory, StudentCatalogPerYearFactory
from edualert.catalogs.models import SubjectGrade, ExaminationGrade
from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory, LabelFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.study_classes.factories import StudyClassFactory, TeacherClassThroughFactory
from edualert.subjects.factories import SubjectFactory, ProgramSubjectThroughFactory


@ddt
class CatalogImportTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.school = RegisteredSchoolUnitFactory()
        cls.teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=cls.school)
        cls.study_class = StudyClassFactory(school_unit=cls.school, class_grade='IX', class_grade_arabic=9, class_letter='A')
        cls.student = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=cls.school, student_in_class=cls.study_class)
        cls.subject = SubjectFactory()
        cls.teacher_class_through = TeacherClassThroughFactory(study_class=cls.study_class, teacher=cls.teacher, subject=cls.subject)
        cls.current_calendar = AcademicYearCalendarFactory()
        cls.label = LabelFactory(user_role=UserProfile.UserRoles.STUDENT, text='good')
        cls.label2 = LabelFactory(user_role=UserProfile.UserRoles.STUDENT, text='v good')
        cls.subject_through = ProgramSubjectThroughFactory(
            subject=cls.subject,
            class_grade='IX',
            class_grade_arabic=9,
            is_mandatory=True,
            generic_academic_program=cls.study_class.academic_program.generic_academic_program,
            weekly_hours_count=1,
        )
        cls.differences_event = SchoolEventFactory(
            event_type=SchoolEvent.EventTypes.DIFERENTE, semester=cls.current_calendar.first_semester,
            academic_year_calendar=cls.current_calendar, starts_at=datetime.date(2019, 12, 21), ends_at=datetime.date(2019, 12, 23)
        )
        cls.second_examination_event = SchoolEventFactory(
            event_type=SchoolEvent.EventTypes.CORIGENTE, academic_year_calendar=cls.current_calendar,
            starts_at=datetime.date(2020, 5, 4), ends_at=datetime.date(2020, 5, 7)
        )
        cls.catalog_per_year = StudentCatalogPerYearFactory(study_class=cls.study_class, student=cls.student)
        cls.file_name = 'file.csv'

    def setUp(self):
        self.catalog = StudentCatalogPerSubjectFactory(study_class=self.study_class, teacher=self.teacher, subject=self.subject, student=self.student, is_enrolled=True)
        self.study_class.refresh_from_db()
        self.teacher_class_through.refresh_from_db()
        self.data = {
            'Nume': self.student.full_name,
            'Etichete': 'good; v good',
            'Note sem. I': '',
            'Teză sem. I': '',
            'Note sem. II': '4-4-2020: 10; 5-4-2020: 10',
            'Teză sem. II': '4-4-2020: 7',
            'Diferență sem. I Oral Prof. I': '22-12-2019: 6',
            'Diferență sem. I Oral Prof. II': '22-12-2019: 7',
            'Diferență sem. I Scris Prof. I': '22-12-2019: 8',
            'Diferență sem. I Scris Prof. II': '22-12-2019: 9',
            'Diferență sem. II Oral Prof. I': '',
            'Diferență sem. II Oral Prof. II': '',
            'Diferență sem. II Scris Prof. I': '',
            'Diferență sem. II Scris Prof. II': '',
            'Diferență anuală Oral Prof. I': '',
            'Diferență anuală Oral Prof. II': '',
            'Diferență anuală Scris Prof. I': '',
            'Diferență anuală Scris Prof. II': '',
            'Corigență Oral Prof. I': '5-5-2020: 6',
            'Corigență Oral Prof. II': '5-5-2020: 7',
            'Corigență Scris Prof. I': '5-5-2020: 8',
            'Corigență Scris Prof. II': '5-5-2020: 9',
            'Absențe motivate sem. I': '12-12-2019; 13-12-2019',
            'Absențe motivate sem. II': '4-4-2020; 5-4-2020',
            'Absențe nemotivate sem. I': '12-12-2019; 13-12-2019',
            'Absențe nemotivate sem. II': '4-4-2020; 5-4-2020',
            'Observații': 'foarte bun elev',
            'Teste inițiale / finale': 'Da',
            'Teză': 'Da',
            'Simulări': 'Da',
            'Scutit': 'Nu',
            'Înregistrat opțional': 'Da'
        }

    @staticmethod
    def create_file(file_name):
        file = io.StringIO()
        file.name = file_name
        return file

    def get_response(self, url, file):
        file.seek(0)
        response = self.client.post(url, data={'file': file}, format='multipart')
        return response

    @staticmethod
    def write_data(file, data_to_write):
        writer = csv.DictWriter(file, fieldnames=data_to_write.keys())
        writer.writeheader()
        writer.writerow(data_to_write)

        return writer

    def assertError(self, response, field, error):
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(response.data.keys(), ['errors', 'report'])
        self.assertEqual(response.data['report'], '0 out of 1 catalog saved successfully.')
        self.assertCountEqual(response.data['errors'].keys(), [1])
        self.assertCountEqual(response.data['errors'][1].keys(), [field])
        self.assertEqual(response.data['errors'][1][field], error)

    @staticmethod
    def build_url(study_class_id, subject_id):
        return reverse('catalogs:import-subject-catalogs', kwargs={'study_class_id': study_class_id, 'subject_id': subject_id})

    @staticmethod
    def get_csv_rows_from_response(response):
        buffer = io.StringIO()
        buffer.write(response.content.decode('utf-8'))
        buffer.seek(0)

        return csv.DictReader(buffer)

    def test_catalog_export_unauthenticated(self):
        response = self.client.post(self.build_url(self.study_class.id, self.subject.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.PRINCIPAL,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_catalog_import_wrong_user_type(self, user_role):
        user = UserProfileFactory(
            user_role=user_role,
            school_unit=self.school if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )
        self.client.login(username=user.username, password='passwd')

        file = self.create_file(self.file_name)
        response = self.get_response(self.build_url(self.study_class.id, self.subject.id), file)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_catalog_import_does_not_teach_class(self):
        self.client.login(username=self.teacher.username, password='passwd')
        self.teacher_class_through.study_class = StudyClassFactory()
        self.teacher_class_through.save()

        file = self.create_file(self.file_name)
        response = self.get_response(self.build_url(self.study_class.id, self.subject.id), file)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_catalog_import_subject_not_taught_in_study_class(self):
        self.client.login(username=self.teacher.username, password='passwd')

        file = self.create_file(self.file_name)
        response = self.get_response(self.build_url(self.study_class.id, SubjectFactory().id), file)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_catalog_import_does_not_teach_subject(self):
        self.client.login(username=self.teacher.username, password='passwd')
        self.teacher_class_through.subject = SubjectFactory()
        self.teacher_class_through.save()

        file = self.create_file(self.file_name)
        response = self.get_response(self.build_url(self.study_class.id, self.subject.id), file)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @data(
        'text/html',
        'text/csv',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    def test_catalog_import_wrong_content_type(self, content_type):
        self.client.login(username=self.teacher, password='passwd')
        file = self.create_file(self.file_name)
        file.write('aaa')

        response = self.client.post(self.build_url(self.study_class.id, self.subject.id), data={'file': file}, content_type=content_type)
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
        self.assertEqual(response.data, {'detail': f'Unsupported media type "{content_type}" in request.'})

    @data(
        'file.txt', 'file.docx', 'file.csvx'
    )
    def test_catalog_import_invalid_extension(self, file_name):
        self.client.login(username=self.teacher.username, password='passwd')
        file = self.create_file(file_name)
        file.write('aaa')
        response = self.get_response(self.build_url(self.study_class.id, self.subject.id), file)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'file': ['File must be csv.']})

    def test_catalog_import_invalid_file(self):
        url = self.build_url(self.study_class.id, self.subject.id)
        # No file at all
        self.client.login(username=self.teacher.username, password='passwd')
        no_file_sent_error = {'file': ['No file was submitted.']}
        response = self.client.post(url, format='multipart')
        self.assertEqual(response.data, no_file_sent_error)

        # Wrong key
        file = self.create_file(self.file_name)
        response = self.client.post(url, {'wrong_file': file}, format='multipart')
        self.assertEqual(response.data, no_file_sent_error)

        # Wrong boundary
        request_data = encode_multipart('==boundary', {'file': file})
        content_type = 'multipart/form-data; boundary=WrongBoundary'
        response = self.client.post(url, request_data, content_type=content_type)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, no_file_sent_error)

    @data(
        'file', 'file.ext.ext', 'file()'
    )
    def test_catalog_import_invalid_file_name(self, file_name):
        self.client.login(username=self.teacher.username, password='passwd')
        file = self.create_file(file_name)
        file.write('aaa')
        response = self.get_response(self.build_url(self.study_class.id, self.subject.id), file)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'non_field_errors': ['Invalid file name.']})

    def test_catalog_import_missing_fields(self):
        self.client.login(username=self.teacher.username, password='passwd')

        for field in self.data.keys():
            data_to_send = {required_field: value for required_field, value in self.data.items() if required_field != field}

            file = self.create_file(self.file_name)
            self.write_data(file, data_to_send)
            response = self.get_response(self.build_url(self.study_class.id, self.subject.id), file)
            self.assertError(response, field, 'This field is required.')

    def test_catalog_import_student_not_found(self):
        self.client.login(username=self.teacher.username, password='passwd')

        self.data['Nume'] = 'Ceva nume'
        file = self.create_file(self.file_name)
        self.write_data(file, self.data)

        response = self.get_response(self.build_url(self.study_class.id, self.subject.id), file)
        self.assertError(response, 'Nume', "A student with this name doesn't exist yet.")

    def test_catalog_import_catalog_does_not_exist(self):
        self.client.login(username=self.teacher.username, password='passwd')
        self.catalog.delete()

        file = self.create_file(self.file_name)
        self.write_data(file, self.data)

        response = self.get_response(self.build_url(self.study_class.id, self.subject.id), file)
        self.assertError(response, 'Nume', "A catalog for this student and subject doesn't exist yet.")

    @data(
        'good, v good', 'vgood', 'good; good'
    )
    def test_catalog_import_label_does_not_exist(self, labels):
        self.client.login(username=self.teacher.username, password='passwd')
        self.data['Etichete'] = labels

        file = self.create_file(self.file_name)
        self.write_data(file, self.data)

        response = self.get_response(self.build_url(self.study_class.id, self.subject.id), file)
        self.assertError(response, 'Etichete', 'Labels must exist, be unique, and be for the student user role.')

    def test_catalog_import_label_for_wrong_user_role(self):
        self.client.login(username=self.teacher.username, password='passwd')
        LabelFactory(text='other_label', user_role=UserProfile.UserRoles.PARENT)
        self.data['Etichete'] = 'other label'

        file = self.create_file(self.file_name)
        self.write_data(file, self.data)

        response = self.get_response(self.build_url(self.study_class.id, self.subject.id), file)
        self.assertError(response, 'Etichete', 'Labels must exist, be unique, and be for the student user role.')

    @data(
        ('Teză sem. I', '12-12-2019: 7; 13-12-2019: 9'),
        ('Teză sem. II', '4-4-2020: 5; 5-4-2020: 10')
    )
    @unpack
    def test_catalog_import_more_than_one_thesis_grade(self, field, value):
        self.client.login(username=self.teacher.username, password='passwd')
        self.data[field] = value

        for diff_field in ['Diferență sem. I Oral Prof. I', 'Diferență sem. I Oral Prof. II', 'Diferență sem. I Scris Prof. I',  'Diferență sem. I Scris Prof. II']:
            self.data[diff_field] = ''

        file = self.create_file(self.file_name)
        self.write_data(file, self.data)

        response = self.get_response(self.build_url(self.study_class.id, self.subject.id), file)
        self.assertError(response, field, 'Only one grade allowed.')

    @data(
        ('Note sem. I', '4-4-2020: 7; 12-12-2019: 9', 'first'),
        ('Note sem. II', '4-4-2020: 7; 12-12-2019: 10', 'second'),
        ('Teză sem. I', '4-4-2020: 5', 'first'),
        ('Teză sem. II', '12-12-2019: 5', 'second'),
        ('Absențe motivate sem. I', '4-4-2020', 'first'),
        ('Absențe nemotivate sem. I', '4-4-2020', 'first'),
        ('Absențe motivate sem. II', '12-12-2019', 'second'),
        ('Absențe nemotivate sem. II', '12-12-2019', 'second')
    )
    @unpack
    def test_catalog_import_outside_semester(self, field, grades, semester):
        self.client.login(username=self.teacher.username, password='passwd')
        self.data[field] = grades

        for difference in ['Diferență sem. I Oral Prof. I', 'Diferență sem. I Oral Prof. II',
                           'Diferență sem. I Scris Prof. I', 'Diferență sem. I Scris Prof. II']:
            self.data[difference] = ''

        file = self.create_file(self.file_name)
        self.write_data(file, self.data)
        response = self.get_response(self.build_url(self.study_class.id, self.subject.id), file)
        self.assertError(response, field, f'Must be inside the {semester} semester.')

    @data(
        '4-4-2020: ten; 4-4-2020: 10', '4-4-2020: 5.5; 4-4-2020: 10', '4-4-2020-5; 4-4-2020: 10',
        '4-4-2020: : 10; 4-4-2020: 10', '4-4-2020, 5; 4-4-2020: 10', '4-4-2020; 4-4-2020: 10'
    )
    def test_catalog_import_grades_validations(self, grade):
        self.client.login(username=self.teacher.username, password='passwd')
        self.data['Note sem. II'] = grade

        file = self.create_file(self.file_name)
        self.write_data(file, self.data)
        response = self.get_response(self.build_url(self.study_class.id, self.subject.id), file)
        self.assertError(response, 'Note sem. II', 'Must be in the format DD-MM-YYYY: grade.')

    @data(
        '-1', '11'
    )
    def test_catalog_import_invalid_grade(self, grade):
        self.client.login(username=self.teacher.username, password='passwd')
        self.data['Note sem. II'] = f'4-4-2020: {grade}'

        file = self.create_file(self.file_name)
        self.write_data(file, self.data)
        response = self.get_response(self.build_url(self.study_class.id, self.subject.id), file)
        self.assertError(response, 'Note sem. II', 'Grade must be between 1 and 10.')

    @data(
        'Teste inițiale / finale', 'Teză', 'Simulări', 'Scutit', 'Înregistrat opțional'
    )
    def test_catalog_import_boolean_validation(self, field):
        self.client.login(username=self.teacher.username, password='passwd')

        invalid_values = ['yes', 'no', 'True', 'true', '0', '1']
        for value in invalid_values:
            self.data[field] = value
            file = self.create_file(self.file_name)
            self.write_data(file, self.data)

            response = self.get_response(self.build_url(self.study_class.id, self.subject.id), file)
            self.assertError(response, field, 'Must be either "Da" or "Nu".')

    def test_catalog_import_allows_exemption(self):
        self.client.login(username=self.teacher.username, password='passwd')
        self.subject.allows_exemption = False
        self.subject.save()

        self.data['Scutit'] = 'Da'
        file = self.create_file(self.file_name)
        self.write_data(file, self.data)

        response = self.get_response(self.build_url(self.study_class.id, self.subject.id), file)
        self.assertError(response, 'Scutit', 'The subject does not allow exemption.')

        self.subject.allows_exemption = True
        self.subject.save()
        file = self.create_file(self.file_name)
        self.write_data(file, self.data)

        response = self.get_response(self.build_url(self.study_class.id, self.subject.id), file)
        self.assertEqual(response.data['errors'], {})

    def test_catalog_import_mandatory_subject(self):
        self.client.login(username=self.teacher.username, password='passwd')

        self.data['Înregistrat opțional'] = 'Nu'
        file = self.create_file(self.file_name)
        self.write_data(file, self.data)

        response = self.get_response(self.build_url(self.study_class.id, self.subject.id), file)
        self.assertError(response, 'Înregistrat opțional', 'Must be enrolled to all mandatory subjects.')

        self.subject_through.generic_academic_program = None
        self.subject_through.academic_program = self.study_class.academic_program
        self.subject_through.is_mandatory = False
        self.subject_through.save()

        file = self.create_file(self.file_name)
        self.write_data(file, self.data)

        response = self.get_response(self.build_url(self.study_class.id, self.subject.id), file)
        self.assertEqual(response.data['errors'], {})
        self.catalog.refresh_from_db()
        self.assertFalse(self.catalog.is_enrolled)

    def test_catalog_import_thesis_validation(self):
        self.client.login(username=self.teacher.username, password='passwd')
        self.data['Teză'] = 'Nu'
        self.data['Teză sem. I'] = '12-12-2019: 10'

        for difference in ['Diferență sem. I Oral Prof. I', 'Diferență sem. I Oral Prof. II',
                           'Diferență sem. I Scris Prof. I', 'Diferență sem. I Scris Prof. II']:
            self.data[difference] = ''

        file = self.create_file(self.file_name)
        self.write_data(file, self.data)
        response = self.get_response(self.build_url(self.study_class.id, self.subject.id), file)

        self.assertCountEqual(response.data['errors'][1], ['Teză sem. I', 'Teză sem. II'])
        for field in ['Teză sem. I', 'Teză sem. II']:
            self.assertEqual(response.data['errors'][1][field], "Thesis grades are not allowed if the user doesn't want thesis.")

        self.data['Teză sem. I'] = ''
        self.data['Teză sem. II'] = ''
        SubjectGradeFactory(grade_type=SubjectGrade.GradeTypes.THESIS, catalog_per_subject=self.catalog)
        file = self.create_file(self.file_name)
        self.write_data(file, self.data)
        response = self.get_response(self.build_url(self.study_class.id, self.subject.id), file)
        self.assertError(response, 'Teză', 'This field cannot be false if the student already has thesis grades.')

    def test_catalog_import_remarks_validation(self):
        self.client.login(username=self.teacher.username, password='passwd')
        self.data['Observații'] = 'a' * 501

        file = self.create_file(self.file_name)
        self.write_data(file, self.data)
        response = self.get_response(self.build_url(self.study_class.id, self.subject.id), file)
        self.assertError(response, 'Observații', 'Maximum 500 characters allowed.')

    @data(
        ('Diferență sem. I Oral Prof. I', 'Diferență sem. I Oral Prof. II', 'Diferență sem. I Scris Prof. I', 'Diferență sem. I Scris Prof. II'),
        ('Diferență sem. II Oral Prof. I', 'Diferență sem. II Oral Prof. II', 'Diferență sem. II Scris Prof. I', 'Diferență sem. II Scris Prof. II'),
        ('Diferență anuală Oral Prof. I', 'Diferență anuală Oral Prof. II', 'Diferență anuală Scris Prof. I', 'Diferență anuală Scris Prof. II')
    )
    def test_catalog_import_all_difference_grades_present(self, fields):
        self.client.login(username=self.teacher.username, password='passwd')
        self.data['Note sem. I'] = ''
        self.data['Note sem. II'] = ''
        self.data['Teză sem. II'] = ''
        for field in [
            'Diferență sem. I Oral Prof. I', 'Diferență sem. I Oral Prof. II', 'Diferență sem. I Scris Prof. I',
            'Diferență sem. I Scris Prof. II', 'Diferență sem. II Oral Prof. I', 'Diferență sem. II Oral Prof. II',
            'Diferență sem. II Scris Prof. I', 'Diferență sem. II Scris Prof. II', 'Diferență anuală Oral Prof. I',
            'Diferență anuală Oral Prof. II', 'Diferență anuală Scris Prof. I', 'Diferență anuală Scris Prof. II',
            'Corigență Oral Prof. I', 'Corigență Oral Prof. II', 'Corigență Scris Prof. I', 'Corigență Scris Prof. II'
        ]:
            self.data[field] = ''

        for field in fields:
            self.data[field] = ""
        file = self.create_file(self.file_name)
        self.write_data(file, self.data)
        response = self.get_response(self.build_url(self.study_class.id, self.subject.id), file)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['errors'], {})

        self.data[fields[0]] = "22-12-2019: 6"
        file = self.create_file(self.file_name)
        self.write_data(file, self.data)
        response = self.get_response(self.build_url(self.study_class.id, self.subject.id), file)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        SubjectGrade.objects.all().delete()
        self.data[fields[0]] = ""
        for field in fields[1:]:
            self.data[field] = "22-12-2019: 6"

        file = self.create_file(self.file_name)
        self.write_data(file, self.data)
        response = self.get_response(self.build_url(self.study_class.id, self.subject.id), file)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for field in fields:
            self.assertEqual(response.data['errors'][1][field], 'Cannot add difference unless all fields for this semester are provided.')

    def test_catalog_import_difference_grades_already_has_grades_that_semester(self):
        self.client.login(username=self.teacher.username, password='passwd')
        grade = SubjectGradeFactory(semester=1, catalog_per_subject=self.catalog)

        file = self.create_file(self.file_name)
        self.write_data(file, self.data)
        response = self.get_response(self.build_url(self.study_class.id, self.subject.id), file)
        for field in ['Diferență sem. I Oral Prof. I', 'Diferență sem. I Oral Prof. II',
                      'Diferență sem. I Scris Prof. I', 'Diferență sem. I Scris Prof. II']:
            self.assertEqual(response.data['errors'][1][field], 'Cannot have difference grades if there already are grades for this semester.')

        grade.delete()
        self.data['Note sem. I'] = '12-12-2019: 7'
        file = self.create_file(self.file_name)
        self.write_data(file, self.data)
        response = self.get_response(self.build_url(self.study_class.id, self.subject.id), file)
        for field in ['Diferență sem. I Oral Prof. I', 'Diferență sem. I Oral Prof. II',
                      'Diferență sem. I Scris Prof. I', 'Diferență sem. I Scris Prof. II']:
            self.assertEqual(response.data['errors'][1][field], 'Cannot have difference grades if there already are grades for this semester.')

    def test_catalog_import_thesis_is_overridden(self):
        self.client.login(username=self.teacher.username, password='passwd')
        thesis_sem1 = SubjectGradeFactory(
            catalog_per_subject=self.catalog,
            semester=1,
            grade_type=SubjectGrade.GradeTypes.THESIS
        )
        thesis_sem2 = SubjectGradeFactory(
            catalog_per_subject=self.catalog,
            semester=2,
            grade_type=SubjectGrade.GradeTypes.THESIS
        )
        for field in [
            'Diferență sem. I Oral Prof. I', 'Diferență sem. I Oral Prof. II',
            'Diferență sem. I Scris Prof. I', 'Diferență sem. I Scris Prof. II',
            'Diferență sem. II Oral Prof. I', 'Diferență sem. II Oral Prof. II',
            'Diferență sem. II Scris Prof. I', 'Diferență sem. II Scris Prof. II',
            'Diferență anuală Oral Prof. I', 'Diferență anuală Oral Prof. II',
            'Diferență anuală Scris Prof. I', 'Diferență anuală Scris Prof. II'
        ]:
            self.data[field] = ''

        file = self.create_file(self.file_name)
        self.write_data(file, self.data)
        response = self.get_response(self.build_url(self.study_class.id, self.subject.id), file)
        self.assertEqual(response.data['errors'], {})
        self.assertFalse(SubjectGrade.objects.filter(grade_type__in=SubjectGrade.GradeTypes.THESIS, id__in=[thesis_sem1.id, thesis_sem2.id]))

    def test_catalog_import_examinations_outside_event(self):
        self.client.login(username=self.teacher.username, password='passwd')
        data_to_send = copy(self.data)
        for field in [
            'Diferență sem. I Oral Prof. I', 'Diferență sem. I Oral Prof. II',
            'Diferență sem. I Scris Prof. I', 'Diferență sem. I Scris Prof. II',
            'Corigență Oral Prof. I', 'Corigență Oral Prof. II', 'Corigență Scris Prof. I', 'Corigență Scris Prof. II'
        ]:
            data_to_send[field] = '3-3-2020: 10'
            file = self.create_file(self.file_name)
            self.write_data(file, data_to_send)
            response = self.get_response(self.build_url(self.study_class.id, self.subject.id), file)
            self.assertError(response, field, 'Must be during the examination event.')

            data_to_send = copy(self.data)

    def test_catalog_import_success(self):
        self.client.login(username=self.teacher.username, password='passwd')
        file = self.create_file(self.file_name)
        writer = self.write_data(file, self.data)

        # Create a few thesis and difference grade that should be deleted
        difference_sem1 = ExaminationGradeFactory(
            grade_type=ExaminationGrade.GradeTypes.DIFFERENCE,
            examination_type=ExaminationGrade.ExaminationTypes.ORAL,
            catalog_per_subject=self.catalog,
            semester=1
        )

        other_student = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=self.school, student_in_class=self.study_class)
        other_catalog = StudentCatalogPerSubjectFactory(study_class=self.study_class, teacher=self.teacher, subject=self.subject, student=other_student, is_enrolled=True)
        other_catalog_per_year = StudentCatalogPerYearFactory(study_class=self.study_class, student=other_student)
        self.data['Nume'] = other_student.full_name
        writer.writerow(self.data)

        writer.writerow({})

        response = self.get_response(self.build_url(self.study_class.id, self.subject.id), file)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertNotIn(1, response.data['errors'])
        self.assertNotIn(2, response.data['errors'])

        self.assertNotEqual(response.data['errors'][3], {})
        self.assertEqual(response.data['report'], '2 out of 3 catalogs saved successfully.')

        self.assertFalse(ExaminationGrade.objects.filter(id=difference_sem1.id).exists())

        self.catalog = self.student.student_catalogs_per_subject.first()
        other_catalog = other_student.student_catalogs_per_subject.first()
        for catalog in [self.catalog, other_catalog]:
            self.assertEqual(catalog.remarks, self.data['Observații'])
            self.assertEqual(catalog.wants_level_testing_grade, True)
            self.assertEqual(catalog.wants_thesis, True)
            self.assertEqual(catalog.wants_simulation, True)
            self.assertEqual(catalog.is_exempted, False)
            self.assertEqual(catalog.is_enrolled, True)
            self.assertEqual(catalog.founded_abs_count_sem1, len(self.data['Absențe motivate sem. I'].split('; ')))
            self.assertEqual(catalog.unfounded_abs_count_sem1, len(self.data['Absențe nemotivate sem. I'].split('; ')))
            self.assertEqual(catalog.founded_abs_count_sem2, len(self.data['Absențe motivate sem. II'].split('; ')))
            self.assertEqual(catalog.unfounded_abs_count_sem2, len(self.data['Absențe nemotivate sem. II'].split('; ')))
            self.assertEqual(catalog.founded_abs_count_annual, catalog.founded_abs_count_sem1 + catalog.founded_abs_count_sem2)
            self.assertEqual(catalog.unfounded_abs_count_annual, catalog.unfounded_abs_count_sem1 + catalog.unfounded_abs_count_sem2)
        for student in [self.student, other_student]:
            self.assertCountEqual(student.labels.values_list('id', flat=True), [self.label.id, self.label2.id])

        self.study_class.refresh_from_db()
        self.assertEqual(self.study_class.avg_sem1, 8)
        self.assertEqual(self.study_class.avg_annual, Decimal(8.25))
        self.assertEqual(self.study_class.unfounded_abs_avg_sem1, 2)
        self.assertEqual(self.study_class.unfounded_abs_avg_sem2, 2)
        self.assertEqual(self.study_class.unfounded_abs_avg_annual, 4)
        self.assertEqual(self.study_class.academic_program.unfounded_abs_avg_sem1, 2)
        self.assertEqual(self.study_class.academic_program.unfounded_abs_avg_sem2, 2)
        self.assertEqual(self.study_class.academic_program.unfounded_abs_avg_annual, 4)

        for catalog in [self.catalog, other_catalog]:
            self.assertEqual(catalog.grades.filter(
                semester=1,
                taken_at__in=[datetime.date(2019, 12, 13), datetime.date(2019, 12, 12)],
                grade=10,
                grade_type=SubjectGrade.GradeTypes.REGULAR
            ).count(), 0)
            self.assertEqual(catalog.grades.filter(
                semester=1,
                taken_at=datetime.date(2019, 12, 19),
                grade=7,
                grade_type=SubjectGrade.GradeTypes.THESIS
            ).count(), 0)
            self.assertEqual(catalog.grades.filter(
                semester=2,
                taken_at__in=[datetime.date(2020, 4, 4), datetime.date(2020, 4, 5)],
                grade=10,
                grade_type=SubjectGrade.GradeTypes.REGULAR
            ).count(), 2)
            self.assertEqual(catalog.grades.filter(
                semester=2,
                taken_at=datetime.date(2020, 4, 4),
                grade=7,
                grade_type=SubjectGrade.GradeTypes.THESIS
            ).count(), 1)
            self.assertEqual(catalog.absences.filter(
                semester=1,
                taken_at__in=[datetime.date(2019, 12, 12), datetime.date(2019, 12, 13)],
                is_founded=True
            ).count(), 2)
            self.assertEqual(catalog.absences.filter(
                semester=1,
                taken_at__in=[datetime.date(2019, 12, 12), datetime.date(2019, 12, 13)],
                is_founded=False
            ).count(), 2)
            self.assertEqual(catalog.absences.filter(
                semester=2,
                taken_at__in=[datetime.date(2020, 4, 4), datetime.date(2020, 4, 5)],
                is_founded=True
            ).count(), 2)
            self.assertEqual(catalog.absences.filter(
                semester=2,
                taken_at__in=[datetime.date(2020, 4, 4), datetime.date(2020, 4, 5)],
                is_founded=False
            ).count(), 2)
            self.assertEqual(catalog.examination_grades.filter(
                grade_type=ExaminationGrade.GradeTypes.DIFFERENCE,
                examination_type=ExaminationGrade.ExaminationTypes.ORAL,
                semester=1,
                taken_at=datetime.date(2019, 12, 22),
                grade1=6,
                grade2=7
            ).count(), 1)
            self.assertEqual(catalog.examination_grades.filter(
                grade_type=ExaminationGrade.GradeTypes.DIFFERENCE,
                examination_type=ExaminationGrade.ExaminationTypes.ORAL,
                semester=1,
                taken_at=datetime.date(2019, 12, 22),
                grade1=6,
                grade2=7
            ).count(), 1)
            self.assertEqual(catalog.examination_grades.filter(
                grade_type=ExaminationGrade.GradeTypes.DIFFERENCE,
                examination_type=ExaminationGrade.ExaminationTypes.ORAL,
                semester=2,
                taken_at=datetime.date(2020, 4, 20),
                grade1=6,
                grade2=7
            ).count(), 0)
            self.assertEqual(catalog.examination_grades.filter(
                grade_type=ExaminationGrade.GradeTypes.DIFFERENCE,
                examination_type=ExaminationGrade.ExaminationTypes.WRITTEN,
                semester=2,
                taken_at=datetime.date(2020, 4, 20),
                grade1=8,
                grade2=9
            ).count(), 0)
            self.assertEqual(catalog.examination_grades.filter(
                grade_type=ExaminationGrade.GradeTypes.DIFFERENCE,
                examination_type=ExaminationGrade.ExaminationTypes.ORAL,
                taken_at=datetime.date(2019, 12, 22),
                grade1=6,
                grade2=7,
                semester__isnull=True
            ).count(), 0)

            self.assertEqual(catalog.examination_grades.filter(
                grade_type=ExaminationGrade.GradeTypes.DIFFERENCE,
                examination_type=ExaminationGrade.ExaminationTypes.WRITTEN,
                taken_at=datetime.date(2019, 12, 22),
                grade1=8,
                grade2=9,
                semester__isnull=True
            ).count(), 0)
            self.assertEqual(catalog.examination_grades.filter(
                grade_type=ExaminationGrade.GradeTypes.SECOND_EXAMINATION,
                examination_type=ExaminationGrade.ExaminationTypes.ORAL,
                taken_at=datetime.date(2020, 5, 5),
                grade1=6,
                grade2=7
            ).count(), 1)
            self.assertEqual(catalog.examination_grades.filter(
                grade_type=ExaminationGrade.GradeTypes.SECOND_EXAMINATION,
                examination_type=ExaminationGrade.ExaminationTypes.WRITTEN,
                taken_at=datetime.date(2020, 5, 5),
                grade1=8,
                grade2=9
            ).count(), 1)

            for field in ['wants_level_testing_grade', 'wants_thesis', 'wants_simulation', 'is_enrolled']:
                self.assertTrue(getattr(catalog, field), True)

            self.assertFalse(catalog.is_exempted)


