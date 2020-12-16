import datetime
from unittest import skip
from unittest.mock import patch

from dateutil.relativedelta import relativedelta
from ddt import ddt, data
from django.test import TestCase, override_settings
from pytz import utc

from edualert.academic_calendars.factories import AcademicYearCalendarFactory
from edualert.academic_programs.factories import AcademicProgramFactory
from edualert.catalogs.factories import StudentCatalogPerSubjectFactory, SubjectAbsenceFactory
from edualert.catalogs.models import SubjectAbsence
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.statistics.tasks import send_monthly_school_unit_absence_report_task, _compute_report_data_for_school_unit
from edualert.study_classes.factories import StudyClassFactory
from edualert.subjects.factories import SubjectFactory


@ddt
class SendMonthlySchoolUnitAbsenceReportTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # generate subjects
        subject_names = ['Matematica', 'Limba Romana', 'Limba Engleza', 'Limba Franceza', 'Fizica', 'Chimie',
                         'Biologie', 'TIC', 'Educatie Fizica', 'Tehnologii generale in electronica -automatizari(M1)']
        all_subjects = [SubjectFactory(name=i) for i in subject_names]

        # declare helper for easier selection of subjects
        def select_subjects(*args):
            return [s for s in all_subjects if s.name in args]

        cls.current_calendar = AcademicYearCalendarFactory()

        # Generate a new school
        cls.school_unit1 = RegisteredSchoolUnitFactory()
        academic_program1 = AcademicProgramFactory(school_unit=cls.school_unit1)
        cls.unit1_class1 = StudyClassFactory(school_unit=cls.school_unit1, academic_program=academic_program1,
                                             class_grade='VI', class_grade_arabic=6, class_letter='A')
        cls.unit1_class2 = StudyClassFactory(school_unit=cls.school_unit1, academic_program=academic_program1,
                                             class_grade='VII', class_grade_arabic=7, class_letter='Z')

        # Add two more classes to test order
        cls.unit1_class3 = StudyClassFactory(school_unit=cls.school_unit1, academic_program=academic_program1,
                                             class_grade='VI', class_grade_arabic=6, class_letter='Z')
        cls.unit1_class4 = StudyClassFactory(school_unit=cls.school_unit1, academic_program=academic_program1,
                                             class_grade='VII', class_grade_arabic=7, class_letter='A')

        # Add a fifth class; this will not appear in the results since it doesn't have any `StudentCatalogPerSubject`s
        StudyClassFactory(school_unit=cls.school_unit1, academic_program=academic_program1,
                          class_grade='X', class_grade_arabic=10, class_letter='A')

        # generate students and select subjects for the first school and class
        cls.unit1_class1._catalogs = []
        for student in _gen_students(5):
            for subject in select_subjects('Matematica', 'Limba Romana', 'Limba Engleza', 'Limba Franceza'):
                cls.unit1_class1._catalogs.append(StudentCatalogPerSubjectFactory(study_class=cls.unit1_class1, subject=subject, student=student))

        # generate students and select subjects for the first school and second class
        cls.unit1_class2._catalogs = []
        for student in _gen_students(10):
            for subject in select_subjects('Matematica', 'Fizica', 'Tehnologii generale in electronica -automatizari(M1)'):
                cls.unit1_class2._catalogs.append(StudentCatalogPerSubjectFactory(study_class=cls.unit1_class2, subject=subject, student=student))

        # generate students and select subjects for the first school for third and forth class
        for student in _gen_students(5):
            for subject in select_subjects('Matematica', 'Limba Romana', 'Limba Engleza', 'Biologie'):
                StudentCatalogPerSubjectFactory(study_class=cls.unit1_class3, subject=subject, student=student)
                StudentCatalogPerSubjectFactory(study_class=cls.unit1_class4, subject=subject, student=student)

        # Generate a new school
        cls.school_unit2 = RegisteredSchoolUnitFactory()
        academic_program2 = AcademicProgramFactory(school_unit=cls.school_unit2)
        cls.unit2_class1 = StudyClassFactory(school_unit=cls.school_unit2, academic_program=academic_program2,
                                             class_grade='VI', class_letter='A')
        cls.unit2_class2 = StudyClassFactory(school_unit=cls.school_unit2, academic_program=academic_program2,
                                             class_grade='VII', class_letter='Z')

        # generate students and select subjects for the second school and first class
        cls.unit2_class1._catalogs = []
        for student in _gen_students(5):
            for subject in select_subjects('Matematica', 'Limba Romana', 'Limba Engleza', 'TIC'):
                cls.unit2_class1._catalogs.append(StudentCatalogPerSubjectFactory(study_class=cls.unit2_class1, subject=subject, student=student))

        # generate students and select subjects for the second school and class
        cls.unit2_class2._catalogs = []
        for student in _gen_students(5):
            for subject in select_subjects('Matematica', 'Fizica', 'Chimie', 'Educatie Fizica'):
                cls.unit2_class2._catalogs.append(StudentCatalogPerSubjectFactory(study_class=cls.unit2_class2, subject=subject, student=student))

    @skip('Used only for manually testing the task')
    @data(
        datetime.datetime(2019, 10, 11).replace(tzinfo=utc),
        datetime.datetime(2019, 11, 11).replace(tzinfo=utc),
        datetime.datetime(2019, 12, 11).replace(tzinfo=utc),
        datetime.datetime(2020, 1, 11).replace(tzinfo=utc),
        datetime.datetime(2020, 2, 11).replace(tzinfo=utc),
        datetime.datetime(2020, 3, 11).replace(tzinfo=utc),
        datetime.datetime(2020, 4, 11).replace(tzinfo=utc),
        datetime.datetime(2020, 5, 11).replace(tzinfo=utc),
        datetime.datetime(2020, 6, 11).replace(tzinfo=utc),
        datetime.datetime(2020, 7, 11).replace(tzinfo=utc),
        datetime.datetime(2020, 8, 11).replace(tzinfo=utc),
        datetime.datetime(2020, 9, 11).replace(tzinfo=utc),
    )
    def test_send_monthly_school_unit_absence_report_task(self, current_date):
        # set the empty values based on Django's email settings
        email_host = ''
        email_host_user = ''
        email_host_password = ''
        email_port = 587
        email_backend = 'django.core.mail.backends.smtp.EmailBackend'
        # set email address for the sender and the email address where
        # the reports should be sent
        from_email = ''
        to_emails = []
        principal_email_format = ''

        reported_date = current_date - relativedelta(months=1)

        # update the email for the school principals
        for index, principal in enumerate(UserProfile.objects.filter(user_role=UserProfile.UserRoles.PRINCIPAL)):
            principal.email = principal_email_format.format(index)
            principal.save()

        # only generate absences for the months in the current calendar
        if reported_date.year == 2019 or reported_date.month < 7:
            self._generate_school_units_absences(reported_date, current_date)

        # setup SMTP credentials and send emails
        with override_settings(EMAIL_HOST=email_host, EMAIL_PORT=email_port, EMAIL_HOST_USER=email_host_user,
                               EMAIL_HOST_PASSWORD=email_host_password, EMAIL_BACKEND=email_backend, EMAIL_USE_TLS=True,
                               SERVER_EMAIL=from_email, ABSENCES_REPORT_DELIVERY_EMAILS=to_emails):
            with patch('django.utils.timezone.now', return_value=current_date):
                send_monthly_school_unit_absence_report_task()

    def test__compute_report_data_for_school_unit(self):
        current_date = datetime.datetime(2019, 11, 11).replace(tzinfo=utc)
        reported_date = current_date - relativedelta(months=1)
        self._generate_school_units_absences(reported_date, current_date)

        classes_dict = _compute_report_data_for_school_unit(self.current_calendar.academic_year, reported_date,
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
        self._assert_subject('Fizica', 40, 50, clazz['subjects'][0])
        self._assert_subject('Matematica', 40, 50, clazz['subjects'][1])
        self._assert_subject('Tehnologii generale in electronica -automatizari(M1)', 40, 50, clazz['subjects'][2])

    def _generate_school_units_absences(self, report_date, today):
        absences = []

        for catalog_per_subject in self.unit1_class1._catalogs:
            absences.extend(_build_absences(catalog_per_subject, report_date, today, 2, 3))
        for catalog_per_subject in self.unit1_class2._catalogs:
            absences.extend(_build_absences(catalog_per_subject, report_date, today, 4, 5))

        for catalog_per_subject in self.unit2_class1._catalogs:
            absences.extend(_build_absences(catalog_per_subject, report_date, today, 6, 7))
        for catalog_per_subject in self.unit2_class2._catalogs:
            absences.extend(_build_absences(catalog_per_subject, report_date, today, 8, 9))

        SubjectAbsence.objects.bulk_create(absences)

    def _assert_subject(self, name, founded_absences, unfounded_absences, subject):
        self.assertEqual(name, subject['subject_name'])
        self.assertEqual(founded_absences, subject['founded_absences'])
        self.assertEqual(unfounded_absences, subject['unfounded_absences'])


def _gen_students(count):
    return UserProfileFactory.create_batch(count, user_role=UserProfile.UserRoles.STUDENT)


# declare a helper function to generate absences
def _build_absences(catalog_per_subject, target_date, current_date, founded_absences, unfounded_absences):
    year = current_date.year
    month = current_date.month
    target_year = target_date.year
    target_month = target_date.month
    absences = []

    # build absences for the current date as well to make sure all those for the target date are considered
    absences.extend(SubjectAbsenceFactory.build_batch(unfounded_absences, catalog_per_subject=catalog_per_subject,
                                                      student=catalog_per_subject.student,
                                                      taken_at=datetime.date(target_year, target_month, 1)))
    absences.extend(SubjectAbsenceFactory.build_batch(unfounded_absences, catalog_per_subject=catalog_per_subject,
                                                      student=catalog_per_subject.student,
                                                      taken_at=datetime.date(year, month, 1)))

    absences.extend(SubjectAbsenceFactory.build_batch(founded_absences, catalog_per_subject=catalog_per_subject,
                                                      student=catalog_per_subject.student, is_founded=True,
                                                      taken_at=datetime.date(target_year, target_month, 1)))
    absences.extend(SubjectAbsenceFactory.build_batch(founded_absences, catalog_per_subject=catalog_per_subject,
                                                      student=catalog_per_subject.student, is_founded=True,
                                                      taken_at=datetime.date(year, month, 1)))
    return absences
