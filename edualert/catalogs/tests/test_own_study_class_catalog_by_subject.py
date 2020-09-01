import datetime

from ddt import data, ddt
from django.db.models import Count, Max
from django.urls import reverse
from rest_framework import status

from edualert.academic_calendars.factories import AcademicYearCalendarFactory
from edualert.catalogs.factories import StudentCatalogPerSubjectFactory, SubjectGradeFactory, SubjectAbsenceFactory, ExaminationGradeFactory
from edualert.catalogs.models import SubjectGrade, ExaminationGrade, StudentCatalogPerSubject
from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.study_classes.factories import StudyClassFactory, TeacherClassThroughFactory
from edualert.subjects.factories import SubjectFactory, ProgramSubjectThroughFactory


@ddt
class OwnStudyClassCatalogPerSubjectTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.calendar = AcademicYearCalendarFactory()
        cls.school_unit = RegisteredSchoolUnitFactory()
        cls.teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=cls.school_unit)
        cls.student = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=cls.school_unit)
        cls.study_class = StudyClassFactory(school_unit=cls.school_unit, class_grade='IX', class_grade_arabic=9)
        cls.subject = SubjectFactory()
        cls.teacher_class_through = TeacherClassThroughFactory(
            study_class=cls.study_class,
            teacher=cls.teacher,
            subject=cls.subject
        )
        ProgramSubjectThroughFactory(academic_program=cls.study_class.academic_program, class_grade='IX',
                                     subject=cls.subject, weekly_hours_count=3)

    @staticmethod
    def build_url(study_class_id, subject_id):
        return reverse('catalogs:own-study-class-catalog-by-subject', kwargs={'study_class_id': study_class_id, 'subject_id': subject_id})

    def test_own_study_class_catalog_per_subject_unauthenticated(self):
        response = self.client.get(self.build_url(self.study_class.id, self.subject.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.PRINCIPAL,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_own_study_class_catalog_per_subject_wrong_user_type(self, user_role):
        user = UserProfileFactory(
            user_role=user_role,
            school_unit=self.school_unit if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )
        self.client.login(username=user.username, password='passwd')

        response = self.client.get(self.build_url(self.study_class.id, self.subject.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_own_study_class_catalog_per_subject_study_class_does_not_exist(self):
        self.client.login(username=self.teacher.username, password='passwd')
        response = self.client.get(self.build_url(0, self.subject.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_own_study_class_catalog_per_subject_subject_does_not_exist(self):
        self.client.login(username=self.teacher.username, password='passwd')
        response = self.client.get(self.build_url(self.study_class.id, 0))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_own_study_class_catalog_per_subject_not_assigned_teacher(self):
        self.client.login(username=self.teacher.username, password='passwd')
        self.study_class = StudyClassFactory(school_unit=self.school_unit)
        response = self.client.get(self.build_url(self.study_class.id, self.subject.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_own_study_class_catalog_per_subject_not_teaching_subject(self):
        self.client.login(username=self.teacher.username, password='passwd')

        response = self.client.get(self.build_url(self.study_class.id, SubjectFactory().id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_own_study_class_catalog_per_subject_is_not_enrolled(self):
        StudentCatalogPerSubjectFactory(
            subject=self.subject,
            teacher=self.teacher,
            student=UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, full_name='a'),
            study_class=self.study_class,
            academic_year=2020,
            avg_sem1=1,
            avg_sem2=1,
            avg_final=1,
            abs_count_sem1=1,
            abs_count_sem2=1,
            abs_count_annual=1,
            is_enrolled=False
        )
        self.client.login(username=self.teacher.username, password='passwd')
        response = self.client.get(self.build_url(self.study_class.id, self.subject.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_own_study_class_catalog_per_subject_success(self):
        self.client.login(username=self.teacher.username, password='passwd')
        catalog1 = StudentCatalogPerSubjectFactory(
            subject=self.subject,
            teacher=self.teacher,
            student=UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, full_name='a'),
            study_class=self.study_class,
            academic_year=2020,
            avg_sem1=1,
            avg_sem2=1,
            avg_final=1,
            abs_count_sem1=1,
            abs_count_sem2=1,
            abs_count_annual=1
        )
        grade1 = SubjectGradeFactory(
            catalog_per_subject=catalog1,
            student=catalog1.student,
            semester=1,
            grade=10
        )
        grade2 = SubjectGradeFactory(
            catalog_per_subject=catalog1,
            student=catalog1.student,
            semester=1,
            grade=9
        )
        grade3 = SubjectGradeFactory(
            catalog_per_subject=catalog1,
            student=catalog1.student,
            semester=2,
            grade=3,
            grade_type=SubjectGrade.GradeTypes.THESIS
        )
        absence1 = SubjectAbsenceFactory(
            catalog_per_subject=catalog1,
            student=catalog1.student,
            semester=1
        )
        absence2 = SubjectAbsenceFactory(
            catalog_per_subject=catalog1,
            student=catalog1.student,
            semester=1
        )
        absence3 = SubjectAbsenceFactory(
            catalog_per_subject=catalog1,
            student=catalog1.student,
            semester=2
        )
        examination_grade1 = ExaminationGradeFactory(
            catalog_per_subject=catalog1,
            student=catalog1.student,
            subject_name=self.subject.name,
            grade_type=ExaminationGrade.GradeTypes.DIFFERENCE,
            semester=1
        )
        examination_grade2 = ExaminationGradeFactory(
            catalog_per_subject=catalog1,
            student=catalog1.student,
            subject_name=self.subject.name,
            grade_type=ExaminationGrade.GradeTypes.SECOND_EXAMINATION
        )
        catalog2 = StudentCatalogPerSubjectFactory(
            subject=self.subject,
            teacher=self.teacher,
            student=UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, full_name='b'),
            study_class=self.study_class,
            academic_year=2020,
            avg_sem1=1,
            avg_sem2=1,
            avg_final=1,
            abs_count_sem1=1,
            abs_count_sem2=1,
            abs_count_annual=1
        )
        grade4 = SubjectGradeFactory(
            catalog_per_subject=catalog2,
            student=catalog2.student,
            semester=1,
            grade=10
        )
        grade5 = SubjectGradeFactory(
            catalog_per_subject=catalog2,
            student=catalog2.student,
            semester=1,
            grade=9
        )
        grade6 = SubjectGradeFactory(
            catalog_per_subject=catalog2,
            student=catalog2.student,
            semester=2,
            grade=3
        )
        absence4 = SubjectAbsenceFactory(
            catalog_per_subject=catalog2,
            student=catalog2.student,
            semester=1
        )
        absence5 = SubjectAbsenceFactory(
            catalog_per_subject=catalog2,
            student=catalog2.student,
            semester=1
        )
        absence6 = SubjectAbsenceFactory(
            catalog_per_subject=catalog2,
            student=catalog2.student,
            semester=2
        )
        examination_grade3 = ExaminationGradeFactory(
            catalog_per_subject=catalog2,
            student=catalog2.student,
            subject_name=self.subject.name,
            grade_type=ExaminationGrade.GradeTypes.DIFFERENCE,
            semester=2
        )
        examination_grade4 = ExaminationGradeFactory(
            catalog_per_subject=catalog2,
            student=catalog2.student,
            subject_name=self.subject.name,
            grade_type=ExaminationGrade.GradeTypes.SECOND_EXAMINATION,
            semester=1
        )

        response = self.client.get(self.build_url(self.study_class.id, self.subject.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        catalog_expected_fields = [
            'id', 'student', 'avg_sem1', 'avg_sem2', 'avg_annual', 'avg_after_2nd_examination', 'avg_limit', 'abs_count_sem1', 'abs_count_sem2',
            'abs_count_annual', 'founded_abs_count_sem1', 'founded_abs_count_sem2', 'founded_abs_count_annual', 'unfounded_abs_count_sem1',
            'unfounded_abs_count_sem2', 'unfounded_abs_count_annual', 'grades_sem1', 'grades_sem2', 'abs_sem1', 'abs_sem2',
            'second_examination_grades', 'difference_grades_sem1', 'difference_grades_sem2', 'wants_thesis', 'is_exempted',
            'third_of_hours_count_sem1', 'third_of_hours_count_sem2', 'third_of_hours_count_annual', 'is_coordination_subject'
        ]
        student_expected_fields = ['id', 'full_name', 'labels', 'risk_description']
        label_expected_fields = ['id', 'text']
        grade_fields = ['id', 'grade', 'taken_at', 'grade_type', 'created']
        absence_fields = ['id', 'taken_at', 'is_founded', 'created']
        examination_grade_fields = ['id', 'examination_type', 'taken_at', 'grade1', 'grade2', 'created']
        for catalog_data in response.data:
            self.assertCountEqual(catalog_data.keys(), catalog_expected_fields)
            self.assertCountEqual(catalog_data['student'].keys(), student_expected_fields)
            for label_data in catalog_data['student']['labels']:
                self.assertCountEqual(label_data.keys(), label_expected_fields)
            for grade_data in catalog_data['grades_sem1'] + catalog_data['grades_sem2']:
                self.assertCountEqual(grade_data.keys(), grade_fields)
            for absence_data in catalog_data['abs_sem1'] + catalog_data['abs_sem2']:
                self.assertCountEqual(absence_data.keys(), absence_fields)
            for examination_data in catalog_data['second_examination_grades'] + catalog_data['difference_grades_sem1'] + catalog_data['difference_grades_sem2']:
                self.assertCountEqual(examination_data.keys(), examination_grade_fields)
            self.assertEqual(catalog_data['avg_limit'], 5)
            self.assertEqual(catalog_data['third_of_hours_count_sem1'], 15)
            self.assertEqual(catalog_data['third_of_hours_count_sem2'], 15)
            self.assertEqual(catalog_data['third_of_hours_count_annual'], 30)

        self.assertCountEqual([grade['id'] for grade in response.data[0]['grades_sem1']], [grade1.id, grade2.id])
        self.assertCountEqual([grade['id'] for grade in response.data[0]['grades_sem2']], [grade3.id])
        self.assertCountEqual([grade['id'] for grade in response.data[1]['grades_sem1']], [grade4.id, grade5.id])
        self.assertCountEqual([grade['id'] for grade in response.data[1]['grades_sem2']], [grade6.id])
        self.assertCountEqual([absence['id'] for absence in response.data[0]['abs_sem1']], [absence1.id, absence2.id])
        self.assertCountEqual([absence['id'] for absence in response.data[0]['abs_sem2']], [absence3.id])
        self.assertCountEqual([absence['id'] for absence in response.data[1]['abs_sem1']], [absence4.id, absence5.id])
        self.assertCountEqual([absence['id'] for absence in response.data[1]['abs_sem2']], [absence6.id])
        self.assertCountEqual([grade['id'] for grade in response.data[0]['difference_grades_sem1']], [examination_grade1.id])
        self.assertCountEqual(response.data[0]['difference_grades_sem2'], [])
        self.assertCountEqual([grade['id'] for grade in response.data[0]['second_examination_grades']], [examination_grade2.id])
        self.assertCountEqual(response.data[1]['difference_grades_sem1'], [])
        self.assertCountEqual([grade['id'] for grade in response.data[1]['difference_grades_sem2']], [examination_grade3.id])
        self.assertCountEqual([grade['id'] for grade in response.data[1]['second_examination_grades']], [examination_grade4.id])

    @data(
        None, 'student_name', 'avg_sem1', 'avg_sem2', 'avg_final',
        'abs_count_sem1', 'abs_count_sem2', 'abs_count_annual',
        '-student_name', '-avg_sem1', '-avg_sem2', '-avg_final', '-abs_count_sem1', '-abs_count_sem2', '-abs_count_annual'
    )
    def test_own_study_class_catalog_per_subject_ordering(self, ordering):
        self.client.login(username=self.teacher.username, password='passwd')

        StudentCatalogPerSubjectFactory(
            subject=self.subject,
            teacher=self.teacher,
            student=UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, full_name='a'),
            study_class=self.study_class,
            academic_year=2020,
            avg_sem1=1,
            avg_sem2=1,
            avg_final=1,
            abs_count_sem1=1,
            abs_count_sem2=1,
            abs_count_annual=1
        )
        StudentCatalogPerSubjectFactory(
            subject=self.subject,
            teacher=self.teacher,
            student=UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, full_name='b'),
            study_class=self.study_class,
            academic_year=2020,
            avg_sem1=2,
            avg_sem2=2,
            avg_final=2,
            abs_count_sem1=2,
            abs_count_sem2=2,
            abs_count_annual=2
        )
        StudentCatalogPerSubjectFactory(
            subject=self.subject,
            teacher=self.teacher,
            student=UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, full_name='c'),
            study_class=self.study_class,
            academic_year=2020,
            avg_sem1=3,
            avg_sem2=3,
            avg_final=3,
            abs_count_sem1=3,
            abs_count_sem2=3,
            abs_count_annual=3
        )
        response = self.client.get(self.build_url(self.study_class.id, self.subject.id), {'ordering': ordering} if ordering else None)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        if not ordering or ordering == 'student_name':
            ordering = 'student__full_name'

        if ordering == '-student_name':
            ordering = '-student__full_name'

        for catalog_data, catalog in zip(response.data, StudentCatalogPerSubject.objects.order_by(ordering)):
            self.assertEqual(catalog_data['id'], catalog.id)

    def test_own_study_class_catalog_per_subject_ordering_by_aggregates(self):
        self.client.login(username=self.teacher.username, password='passwd')

        catalog1 = StudentCatalogPerSubjectFactory(
            subject=self.subject,
            teacher=self.teacher,
            student=UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, full_name='a'),
            study_class=self.study_class,
            academic_year=2020
        )
        catalog2 = StudentCatalogPerSubjectFactory(
            subject=self.subject,
            teacher=self.teacher,
            student=UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, full_name='b'),
            study_class=self.study_class,
            academic_year=2020
        )
        catalog3 = StudentCatalogPerSubjectFactory(
            subject=self.subject,
            teacher=self.teacher,
            student=UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, full_name='c'),
            study_class=self.study_class,
            academic_year=2020
        )
        SubjectGradeFactory(
            catalog_per_subject=catalog1,
            student=catalog1.student,
            semester=1,
            grade=10,
            taken_at=datetime.date(2020, 4, 4)
        )
        for _ in range(2):
            SubjectGradeFactory(
                catalog_per_subject=catalog2,
                student=catalog2.student,
                semester=1,
                grade=9,
                taken_at=datetime.date(2020, 5, 5)
            )
        for _ in range(3):
            SubjectGradeFactory(
                catalog_per_subject=catalog3,
                student=catalog3.student,
                semester=2,
                grade=3,
                grade_type=SubjectGrade.GradeTypes.THESIS,
                taken_at=datetime.date(2020, 6, 6)
            )

        response = self.client.get(self.build_url(self.study_class.id, self.subject.id), {'ordering': 'grades_count'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for catalog_data, catalog in zip(response.data, StudentCatalogPerSubject.objects.annotate(grades_count=Count('grade')).order_by('grades_count')):
            self.assertEqual(catalog_data['id'], catalog.id)

        response = self.client.get(self.build_url(self.study_class.id, self.subject.id), {'ordering': '-grades_count'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for catalog_data, catalog in zip(response.data, StudentCatalogPerSubject.objects.annotate(grades_count=Count('grade')).order_by('-grades_count')):
            self.assertEqual(catalog_data['id'], catalog.id)

        response = self.client.get(self.build_url(self.study_class.id, self.subject.id), {'ordering': 'last_grade_date'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for catalog_data, catalog in zip(response.data, StudentCatalogPerSubject.objects.annotate(last_grade_date=Max('grade__taken_at')).order_by('last_grade_date')):
            self.assertEqual(catalog_data['id'], catalog.id)

        response = self.client.get(self.build_url(self.study_class.id, self.subject.id), {'ordering': '-last_grade_date'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for catalog_data, catalog in zip(response.data, StudentCatalogPerSubject.objects.annotate(last_grade_date=Max('grade__taken_at')).order_by('-last_grade_date')):
            self.assertEqual(catalog_data['id'], catalog.id)
