import datetime
from unittest import skip

from dateutil.relativedelta import relativedelta
from django.test import TestCase, override_settings
from django.utils import timezone

from edualert.academic_programs.factories import AcademicProgramFactory
from edualert.catalogs.factories import StudentCatalogPerSubjectFactory, SubjectAbsenceFactory
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.statistics.tasks import send_monthly_school_unit_absence_report_task
from edualert.study_classes.factories import StudyClassFactory
from edualert.subjects.factories import SubjectFactory


class SendMonthlySchoolUnitAbsenceReportTestCase(TestCase):
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
        send_to_email = ''

        today = timezone.now().date()
        year = today.year
        month = today.month
        report_date = today - relativedelta(months=1)
        target_year = report_date.year
        target_month = report_date.month

        # Generate two school units with two classes each and some students with absences
        school_unit1 = RegisteredSchoolUnitFactory(email=send_to_email)
        academic_program1 = AcademicProgramFactory(school_unit=school_unit1)
        study_class1 = StudyClassFactory(school_unit=school_unit1, academic_program=academic_program1)
        study_class2 = StudyClassFactory(school_unit=school_unit1, academic_program=academic_program1, class_grade='VII', class_letter='Z')

        # declare a helper function to generate absences
        def gen_absences(catalog_per_subject, founded_absences, unfounded_absences):
            for i in range(0, unfounded_absences):
                SubjectAbsenceFactory(catalog_per_subject=catalog_per_subject, student=catalog_per_subject.student, taken_at=datetime.date(target_year, target_month, 1))
                SubjectAbsenceFactory(catalog_per_subject=catalog_per_subject, student=catalog_per_subject.student, taken_at=datetime.date(year, month, 1))
            for i in range(0, founded_absences):
                SubjectAbsenceFactory(catalog_per_subject=catalog_per_subject, student=catalog_per_subject.student, is_founded=True, taken_at=datetime.date(target_year, target_month, 1))
                SubjectAbsenceFactory(catalog_per_subject=catalog_per_subject, student=catalog_per_subject.student, is_founded=True, taken_at=datetime.date(year, month, 1))

        for subject_name in ['Limba Romana', 'Limba Engleza', 'Limba Franceza', 'Matematica', 'Fizica', 'Chimie',
                             'Biologie', 'Istorie', 'Geografie', 'Logica, argumentare si comunicare', 'Religie']:
            subject = SubjectFactory(name=subject_name)

            for i in range(0, 10):
                catalog_per_subject = StudentCatalogPerSubjectFactory(study_class=study_class1, subject=subject)
                gen_absences(catalog_per_subject, 2, 3)
            for i in range(0, 20):
                catalog_per_subject = StudentCatalogPerSubjectFactory(study_class=study_class2, subject=subject)
                gen_absences(catalog_per_subject, 4, 5)

        school_unit2 = RegisteredSchoolUnitFactory(email=send_to_email)
        academic_program2 = AcademicProgramFactory(school_unit=school_unit2)
        study_class3 = StudyClassFactory(school_unit=school_unit2, academic_program=academic_program2)
        study_class4 = StudyClassFactory(school_unit=school_unit2, academic_program=academic_program2, class_grade='VII', class_letter='Z')
        for subject_name in ['TIC', 'Educatie Fizica', 'Tehnologii generale in electronica -automatizari(M1)',
                             'Electrotehnica si masurari tehnice(M2)', 'Elemente de mecanica (M3)', 'Dirigentie']:
            subject = SubjectFactory(name=subject_name)
            for i in range(0, 10):
                catalog_per_subject = StudentCatalogPerSubjectFactory(study_class=study_class3, subject=subject)
                gen_absences(catalog_per_subject, 6, 7)
            for i in range(0, 20):
                catalog_per_subject = StudentCatalogPerSubjectFactory(study_class=study_class4, subject=subject)
                gen_absences(catalog_per_subject, 8, 9)

        # setup SMTP credentials and send emails
        with override_settings(EMAIL_HOST=email_host, EMAIL_PORT=email_port, EMAIL_HOST_USER=email_host_user,
                               EMAIL_HOST_PASSWORD=email_host_password, EMAIL_BACKEND=email_backend, EMAIL_USE_TLS=True,
                               SERVER_EMAIL=from_email):
            send_monthly_school_unit_absence_report_task()
