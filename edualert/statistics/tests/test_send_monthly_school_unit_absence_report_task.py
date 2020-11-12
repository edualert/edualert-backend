import datetime
from unittest import skip

from dateutil.relativedelta import relativedelta
from django.db import connection
from django.test import TestCase, override_settings
from django.utils import timezone

from edualert.academic_calendars.factories import AcademicYearCalendarFactory
from edualert.academic_programs.factories import AcademicProgramFactory
from edualert.catalogs.factories import StudentCatalogPerSubjectFactory, SubjectAbsenceFactory
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.statistics.tasks import send_monthly_school_unit_absence_report_task, _compute_report_data_for_school_unit
from edualert.study_classes.factories import StudyClassFactory
from edualert.subjects.factories import SubjectFactory


class SendMonthlySchoolUnitAbsenceReportTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        date = datetime.date(2020, 11, 1)
        year = date.year
        month = date.month
        report_date = date - relativedelta(months=1)
        target_year = report_date.year
        target_month = report_date.month
        cls.current_calendar = AcademicYearCalendarFactory()

        # generate X students
        def gen_students(count):
            return [UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT) for _ in range(0, count)]

        # declare a helper function to generate absences
        def gen_absences(catalog_per_subject, founded_absences, unfounded_absences):
            for i in range(0, unfounded_absences):
                SubjectAbsenceFactory(catalog_per_subject=catalog_per_subject, student=catalog_per_subject.student,
                                      taken_at=datetime.date(target_year, target_month, 1))
                SubjectAbsenceFactory(catalog_per_subject=catalog_per_subject, student=catalog_per_subject.student,
                                      taken_at=datetime.date(year, month, 1))
            for i in range(0, founded_absences):
                SubjectAbsenceFactory(catalog_per_subject=catalog_per_subject, student=catalog_per_subject.student,
                                      is_founded=True, taken_at=datetime.date(target_year, target_month, 1))
                SubjectAbsenceFactory(catalog_per_subject=catalog_per_subject, student=catalog_per_subject.student,
                                      is_founded=True, taken_at=datetime.date(year, month, 1))

        # generate subjects
        subject_names = ['Matematica', 'Limba Romana', 'Limba Engleza', 'Limba Franceza', 'Fizica', 'Chimie',
                         'Biologie', 'TIC', 'Educatie Fizica']
        all_subjects = [SubjectFactory(name=i) for i in subject_names]

        # declare helper for easier selection of subjects
        def select_subjects(*args):
            return [s for s in all_subjects if s.name in args]

        # Generate a new school
        cls.school_unit1 = RegisteredSchoolUnitFactory()
        academic_program1 = AcademicProgramFactory(school_unit=cls.school_unit1)
        study_class1 = StudyClassFactory(school_unit=cls.school_unit1, academic_program=academic_program1,
                                         class_grade='VI', class_grade_arabic=6, class_letter='A')
        study_class2 = StudyClassFactory(school_unit=cls.school_unit1, academic_program=academic_program1,
                                         class_grade='VII', class_grade_arabic=7, class_letter='Z')

        # Add two more classes to test order
        study_class3 = StudyClassFactory(school_unit=cls.school_unit1, academic_program=academic_program1,
                                         class_grade='VI', class_grade_arabic=6, class_letter='Z')
        study_class4 = StudyClassFactory(school_unit=cls.school_unit1, academic_program=academic_program1,
                                         class_grade='VII', class_grade_arabic=7, class_letter='A')

        # Add a fifth class; this will not appear in the results since it doesn't have any `StudentCatalogPerSubject`s
        StudyClassFactory(school_unit=cls.school_unit1, academic_program=academic_program1,
                          class_grade='X', class_grade_arabic=10, class_letter='A')

        # generate students and select subjects for the first school and class
        for student in gen_students(5):
            for subject in select_subjects('Matematica', 'Limba Romana', 'Limba Engleza', 'Limba Franceza'):
                catalog_per_subject = StudentCatalogPerSubjectFactory(study_class=study_class1, subject=subject, student=student)
                gen_absences(catalog_per_subject, 2, 3)

        # generate students and select subjects for the first school and second class
        for student in gen_students(10):
            for subject in select_subjects('Matematica', 'Fizica', 'Biologie'):
                catalog_per_subject = StudentCatalogPerSubjectFactory(study_class=study_class2, subject=subject, student=student)
                gen_absences(catalog_per_subject, 4, 5)

        # generate students and select subjects for the first school for third and forth class
        for student in gen_students(5):
            for subject in select_subjects('Matematica', 'Limba Romana', 'Limba Engleza', 'Biologie'):
                StudentCatalogPerSubjectFactory(study_class=study_class3, subject=subject, student=student)
                StudentCatalogPerSubjectFactory(study_class=study_class4, subject=subject, student=student)

        # Generate a new school
        cls.school_unit2 = RegisteredSchoolUnitFactory()
        academic_program2 = AcademicProgramFactory(school_unit=cls.school_unit2)
        study_class1 = StudyClassFactory(school_unit=cls.school_unit2, academic_program=academic_program2,
                                         class_grade='VI', class_letter='A')
        study_class2 = StudyClassFactory(school_unit=cls.school_unit2, academic_program=academic_program2,
                                         class_grade='VII', class_letter='Z')

        # generate students and select subjects for the second school and first class
        for student in gen_students(5):
            for subject in select_subjects('Matematica', 'Limba Romana', 'Limba Engleza', 'TIC'):
                catalog_per_subject = StudentCatalogPerSubjectFactory(study_class=study_class1, subject=subject, student=student)
                gen_absences(catalog_per_subject, 6, 7)

        # generate students and select subjects for the second school and class
        for student in gen_students(5):
            for subject in select_subjects('Matematica', 'Fizica', 'Chimie', 'Educatie Fizica'):
                catalog_per_subject = StudentCatalogPerSubjectFactory(study_class=study_class2, subject=subject, student=student)
                gen_absences(catalog_per_subject, 8, 9)

    @skip('Used only for manually testing the task')
    def test_send_monthly_school_unit_absence_report_task(self):
        # set the empty values based on Django's email settings
        email_host = ''
        email_host_user = ''
        email_host_password = ''
        email_port = 587
        email_backend = 'django.core.mail.backends.smtp.EmailBackend'
        # set email address for the sender and the email address where
        # the reports should be sent
        from_email = ''

        # setup SMTP credentials and send emails
        with override_settings(EMAIL_HOST=email_host, EMAIL_PORT=email_port, EMAIL_HOST_USER=email_host_user,
                               EMAIL_HOST_PASSWORD=email_host_password, EMAIL_BACKEND=email_backend, EMAIL_USE_TLS=True,
                               SERVER_EMAIL=from_email):
            send_monthly_school_unit_absence_report_task()

    def test__compute_report_data_for_school_unit(self):
        today = timezone.now().date()
        report_date = today - relativedelta(months=1)
        target_year = report_date.year
        target_month = report_date.month

        classes_dict = _compute_report_data_for_school_unit(self.current_calendar, target_year, target_month,
                                                            self.school_unit1)
        classes = list(classes_dict.values())
        self.assertEqual(4, len(classes))

        # assert class and subjects
        clazz = classes[0]
        self.assertEqual('VI A', clazz['class_name'])
        self.assertEqual(4, len(clazz['subjects']))
        self._assert_subject('Limba Engleza', 10, 15, clazz['subjects'][0])
        self._assert_subject('Limba Franceza', 10, 15, clazz['subjects'][1])
        self._assert_subject('Limba Romana', 10, 15, clazz['subjects'][2])
        self._assert_subject('Matematica', 10, 15, clazz['subjects'][3])

        # assert class and subjects
        clazz = classes[1]
        self.assertEqual('VI Z', clazz['class_name'])
        self.assertEqual(4, len(clazz['subjects']))
        self._assert_subject('Biologie', 0, 0, clazz['subjects'][0])
        self._assert_subject('Limba Engleza', 0, 0, clazz['subjects'][1])
        self._assert_subject('Limba Romana', 0, 0, clazz['subjects'][2])
        self._assert_subject('Matematica', 0, 0, clazz['subjects'][3])

        # assert class and subjects
        clazz = classes[2]
        self.assertEqual('VII A', clazz['class_name'])
        self.assertEqual(4, len(clazz['subjects']))
        self._assert_subject('Biologie', 0, 0, clazz['subjects'][0])
        self._assert_subject('Limba Engleza', 0, 0, clazz['subjects'][1])
        self._assert_subject('Limba Romana', 0, 0, clazz['subjects'][2])
        self._assert_subject('Matematica', 0, 0, clazz['subjects'][3])

        # assert class and subjects
        clazz = classes[3]
        self.assertEqual('VII Z', clazz['class_name'])
        self.assertEqual(3, len(clazz['subjects']))
        self._assert_subject('Biologie', 40, 50, clazz['subjects'][0])
        self._assert_subject('Fizica', 40, 50, clazz['subjects'][1])
        self._assert_subject('Matematica', 40, 50, clazz['subjects'][2])

    def _assert_subject(self, name, founded_absences, unfounded_absences, subject):
        self.assertEqual(name, subject['subject_name'])
        self.assertEqual(founded_absences, subject['founded_absences'])
        self.assertEqual(unfounded_absences, subject['unfounded_absences'])
