from ddt import data, ddt
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from edualert.academic_calendars.factories import AcademicYearCalendarFactory
from edualert.catalogs.factories import StudentCatalogPerSubjectFactory, SubjectGradeFactory, ExaminationGradeFactory, SubjectAbsenceFactory, StudentCatalogPerYearFactory
from edualert.catalogs.models import ExaminationGrade
from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory, LabelFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.study_classes.factories import StudyClassFactory, TeacherClassThroughFactory
from edualert.subjects.factories import SubjectFactory, ProgramSubjectThroughFactory


@ddt
class OwnStudyClassPupilDetailTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.calendar = AcademicYearCalendarFactory()
        cls.school_unit = RegisteredSchoolUnitFactory()
        cls.teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=cls.school_unit)
        cls.study_class = StudyClassFactory(school_unit=cls.school_unit, class_grade='IX', class_grade_arabic=9, class_master=cls.teacher)
        cls.student = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=cls.school_unit, student_in_class=cls.study_class)
        StudentCatalogPerYearFactory(student=cls.student, study_class=cls.study_class)

    @staticmethod
    def build_url(study_class_id, pupil_id):
        return reverse('catalogs:own-study-class-pupil-detail', kwargs={'study_class_id': study_class_id, 'pupil_id': pupil_id})

    def test_own_study_class_pupil_detail_unauthenticated(self):
        response = self.client.get(self.build_url(self.study_class.id, self.student.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.PRINCIPAL,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_own_study_class_pupil_detail_wrong_user_type(self, user_role):
        user = UserProfileFactory(
            user_role=user_role,
            school_unit=self.school_unit if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )
        self.client.login(username=user.username, password='passwd')

        response = self.client.get(self.build_url(self.study_class.id, self.student.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_own_study_class_pupil_detail_study_class_does_not_exist(self):
        self.client.login(username=self.teacher.username, password='passwd')
        response = self.client.get(self.build_url(0, self.student.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_own_study_class_pupil_detail_is_not_class_master(self):
        self.client.login(username=self.teacher.username, password='passwd')
        study_class = StudyClassFactory(school_unit=self.school_unit)

        response = self.client.get(self.build_url(study_class.id, self.student.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_own_study_class_pupil_detail_student_not_found(self):
        self.client.login(username=self.teacher.username, password='passwd')

        # not student in requested class
        profile1 = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=self.school_unit)
        # inactive student
        profile2 = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=self.school_unit, is_active=False)

        for student_id in [0, profile1.id, profile2.id]:
            response = self.client.get(self.build_url(self.study_class.id, student_id))
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_own_study_class_pupil_detail_success(self):
        self.client.login(username=self.teacher.username, password='passwd')
        parent = UserProfileFactory(user_role=UserProfile.UserRoles.PARENT, school_unit=self.school_unit)
        self.student.parents.add(parent)
        label = LabelFactory(user_role=UserProfile.UserRoles.STUDENT)
        self.student.labels.add(label)

        coordination_subject = SubjectFactory(name='Dirigentie', is_coordination=True)
        subject1 = SubjectFactory(name='Subject')
        subject2 = SubjectFactory(name='Another Subject')
        subject3 = SubjectFactory(name='Optional Subject')
        teacher2 = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=self.school_unit)

        TeacherClassThroughFactory(study_class=self.study_class, teacher=self.teacher, subject=coordination_subject, is_class_master=True)
        TeacherClassThroughFactory(study_class=self.study_class, teacher=self.teacher, subject=subject1, is_class_master=True)
        TeacherClassThroughFactory(study_class=self.study_class, teacher=teacher2, subject=subject2)
        TeacherClassThroughFactory(study_class=self.study_class, teacher=teacher2, subject=subject3)

        catalog1 = StudentCatalogPerSubjectFactory(student=self.student, teacher=self.teacher, study_class=self.study_class, subject=coordination_subject)
        catalog2 = StudentCatalogPerSubjectFactory(student=self.student, teacher=self.teacher, study_class=self.study_class, subject=subject1)
        catalog3 = StudentCatalogPerSubjectFactory(student=self.student, teacher=teacher2, study_class=self.study_class, subject=subject2)
        StudentCatalogPerSubjectFactory(student=self.student, teacher=teacher2, study_class=self.study_class, subject=subject3, is_enrolled=False)
        for subject in [subject1, subject2]:
            ProgramSubjectThroughFactory(academic_program=self.study_class.academic_program, class_grade=self.study_class.class_grade,
                                         subject=subject, weekly_hours_count=1)

        yesterday = timezone.now().date() - timezone.timedelta(days=1)
        grade1 = SubjectGradeFactory(student=self.student, catalog_per_subject=catalog2)
        grade2 = SubjectGradeFactory(student=self.student, catalog_per_subject=catalog2, taken_at=yesterday)
        grade3 = SubjectGradeFactory(student=self.student, catalog_per_subject=catalog2, semester=2, taken_at=yesterday)
        grade4 = SubjectGradeFactory(student=self.student, catalog_per_subject=catalog2, semester=2)

        exam_grade1 = ExaminationGradeFactory(student=self.student, catalog_per_subject=catalog2)
        exam_grade2 = ExaminationGradeFactory(student=self.student, catalog_per_subject=catalog2, examination_type=ExaminationGrade.ExaminationTypes.ORAL)
        exam_grade3 = ExaminationGradeFactory(student=self.student, catalog_per_subject=catalog2, taken_at=yesterday,
                                              grade_type=ExaminationGrade.GradeTypes.DIFFERENCE, semester=1)
        exam_grade4 = ExaminationGradeFactory(student=self.student, catalog_per_subject=catalog2,
                                              examination_type=ExaminationGrade.ExaminationTypes.ORAL,
                                              grade_type=ExaminationGrade.GradeTypes.DIFFERENCE, semester=1)
        exam_grade5 = ExaminationGradeFactory(student=self.student, catalog_per_subject=catalog2, semester=2,
                                              grade_type=ExaminationGrade.GradeTypes.DIFFERENCE)
        exam_grade6 = ExaminationGradeFactory(student=self.student, catalog_per_subject=catalog2, taken_at=yesterday, semester=2,
                                              examination_type=ExaminationGrade.ExaminationTypes.ORAL,
                                              grade_type=ExaminationGrade.GradeTypes.DIFFERENCE)

        abs1 = SubjectAbsenceFactory(student=self.student, catalog_per_subject=catalog2)
        abs2 = SubjectAbsenceFactory(student=self.student, catalog_per_subject=catalog2, taken_at=yesterday)
        abs3 = SubjectAbsenceFactory(student=self.student, catalog_per_subject=catalog2, semester=2, taken_at=yesterday)
        abs4 = SubjectAbsenceFactory(student=self.student, catalog_per_subject=catalog2, semester=2)

        response = self.client.get(self.build_url(self.study_class.id, self.student.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_fields = [
            'id', 'full_name', 'parents', 'labels', 'risk_description', 'study_class', 'catalogs_per_subjects'
        ]
        catalog_expected_fields = [
            'id', 'subject_name', 'teacher', 'avg_sem1', 'avg_sem2', 'avg_annual', 'avg_after_2nd_examination', 'avg_limit',
            'grades_sem1', 'grades_sem2', 'second_examination_grades', 'difference_grades_sem1', 'difference_grades_sem2',
            'abs_count_sem1', 'abs_count_sem2', 'abs_count_annual',
            'founded_abs_count_sem1', 'founded_abs_count_sem2', 'founded_abs_count_annual',
            'unfounded_abs_count_sem1', 'unfounded_abs_count_sem2', 'unfounded_abs_count_annual',
            'third_of_hours_count_sem1', 'third_of_hours_count_sem2', 'third_of_hours_count_annual',
            'abs_sem1', 'abs_sem2', 'wants_thesis', 'is_exempted', 'is_coordination_subject'
        ]
        profile_expected_fields = ['id', 'full_name']
        label_expected_fields = ['id', 'text']
        study_class_expected_fields = ['id', 'class_grade', 'class_letter']
        grade_expected_fields = ['id', 'grade', 'taken_at', 'grade_type', 'created']
        absence_expected_fields = ['id', 'taken_at', 'is_founded', 'created']
        exam_grade_expected_fields = ['id', 'examination_type', 'grade1', 'grade2', 'taken_at', 'created']

        self.assertCountEqual(response.data.keys(), expected_fields)
        self.assertEqual(len(response.data['parents']), 1)
        self.assertCountEqual(response.data['parents'][0].keys(), profile_expected_fields)
        self.assertEqual(len(response.data['labels']), 1)
        self.assertCountEqual(response.data['labels'][0].keys(), label_expected_fields)
        self.assertCountEqual(response.data['study_class'].keys(), study_class_expected_fields)
        catalogs_per_subjects = response.data['catalogs_per_subjects']
        self.assertEqual(len(catalogs_per_subjects), 3)

        for catalog_data in catalogs_per_subjects:
            self.assertCountEqual(catalog_data.keys(), catalog_expected_fields)
            self.assertCountEqual(catalog_data['teacher'].keys(), profile_expected_fields)
            self.assertEqual(catalog_data['avg_limit'], 6 if catalog_data['id'] == catalog1.id else 5)
            self.assertEqual(catalog_data['third_of_hours_count_sem1'], 5)
            self.assertEqual(catalog_data['third_of_hours_count_sem2'], 5)
            self.assertEqual(catalog_data['third_of_hours_count_annual'], 10)

        self.assertEqual(catalogs_per_subjects[0]['id'], catalog1.id)
        self.assertEqual(catalogs_per_subjects[0]['teacher']['id'], self.teacher.id)
        self.assertEqual(catalogs_per_subjects[0]['subject_name'], coordination_subject.name)
        self.assertEqual(catalogs_per_subjects[1]['id'], catalog3.id)
        self.assertEqual(catalogs_per_subjects[1]['teacher']['id'], teacher2.id)
        self.assertEqual(catalogs_per_subjects[1]['subject_name'], subject2.name)
        self.assertEqual(catalogs_per_subjects[2]['id'], catalog2.id)
        self.assertEqual(catalogs_per_subjects[2]['teacher']['id'], self.teacher.id)
        self.assertEqual(catalogs_per_subjects[2]['subject_name'], subject1.name)

        for grade_data in catalogs_per_subjects[2]['grades_sem1'] + catalogs_per_subjects[2]['grades_sem2']:
            self.assertCountEqual(grade_data.keys(), grade_expected_fields)

        for abs_data in catalogs_per_subjects[2]['abs_sem1'] + catalogs_per_subjects[2]['abs_sem2']:
            self.assertCountEqual(abs_data.keys(), absence_expected_fields)

        for exam_grade_data in catalogs_per_subjects[2]['second_examination_grades'] + \
                               catalogs_per_subjects[2]['difference_grades_sem1'] + catalogs_per_subjects[2]['difference_grades_sem2']:
            self.assertCountEqual(exam_grade_data.keys(), exam_grade_expected_fields)

        self.assertEqual(catalogs_per_subjects[2]['grades_sem1'][0]['id'], grade1.id)
        self.assertEqual(catalogs_per_subjects[2]['grades_sem1'][1]['id'], grade2.id)
        self.assertEqual(catalogs_per_subjects[2]['grades_sem2'][0]['id'], grade4.id)
        self.assertEqual(catalogs_per_subjects[2]['grades_sem2'][1]['id'], grade3.id)

        self.assertEqual(catalogs_per_subjects[2]['abs_sem1'][0]['id'], abs1.id)
        self.assertEqual(catalogs_per_subjects[2]['abs_sem1'][1]['id'], abs2.id)
        self.assertEqual(catalogs_per_subjects[2]['abs_sem2'][0]['id'], abs4.id)
        self.assertEqual(catalogs_per_subjects[2]['abs_sem2'][1]['id'], abs3.id)

        self.assertEqual(catalogs_per_subjects[2]['second_examination_grades'][0]['id'], exam_grade2.id)
        self.assertEqual(catalogs_per_subjects[2]['second_examination_grades'][1]['id'], exam_grade1.id)
        self.assertEqual(catalogs_per_subjects[2]['difference_grades_sem1'][0]['id'], exam_grade4.id)
        self.assertEqual(catalogs_per_subjects[2]['difference_grades_sem1'][1]['id'], exam_grade3.id)
        self.assertEqual(catalogs_per_subjects[2]['difference_grades_sem2'][0]['id'], exam_grade5.id)
        self.assertEqual(catalogs_per_subjects[2]['difference_grades_sem2'][1]['id'], exam_grade6.id)
