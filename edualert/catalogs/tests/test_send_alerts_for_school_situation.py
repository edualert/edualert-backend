import datetime
from unittest.mock import patch, call

from django.utils import timezone

from edualert.catalogs.factories import StudentCatalogPerSubjectFactory, SubjectAbsenceFactory, SubjectGradeFactory
from edualert.catalogs.models import SubjectGrade
from edualert.catalogs.utils.school_situation_alerts import get_time_period, get_unfounded_absences_count_for_student, \
    get_grades_for_students, get_parents_contact, group_grades_by_subject, get_subject_initials, get_formatted_grades, \
    get_student_initials, send_alerts_for_school_situation
from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.study_classes.factories import StudyClassFactory
from edualert.subjects.factories import SubjectFactory


class SendAlertsForSchoolSituation(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.starts_at = datetime.date(2020, 10, 21)
        cls.ends_at = datetime.date(2020, 10, 27)

        cls.school = RegisteredSchoolUnitFactory()
        cls.study_class = StudyClassFactory(school_unit=cls.school)
        cls.student = UserProfileFactory(school_unit=cls.school, user_role=UserProfile.UserRoles.STUDENT,
                                         student_in_class=cls.study_class, full_name="Pop Ionut")

        cls.subject1 = SubjectFactory(name='Limba Romana')
        cls.subject2 = SubjectFactory(name='Matematica')

        cls.catalog1 = StudentCatalogPerSubjectFactory(student=cls.student, study_class=cls.study_class, subject=cls.subject1)
        cls.catalog2 = StudentCatalogPerSubjectFactory(student=cls.student, study_class=cls.study_class, subject=cls.subject2)

    def test_get_time_period(self):
        self.assertEqual(get_time_period(self.starts_at, self.ends_at), "21-27.10")
        self.assertEqual(get_time_period(datetime.date(2020, 10, 28), datetime.date(2020, 11, 2)), "28.10-2.11")

    def test_get_unfounded_absences_count_for_student(self):
        self.assertEqual(get_unfounded_absences_count_for_student(self.student.id, self.starts_at, self.ends_at), 0)

        SubjectAbsenceFactory(student=self.student, catalog_per_subject=self.catalog1, taken_at=self.starts_at - timezone.timedelta(days=1))
        SubjectAbsenceFactory(student=self.student, catalog_per_subject=self.catalog1, taken_at=self.starts_at)
        SubjectAbsenceFactory(student=self.student, catalog_per_subject=self.catalog1, taken_at=self.starts_at + timezone.timedelta(days=1), is_founded=True)
        SubjectAbsenceFactory(student=self.student, catalog_per_subject=self.catalog2, taken_at=self.ends_at - timezone.timedelta(days=1))
        SubjectAbsenceFactory(student=self.student, catalog_per_subject=self.catalog2, taken_at=self.ends_at)
        SubjectAbsenceFactory(student=self.student, catalog_per_subject=self.catalog2, taken_at=self.ends_at + timezone.timedelta(days=1))

        self.assertEqual(get_unfounded_absences_count_for_student(self.student.id, self.starts_at, self.ends_at), 3)

    def test_get_grades_for_students(self):
        self.assertEqual(get_grades_for_students(self.student.id, self.starts_at, self.ends_at).count(), 0)

        SubjectGradeFactory(student=self.student, catalog_per_subject=self.catalog1, taken_at=self.starts_at - timezone.timedelta(days=1))
        SubjectGradeFactory(student=self.student, catalog_per_subject=self.catalog1, taken_at=self.starts_at)
        SubjectGradeFactory(student=self.student, catalog_per_subject=self.catalog1, taken_at=self.starts_at + timezone.timedelta(days=1))
        SubjectGradeFactory(student=self.student, catalog_per_subject=self.catalog2, taken_at=self.ends_at - timezone.timedelta(days=1))
        SubjectGradeFactory(student=self.student, catalog_per_subject=self.catalog2, taken_at=self.ends_at)
        SubjectGradeFactory(student=self.student, catalog_per_subject=self.catalog2, taken_at=self.ends_at + timezone.timedelta(days=1))

        self.assertEqual(get_grades_for_students(self.student.id, self.starts_at, self.ends_at).count(), 4)

    def test_get_parents_contact(self):
        self.assertCountEqual(get_parents_contact(self.student), ([], []))

        # has email and email_notifications_enabled = true
        parent1 = UserProfileFactory(school_unit=self.school, user_role=UserProfile.UserRoles.PARENT)
        # has both email and phone, email_notifications_enabled = false, sms_notifications_enabled = true
        parent2 = UserProfileFactory(school_unit=self.school, user_role=UserProfile.UserRoles.PARENT,
                                     email_notifications_enabled=False, sms_notifications_enabled=True)
        # has both email and phone, both notifications off
        parent3 = UserProfileFactory(school_unit=self.school, user_role=UserProfile.UserRoles.PARENT,
                                     email_notifications_enabled=False, sms_notifications_enabled=False)
        self.student.parents.add(parent1, parent2, parent3)

        self.assertCountEqual(get_parents_contact(self.student), ([parent1], [parent2]))

    def test_group_grades_by_subject(self):
        self.assertEqual(group_grades_by_subject(SubjectGrade.objects.none()), {})

        SubjectGradeFactory(student=self.student, catalog_per_subject=self.catalog1, grade=7)
        SubjectGradeFactory(student=self.student, catalog_per_subject=self.catalog1, grade=8)
        SubjectGradeFactory(student=self.student, catalog_per_subject=self.catalog1, grade=9)
        SubjectGradeFactory(student=self.student, catalog_per_subject=self.catalog2, grade=10)

        self.assertCountEqual(group_grades_by_subject(SubjectGrade.objects.filter(student_id=self.student.id)), {
            self.subject1.name: ["7", "8", "9"],
            self.subject2.name: ["10", ]
        })

    def test_get_subject_initials(self):
        self.assertEqual(get_subject_initials(""), "")
        self.assertEqual(get_subject_initials("Matematica"), "MAT")
        self.assertEqual(get_subject_initials("FE"), "FE")
        self.assertEqual(get_subject_initials("Limba Romana"), "LRO")
        self.assertEqual(get_subject_initials("Modele Machete Constructii"), "MMC")
        self.assertEqual(get_subject_initials("Modele Machete Constructii Desen"), "MMC")

    def test_get_formatted_grades(self):
        self.assertEqual(get_formatted_grades({}), "")

        SubjectGradeFactory(student=self.student, catalog_per_subject=self.catalog1, grade=7)
        SubjectGradeFactory(student=self.student, catalog_per_subject=self.catalog1, grade=8)
        SubjectGradeFactory(student=self.student, catalog_per_subject=self.catalog1, grade=9)
        SubjectGradeFactory(student=self.student, catalog_per_subject=self.catalog2, grade=10)

        grouped_subjects = group_grades_by_subject(SubjectGrade.objects.filter(student_id=self.student.id))

        self.assertEqual(get_formatted_grades(grouped_subjects), "Matematica 10, Limba Romana 9 ; 8 ; 7")
        self.assertEqual(get_formatted_grades(grouped_subjects, True), "MAT 10, LRO 9 ; 8 ; 7")

    def test_get_student_initials(self):
        self.assertEqual(get_student_initials(""), "")
        self.assertEqual(get_student_initials("Pop Marius Vasile"), "PMV")
        self.assertEqual(get_student_initials("Pop IC Marius"), "PIM")
        self.assertEqual(get_student_initials("Pop I.C. Marius"), "PIM")
        self.assertEqual(get_student_initials("Pop I.C. Marius-Vasile"), "PIM")
        self.assertEqual(get_student_initials("Pop I.C. Marius Vasile"), "PIMV")

    @patch('edualert.catalogs.utils.school_situation_alerts.format_and_send_school_situation_email')
    @patch('edualert.catalogs.utils.school_situation_alerts.format_and_send_school_situation_sms')
    def test_send_alerts(self, send_sms_mock, send_email_mock):
        today = timezone.now().date()
        ten_days_ago = today - timezone.timedelta(days=10)

        # add one more student from a different school
        school2 = RegisteredSchoolUnitFactory()
        study_class2 = StudyClassFactory(school_unit=school2)
        student2 = UserProfileFactory(school_unit=school2, user_role=UserProfile.UserRoles.STUDENT,
                                      student_in_class=study_class2, full_name="Marinescu I. Ioan")
        catalog3 = StudentCatalogPerSubjectFactory(student=student2, study_class=study_class2, subject=self.subject1)

        # add 1 unfounded absence for 1st student
        SubjectAbsenceFactory(student=self.student, catalog_per_subject=self.catalog1, taken_at=ten_days_ago)
        # add grades for both of them
        SubjectGradeFactory(student=self.student, catalog_per_subject=self.catalog1, taken_at=ten_days_ago, grade=6)
        SubjectGradeFactory(student=self.student, catalog_per_subject=self.catalog1, taken_at=ten_days_ago, grade=7)
        SubjectGradeFactory(student=self.student, catalog_per_subject=self.catalog2, taken_at=ten_days_ago, grade=5)
        SubjectGradeFactory(student=student2, catalog_per_subject=catalog3, taken_at=ten_days_ago, grade=10)

        # add 2 parents for each, one allowing emails, one allowing sms
        parent1 = UserProfileFactory(school_unit=self.school, user_role=UserProfile.UserRoles.PARENT)
        parent2 = UserProfileFactory(school_unit=self.school, user_role=UserProfile.UserRoles.PARENT,
                                     email_notifications_enabled=False, sms_notifications_enabled=True)
        parent3 = UserProfileFactory(school_unit=school2, user_role=UserProfile.UserRoles.PARENT)
        parent4 = UserProfileFactory(school_unit=school2, user_role=UserProfile.UserRoles.PARENT,
                                     email_notifications_enabled=False, sms_notifications_enabled=True)
        self.student.parents.add(parent1, parent2)
        student2.parents.add(parent3, parent4)

        # call tested function
        send_alerts_for_school_situation()

        two_weeks_ago = today - timezone.timedelta(days=14)
        one_week_ago = today - timezone.timedelta(days=8)
        time_period = get_time_period(two_weeks_ago, one_week_ago)

        # check mocked calls
        send_email_calls = [call("Marinescu I. Ioan", time_period, "Limba Romana 10", 0, school2.name, [parent3]),
                            call("Pop Ionut", time_period, "Matematica 5, Limba Romana 7 ; 6", 1, self.school.name, [parent1])]
        send_email_mock.assert_has_calls(send_email_calls, any_order=True)

        send_sms_calls = [call("MII", time_period, "LRO 10", 0, [parent4]),
                          call("PI", time_period, "MAT 5, LRO 7 ; 6", 1, [parent2])]
        send_sms_mock.assert_has_calls(send_sms_calls, any_order=True)
