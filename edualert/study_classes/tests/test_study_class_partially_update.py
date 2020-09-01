from ddt import data, ddt
from django.urls import reverse
from rest_framework import status

from edualert.academic_calendars.factories import AcademicYearCalendarFactory
from edualert.academic_programs.factories import AcademicProgramFactory
from edualert.catalogs.factories import StudentCatalogPerYearFactory, StudentCatalogPerSubjectFactory, \
    SubjectGradeFactory, SubjectAbsenceFactory, ExaminationGradeFactory
from edualert.catalogs.models import StudentCatalogPerYear, StudentCatalogPerSubject, SubjectGrade
from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.constants import TRANSFERRED_LABEL
from edualert.profiles.factories import UserProfileFactory, LabelFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.study_classes.factories import StudyClassFactory, TeacherClassThroughFactory
from edualert.subjects.factories import SubjectFactory, ProgramSubjectThroughFactory


@ddt
class StudyClassPartiallyUpdateTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.principal = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL)
        cls.school_unit = RegisteredSchoolUnitFactory(school_principal=cls.principal)

        cls.calendar = AcademicYearCalendarFactory()

        cls.subject1 = SubjectFactory()
        cls.subject2 = SubjectFactory()
        cls.coordination_subject = SubjectFactory(is_coordination=True)

        cls.academic_program = AcademicProgramFactory(school_unit=cls.school_unit)
        ProgramSubjectThroughFactory(generic_academic_program=cls.academic_program.generic_academic_program,
                                     subject=cls.subject1, class_grade='X', class_grade_arabic=10)
        ProgramSubjectThroughFactory(academic_program=cls.academic_program, subject=cls.subject2,
                                     is_mandatory=False, class_grade='X', class_grade_arabic=10)

        cls.teacher1 = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=cls.school_unit)
        cls.teacher2 = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=cls.school_unit)
        cls.teacher1.taught_subjects.add(cls.subject1)
        cls.teacher2.taught_subjects.add(cls.subject1)

        cls.study_class = StudyClassFactory(school_unit=cls.school_unit, class_master=cls.teacher1, academic_program=cls.academic_program,
                                            class_grade='X', class_grade_arabic=10, class_letter='A')

        cls.student1 = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=cls.school_unit, student_in_class=cls.study_class)
        StudentCatalogPerYearFactory(student=cls.student1, study_class=cls.study_class)
        cls.student2 = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=cls.school_unit, student_in_class=cls.study_class)
        StudentCatalogPerYearFactory(student=cls.student2, study_class=cls.study_class)

        cls.new_student = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=cls.school_unit)

    @staticmethod
    def build_url(study_class_id):
        return reverse('study_classes:study-class-detail', kwargs={'id': study_class_id})

    def setUp(self):
        self.teacher_class_through1 = TeacherClassThroughFactory(study_class=self.study_class, teacher=self.teacher1,
                                                                 subject=self.coordination_subject, is_class_master=True)
        self.teacher_class_through2 = TeacherClassThroughFactory(study_class=self.study_class, teacher=self.teacher1, subject=self.subject1,
                                                                 is_class_master=True)
        self.teacher_class_through3 = TeacherClassThroughFactory(study_class=self.study_class, teacher=self.teacher2, subject=self.subject2,
                                                                 is_class_master=False, is_optional_subject=True)

        self.subject_catalog1 = StudentCatalogPerSubjectFactory(student=self.student1, teacher=self.teacher1,
                                                                study_class=self.study_class, subject=self.coordination_subject)
        self.subject_catalog2 = StudentCatalogPerSubjectFactory(student=self.student1, teacher=self.teacher1,
                                                                study_class=self.study_class, subject=self.subject1)
        self.subject_catalog3 = StudentCatalogPerSubjectFactory(student=self.student1, teacher=self.teacher2,
                                                                study_class=self.study_class, subject=self.subject2)
        self.subject_catalog4 = StudentCatalogPerSubjectFactory(student=self.student2, teacher=self.teacher1,
                                                                study_class=self.study_class, subject=self.coordination_subject)
        self.subject_catalog5 = StudentCatalogPerSubjectFactory(student=self.student2, teacher=self.teacher1,
                                                                study_class=self.study_class, subject=self.subject1)
        self.subject_catalog6 = StudentCatalogPerSubjectFactory(student=self.student2, teacher=self.teacher2,
                                                                study_class=self.study_class, subject=self.subject2)

        self.request_data = {
            "class_master": self.teacher2.id,
            "updated_teachers": [
                {
                    "id": self.teacher_class_through2.id,
                    "teacher": self.teacher2.id,
                },
                {
                    "id": self.teacher_class_through3.id,
                    "teacher": self.teacher1.id,
                }
            ],
            "new_students": [
                self.new_student.id
            ],
            "deleted_students": [
                self.student2.id
            ]
        }

    def test_study_class_partially_update_unauthenticated(self):
        url = self.build_url(self.study_class.id)
        response = self.client.patch(url, self.request_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.TEACHER,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_study_class_partially_update_wrong_user_type(self, user_role):
        user = UserProfileFactory(
            user_role=user_role,
            school_unit=RegisteredSchoolUnitFactory() if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )
        self.client.login(username=user.username, password='passwd')

        url = self.build_url(self.study_class.id)
        response = self.client.patch(url, self.request_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_study_class_partially_update_not_found(self):
        self.client.login(username=self.principal.username, password='passwd')

        url = self.build_url(0)
        response = self.client.patch(url, self.request_data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_study_class_partially_update_no_calendar(self):
        self.client.login(username=self.principal.username, password='passwd')
        self.calendar.delete()

        url = self.build_url(self.study_class.id)
        response = self.client.patch(url, self.request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], 'No academic calendar defined.')

    def test_study_class_partially_update_different_year(self):
        self.client.login(username=self.principal.username, password='passwd')
        self.study_class.academic_year = 2010
        self.study_class.save()

        url = self.build_url(self.study_class.id)
        response = self.client.patch(url, self.request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], 'Cannot update a study class from a previous year.')

    def test_study_class_partially_update_validate_class_master(self):
        self.client.login(username=self.principal.username, password='passwd')
        url = self.build_url(self.study_class.id)

        # Not a teacher
        profile1 = UserProfileFactory(user_role=UserProfile.UserRoles.PARENT, school_unit=self.school_unit)
        # From a different school
        profile2 = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=RegisteredSchoolUnitFactory())
        # Already a class master
        profile3 = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=self.school_unit)
        StudyClassFactory(school_unit=self.school_unit, class_master=profile3, class_letter='B')
        # Inactive teacher
        profile4 = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=self.school_unit, is_active=False)

        for profile in [profile1, profile2, profile3, profile4]:
            self.request_data['class_master'] = profile.id

            response = self.client.patch(url, self.request_data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data['class_master'], ['Invalid user.'])

        self.request_data['class_master'] = 0

        response = self.client.patch(url, self.request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['class_master'], ['Invalid pk "0" - object does not exist.'])

    def test_study_class_partially_update_validate_teachers(self):
        self.client.login(username=self.principal.username, password='passwd')
        url = self.build_url(self.study_class.id)

        # Wrong teacher class through id
        for obj_id in [0, TeacherClassThroughFactory().id, self.teacher_class_through1.id]:
            self.request_data['updated_teachers'] = [
                {
                    'id': obj_id,
                    'teacher': self.teacher2.id
                }
            ]
            response = self.client.patch(url, self.request_data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data['updated_teachers'], [f'Invalid pk "{obj_id}" - object does not exist.'])

        # Not a teacher
        profile1 = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=self.school_unit)
        # Another school unit
        profile2 = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=RegisteredSchoolUnitFactory())
        # Inactive teacher
        profile3 = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=self.school_unit, is_active=False)

        for profile in [profile1, profile2, profile3]:
            self.request_data['updated_teachers'] = [
                {
                    'id': self.teacher_class_through3.id,
                    'teacher': profile.id
                }
            ]

            response = self.client.patch(url, self.request_data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data['updated_teachers'], ['At least one teacher is invalid.'])

        # User not found
        self.request_data['updated_teachers'] = [
            {
                'id': self.teacher_class_through3.id,
                'teacher': 0
            }
        ]

        response = self.client.patch(url, self.request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['updated_teachers'][0]['teacher'], ['Invalid pk "0" - object does not exist.'])

        # Subject not in teacher's taught subjects
        teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=self.school_unit)
        self.request_data['updated_teachers'] = [
            {
                'id': self.teacher_class_through2.id,
                'teacher': teacher.id
            }
        ]

        response = self.client.patch(url, self.request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['updated_teachers'], ['Teacher {} does not teach {}.'
                         .format(teacher.full_name, self.subject1.name)])

        primary_study_class = StudyClassFactory(school_unit=self.school_unit, class_grade='I', class_grade_arabic=1)
        teacher_class_through = TeacherClassThroughFactory(study_class=primary_study_class, teacher=primary_study_class.class_master, is_class_master=True)
        url = self.build_url(primary_study_class.id)
        request_data = {
            'updated_teachers': [
                {
                    'id': teacher_class_through.id,
                    'teacher': teacher.id
                }
            ]
        }

        response = self.client.patch(url, request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['updated_teachers'], ['Teacher {} does not teach {}.'
                         .format(teacher.full_name, teacher_class_through.subject_name)])

    def test_study_class_partially_update_validate_new_students(self):
        self.client.login(username=self.principal.username, password='passwd')
        url = self.build_url(self.study_class.id)

        # Not a student
        profile1 = UserProfileFactory(user_role=UserProfile.UserRoles.PARENT, school_unit=self.school_unit)
        # Inactive student
        profile2 = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=self.school_unit, is_active=False)

        for profile_id in [profile1.id, profile2.id, 0]:
            self.request_data['new_students'] = [profile_id, ]

            response = self.client.patch(url, self.request_data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data['new_students'], [f'Invalid pk "{profile_id}" - object does not exist.'])

        # From a different school
        profile1 = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=RegisteredSchoolUnitFactory())
        # Already in a study class
        study_class = StudyClassFactory(school_unit=self.school_unit, class_letter='B')
        profile2 = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=self.school_unit, student_in_class=study_class)

        for profile_id in [profile1.id, profile2.id]:
            self.request_data['new_students'] = [profile_id, ]

            response = self.client.patch(url, self.request_data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data['new_students'], ['At least one student is invalid.'])

    def test_study_class_partially_update_validate_deleted_students(self):
        self.client.login(username=self.principal.username, password='passwd')
        url = self.build_url(self.study_class.id)

        # Not a student
        profile1 = UserProfileFactory(user_role=UserProfile.UserRoles.PARENT, school_unit=self.school_unit)
        # Inactive student
        profile2 = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=self.school_unit, is_active=False)

        for profile_id in [profile1.id, profile2.id, 0]:
            self.request_data['deleted_students'] = [profile_id, ]

            response = self.client.patch(url, self.request_data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data['deleted_students'], [f'Invalid pk "{profile_id}" - object does not exist.'])

        # From a different study class
        study_class = StudyClassFactory(school_unit=self.school_unit, class_letter='B')
        profile = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=self.school_unit, student_in_class=study_class)
        self.request_data['deleted_students'] = [profile.id, ]

        response = self.client.patch(url, self.request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['deleted_students'], ['At least one student is invalid.'])

    def test_study_class_partially_update_no_data(self):
        self.client.login(username=self.principal.username, password='passwd')

        study_class = StudyClassFactory(school_unit=self.school_unit)
        url = self.build_url(study_class.id)

        response = self.client.patch(url, data={})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_study_class_partially_update_just_class_master(self):
        self.client.login(username=self.principal.username, password='passwd')
        url = self.build_url(self.study_class.id)

        request_data = {
            "class_master": self.teacher2.id
        }

        response = self.client.patch(url, request_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.refresh_objects_from_db([self.study_class, self.teacher_class_through1, self.teacher_class_through2,
                                      self.teacher_class_through3, self.subject_catalog1, self.subject_catalog4])
        self.assertEqual(self.study_class.class_master, self.teacher2)
        self.assertEqual(self.teacher_class_through1.teacher, self.teacher2)

        self.assertTrue(self.teacher_class_through1.is_class_master)
        self.assertFalse(self.teacher_class_through2.is_class_master)
        self.assertTrue(self.teacher_class_through3.is_class_master)

        self.assertEqual(self.subject_catalog1.teacher, self.teacher2)
        self.assertEqual(self.subject_catalog4.teacher, self.teacher2)

    def test_study_class_partially_update_just_teachers(self):
        self.client.login(username=self.principal.username, password='passwd')
        url = self.build_url(self.study_class.id)

        request_data = {
            "updated_teachers": [
                {
                    "id": self.teacher_class_through2.id,
                    "teacher": self.teacher2.id,
                },
                {
                    "id": self.teacher_class_through3.id,
                    "teacher": self.teacher1.id,
                }
            ]
        }

        response = self.client.patch(url, request_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.refresh_objects_from_db([self.study_class, self.teacher_class_through1, self.teacher_class_through2, self.teacher_class_through3,
                                      self.subject_catalog2, self.subject_catalog3, self.subject_catalog5, self.subject_catalog6])
        self.assertEqual(self.study_class.class_master, self.teacher1)
        self.assertEqual(self.teacher_class_through1.teacher, self.teacher1)
        self.assertTrue(self.teacher_class_through1.is_class_master)

        self.assertEqual(self.teacher_class_through2.teacher, self.teacher2)
        self.assertFalse(self.teacher_class_through2.is_class_master)
        self.assertEqual(self.subject_catalog2.teacher, self.teacher2)
        self.assertEqual(self.subject_catalog5.teacher, self.teacher2)

        self.assertEqual(self.teacher_class_through3.teacher, self.teacher1)
        self.assertTrue(self.teacher_class_through3.is_class_master)
        self.assertEqual(self.subject_catalog3.teacher, self.teacher1)
        self.assertEqual(self.subject_catalog6.teacher, self.teacher1)

    def test_study_class_partially_update_success(self):
        self.client.login(username=self.principal.username, password='passwd')

        expected_fields = ['id', 'class_grade', 'class_letter', 'academic_year', 'academic_program', 'academic_program_name',
                           'class_master', 'teachers_class_through', 'students', 'has_previous_catalog_data']

        url = self.build_url(self.study_class.id)
        response = self.client.patch(url, self.request_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(response.data.keys(), expected_fields)

        self.refresh_objects_from_db([self.study_class, self.teacher_class_through1, self.teacher_class_through2,
                                      self.teacher_class_through3, self.subject_catalog1, self.subject_catalog2,
                                      self.subject_catalog3, self.student2, self.new_student])
        self.assertEqual(self.study_class.class_master, self.teacher2)
        self.assertEqual(self.teacher_class_through1.teacher, self.teacher2)
        self.assertTrue(self.teacher_class_through1.is_class_master)
        self.assertEqual(self.subject_catalog1.teacher, self.teacher2)

        self.assertEqual(self.teacher_class_through2.teacher, self.teacher2)
        self.assertTrue(self.teacher_class_through2.is_class_master)
        self.assertEqual(self.subject_catalog2.teacher, self.teacher2)

        self.assertEqual(self.teacher_class_through3.teacher, self.teacher1)
        self.assertFalse(self.teacher_class_through3.is_class_master)
        self.assertEqual(self.subject_catalog3.teacher, self.teacher1)

        self.assertFalse(StudentCatalogPerYear.objects.filter(student=self.student2, study_class=self.study_class).exists())
        self.assertFalse(StudentCatalogPerSubject.objects.filter(student=self.student2, study_class=self.study_class).exists())
        self.assertIsNone(self.student2.student_in_class)

        self.assertEqual(self.new_student.student_in_class, self.study_class)
        catalog_per_year = StudentCatalogPerYear.objects.filter(student=self.new_student, study_class=self.study_class).first()
        self.assertIsNotNone(catalog_per_year)
        self.assertEqual(catalog_per_year.behavior_grade_sem1, 10)
        self.assertEqual(catalog_per_year.behavior_grade_sem2, 10)
        self.assertEqual(catalog_per_year.behavior_grade_annual, 10)

        for (subject, is_enrolled, teacher) in zip([self.coordination_subject, self.subject1, self.subject2], [True, True, False],
                                                   [self.teacher2, self.teacher2, self.teacher1]):
            self.assertTrue(StudentCatalogPerSubject.objects.filter(student=self.new_student, teacher=teacher,
                                                                    subject=subject, is_enrolled=is_enrolled).exists())
        coordination_catalog = StudentCatalogPerSubject.objects.filter(student=self.new_student, teacher=self.teacher2,
                                                                       subject=self.coordination_subject, is_enrolled=True).first()
        self.assertIsNotNone(coordination_catalog)
        self.assertTrue(SubjectGrade.objects.filter(catalog_per_subject=coordination_catalog, student=self.new_student, semester=1, grade=10).exists())
        self.assertTrue(SubjectGrade.objects.filter(catalog_per_subject=coordination_catalog, student=self.new_student, semester=2, grade=10).exists())

    def test_study_class_partially_update_teachers_primary_school(self):
        self.client.login(username=self.principal.username, password='passwd')

        primary_study_class = StudyClassFactory(school_unit=self.school_unit, class_grade='I', class_grade_arabic=1)
        class_master = primary_study_class.class_master
        TeacherClassThroughFactory(study_class=primary_study_class, teacher=class_master, is_class_master=True)

        teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=self.school_unit)
        subject = SubjectFactory()
        teacher.taught_subjects.add(subject)
        teacher_class_through = TeacherClassThroughFactory(study_class=primary_study_class, teacher=teacher, is_class_master=False)

        url = self.build_url(primary_study_class.id)
        request_data = {
            'updated_teachers': [
                {
                    'id': teacher_class_through.id,
                    'teacher': class_master.id
                }
            ]
        }

        # This is allowed even if the teacher doesn't have the subject in taught subjects list
        # (because the teacher is the class master)
        response = self.client.patch(url, request_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        teacher_class_through.refresh_from_db()
        self.assertEqual(teacher_class_through.teacher, class_master)
        self.assertTrue(teacher_class_through.is_class_master)

    def test_study_class_partially_update_move_student_from_different_school(self):
        self.client.login(username=self.principal.username, password='passwd')

        self.new_student.labels.add(
            LabelFactory(text=TRANSFERRED_LABEL, is_label_for_transfers_between_schools=True)
        )
        another_school_unit = RegisteredSchoolUnitFactory()
        another_school_profile = UserProfileFactory(school_unit=another_school_unit, full_name=self.new_student.full_name,
                                                    username='{}_{}'.format(another_school_unit.id, self.new_student.email),
                                                    email=self.new_student.email,
                                                    phone_number=self.new_student.phone_number, user_role=UserProfile.UserRoles.STUDENT)

        prev_study_class = StudyClassFactory(school_unit=self.school_unit, class_master=self.teacher1, academic_program=self.academic_program,
                                             class_grade='IX', class_grade_arabic=9, class_letter='A', academic_year=self.calendar.academic_year - 1)
        TeacherClassThroughFactory(study_class=prev_study_class, teacher=self.teacher1, subject=self.coordination_subject, is_class_master=True)
        TeacherClassThroughFactory(study_class=prev_study_class, teacher=self.teacher1, subject=self.subject1, is_class_master=True)
        TeacherClassThroughFactory(study_class=prev_study_class, teacher=self.teacher2, subject=self.subject2, is_class_master=True,
                                   is_optional_subject=True)

        student_prev_study_class = StudyClassFactory(school_unit=another_school_unit, class_grade='IX', class_grade_arabic=9,
                                                     academic_year=self.calendar.academic_year - 1)
        StudentCatalogPerYearFactory(student=another_school_profile, study_class=student_prev_study_class,
                                     avg_sem1=9, avg_sem2=9, avg_annual=9, avg_final=9)
        catalog1 = StudentCatalogPerSubjectFactory(student=another_school_profile, study_class=student_prev_study_class,
                                                   subject=self.coordination_subject, avg_sem1=8, avg_sem2=8, avg_annual=8, avg_final=8)
        SubjectGradeFactory(student=another_school_profile, catalog_per_subject=catalog1, grade=8)
        SubjectAbsenceFactory(student=another_school_profile, catalog_per_subject=catalog1, is_founded=True)

        catalog2 = StudentCatalogPerSubjectFactory(student=another_school_profile, study_class=student_prev_study_class, subject=self.subject2,
                                                   avg_sem1=10, avg_sem2=10, avg_annual=10, avg_final=10)
        ExaminationGradeFactory(student=another_school_profile, catalog_per_subject=catalog2)

        self.request_data = {
            "new_students": [self.new_student.id]
        }

        response = self.client.patch(self.build_url(self.study_class.id), self.request_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        catalog_per_year = StudentCatalogPerYear.objects.get(student=self.new_student, study_class=prev_study_class)
        for average in [catalog_per_year.avg_sem1, catalog_per_year.avg_sem2, catalog_per_year.avg_annual, catalog_per_year.avg_final]:
            self.assertEqual(average, 9)

        new_catalog1 = StudentCatalogPerSubject.objects.get(student=self.new_student, study_class=prev_study_class,
                                                            subject=self.coordination_subject, teacher=self.teacher1)
        for average in [new_catalog1.avg_sem1, new_catalog1.avg_sem2, new_catalog1.avg_annual, new_catalog1.avg_final]:
            self.assertEqual(average, 8)
        self.assertEqual(new_catalog1.grades.count(), 1)
        self.assertEqual(new_catalog1.absences.count(), 1)

        new_catalog2 = StudentCatalogPerSubject.objects.get(student=self.new_student, study_class=prev_study_class,
                                                            subject=self.subject2, teacher=self.teacher2)
        for average in [new_catalog2.avg_sem1, new_catalog2.avg_sem2, new_catalog2.avg_annual, new_catalog2.avg_final]:
            self.assertEqual(average, 10)
        self.assertEqual(new_catalog2.examination_grades.count(), 1)

        new_catalog3 = StudentCatalogPerSubject.objects.get(student=self.new_student, study_class=prev_study_class,
                                                            subject=self.subject1, teacher=self.teacher1)
        for average in [new_catalog3.avg_sem1, new_catalog3.avg_sem2, new_catalog3.avg_annual, new_catalog3.avg_final]:
            self.assertEqual(average, None)
