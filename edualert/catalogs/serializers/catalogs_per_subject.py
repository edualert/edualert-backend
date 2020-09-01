from django.db.models.functions import Lower
from methodtools import lru_cache
from rest_framework import serializers

from edualert.academic_calendars.utils import get_current_academic_calendar
from edualert.catalogs.models import StudentCatalogPerSubject, SubjectAbsence, ExaminationGrade, SubjectGrade
from edualert.catalogs.utils import get_avg_limit_for_subject, has_technological_category, get_working_weeks_count, get_weekly_hours_count
from edualert.profiles.models import UserProfile
from edualert.profiles.serializers.users import StudentBaseSerializer, UserProfileBaseSerializer, LabelSerializer
from edualert.study_classes.serializers import StudyClassNameSerializer


class SubjectGradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubjectGrade
        fields = ('id', 'grade', 'taken_at', 'grade_type', 'created')


class ExaminationGradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExaminationGrade
        fields = ('id', 'examination_type', 'grade1', 'grade2', 'taken_at', 'created')


class SubjectAbsenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubjectAbsence
        fields = ('id', 'taken_at', 'is_founded', 'created')


class StudentCatalogPerSubjectWithTeacherSerializer(serializers.ModelSerializer):
    teacher = UserProfileBaseSerializer()
    grades_sem1 = serializers.SerializerMethodField()
    grades_sem2 = serializers.SerializerMethodField()
    abs_sem1 = serializers.SerializerMethodField()
    abs_sem2 = serializers.SerializerMethodField()
    second_examination_grades = serializers.SerializerMethodField()
    difference_grades_sem1 = serializers.SerializerMethodField()
    difference_grades_sem2 = serializers.SerializerMethodField()
    avg_limit = serializers.SerializerMethodField()
    third_of_hours_count_sem1 = serializers.SerializerMethodField()
    third_of_hours_count_sem2 = serializers.SerializerMethodField()
    third_of_hours_count_annual = serializers.SerializerMethodField()

    class Meta:
        model = StudentCatalogPerSubject
        fields = (
            'id', 'subject_name', 'teacher', 'avg_sem1', 'avg_sem2', 'avg_annual', 'avg_after_2nd_examination', 'avg_limit',
            'grades_sem1', 'grades_sem2', 'second_examination_grades', 'difference_grades_sem1', 'difference_grades_sem2',
            'abs_count_sem1', 'abs_count_sem2', 'abs_count_annual',
            'founded_abs_count_sem1', 'founded_abs_count_sem2', 'founded_abs_count_annual',
            'unfounded_abs_count_sem1', 'unfounded_abs_count_sem2', 'unfounded_abs_count_annual',
            'third_of_hours_count_sem1', 'third_of_hours_count_sem2', 'third_of_hours_count_annual',
            'abs_sem1', 'abs_sem2', 'wants_thesis', 'is_exempted', 'is_coordination_subject'
        )

    @staticmethod
    def get_avg_limit(obj):
        return get_avg_limit_for_subject(obj.study_class, obj.is_coordination_subject, obj.subject_id)

    @lru_cache(maxsize=None)
    def get_weekly_hours_count(self, obj):
        return get_weekly_hours_count(obj.study_class, obj.subject_id)

    @lru_cache(maxsize=None)
    def get_third_of_hours_count_by_semester(self, obj, semester):
        if semester == 1:
            working_weeks_count = self.context.get('working_weeks_count_sem1', 0)
        else:
            working_weeks_count = self.context.get('working_weeks_count_sem2', 0)
        semester_hours_count = working_weeks_count * self.get_weekly_hours_count(obj)
        return semester_hours_count // 3

    def get_third_of_hours_count_sem1(self, obj):
        return self.get_third_of_hours_count_by_semester(obj, 1)

    def get_third_of_hours_count_sem2(self, obj):
        return self.get_third_of_hours_count_by_semester(obj, 2)

    def get_third_of_hours_count_annual(self, obj):
        return self.get_third_of_hours_count_by_semester(obj, 1) + \
               self.get_third_of_hours_count_by_semester(obj, 2)

    @staticmethod
    def get_grades_sem1(obj):
        sem_grades = [grade for grade in obj.grades.all() if grade.semester == 1]
        return SubjectGradeSerializer(instance=sem_grades, many=True).data

    @staticmethod
    def get_grades_sem2(obj):
        sem_grades = [grade for grade in obj.grades.all() if grade.semester == 2]
        return SubjectGradeSerializer(instance=sem_grades, many=True).data

    @staticmethod
    def get_abs_sem1(obj):
        sem_absences = [absence for absence in obj.absences.all() if absence.semester == 1]
        return SubjectAbsenceSerializer(instance=sem_absences, many=True).data

    @staticmethod
    def get_abs_sem2(obj):
        sem_absences = [absence for absence in obj.absences.all() if absence.semester == 2]
        return SubjectAbsenceSerializer(instance=sem_absences, many=True).data

    @staticmethod
    def get_second_examination_grades(obj):
        grades = [grade for grade in obj.examination_grades.all()
                  if grade.grade_type == ExaminationGrade.GradeTypes.SECOND_EXAMINATION]
        return ExaminationGradeSerializer(instance=grades, many=True).data

    @staticmethod
    def get_difference_grades_sem1(obj):
        grades = [grade for grade in obj.examination_grades.all()
                  if grade.grade_type == ExaminationGrade.GradeTypes.DIFFERENCE and grade.semester == 1]
        return ExaminationGradeSerializer(instance=grades, many=True).data

    @staticmethod
    def get_difference_grades_sem2(obj):
        grades = [grade for grade in obj.examination_grades.all()
                  if grade.grade_type == ExaminationGrade.GradeTypes.DIFFERENCE and grade.semester == 2]
        return ExaminationGradeSerializer(instance=grades, many=True).data


class PupilStudyClassSerializer(serializers.ModelSerializer):
    parents = UserProfileBaseSerializer(many=True)
    labels = LabelSerializer(many=True)
    study_class = serializers.SerializerMethodField()
    catalogs_per_subjects = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = (
            'id', 'full_name', 'parents', 'labels', 'risk_description', 'study_class', 'catalogs_per_subjects'
        )

    def get_study_class(self, obj):
        return StudyClassNameSerializer(instance=self.context['study_class']).data

    def get_catalogs_per_subjects(self, obj):
        calendar = get_current_academic_calendar()
        study_class = self.context['study_class']
        is_technological_school = has_technological_category(study_class.school_unit)

        self.context.update({
            'working_weeks_count_sem1': get_working_weeks_count(calendar, 1, study_class, is_technological_school),
            'working_weeks_count_sem2': get_working_weeks_count(calendar, 2, study_class, is_technological_school)
        })

        return StudentCatalogPerSubjectWithTeacherSerializer(
            instance=obj.student_catalogs_per_subject.filter(study_class=study_class, is_enrolled=True)
                .select_related('teacher', 'study_class__school_unit__academic_profile', 'study_class__academic_program')
                .prefetch_related('grades', 'absences', 'examination_grades')
                .order_by('-is_coordination_subject', Lower('subject_name')),
            many=True,
            context=self.context
        ).data


class StudentCatalogPerSubjectSerializer(serializers.ModelSerializer):
    student = StudentBaseSerializer()
    grades_sem1 = serializers.SerializerMethodField()
    grades_sem2 = serializers.SerializerMethodField()
    abs_sem1 = serializers.SerializerMethodField()
    abs_sem2 = serializers.SerializerMethodField()
    second_examination_grades = serializers.SerializerMethodField()
    difference_grades_sem1 = serializers.SerializerMethodField()
    difference_grades_sem2 = serializers.SerializerMethodField()
    avg_limit = serializers.SerializerMethodField()
    third_of_hours_count_sem1 = serializers.SerializerMethodField()
    third_of_hours_count_sem2 = serializers.SerializerMethodField()
    third_of_hours_count_annual = serializers.SerializerMethodField()

    class Meta:
        model = StudentCatalogPerSubject
        fields = (
            'id', 'student', 'avg_sem1', 'avg_sem2', 'avg_annual', 'avg_after_2nd_examination', 'avg_limit', 'abs_count_sem1', 'abs_count_sem2',
            'abs_count_annual', 'founded_abs_count_sem1', 'founded_abs_count_sem2', 'founded_abs_count_annual', 'unfounded_abs_count_sem1',
            'unfounded_abs_count_sem2', 'unfounded_abs_count_annual', 'third_of_hours_count_sem1', 'third_of_hours_count_sem2',
            'third_of_hours_count_annual', 'grades_sem1', 'grades_sem2', 'second_examination_grades',
            'difference_grades_sem1', 'difference_grades_sem2', 'abs_sem1', 'abs_sem2', 'wants_thesis', 'is_exempted', 'is_coordination_subject'
        )

    def get_avg_limit(self, obj):
        avg_limit = self.context.get('avg_limit')
        if avg_limit is not None:
            return avg_limit
        return get_avg_limit_for_subject(obj.study_class, obj.is_coordination_subject, obj.subject_id)

    @lru_cache(maxsize=None)
    def get_weekly_hours_count(self, obj):
        return get_weekly_hours_count(obj.study_class, obj.subject_id)

    @lru_cache(maxsize=None)
    def get_calendar(self):
        return get_current_academic_calendar()

    @lru_cache(maxsize=None)
    def is_technological_school(self, obj):
        return has_technological_category(obj.study_class.school_unit)

    @lru_cache(maxsize=None)
    def get_third_of_hours_count_by_semester(self, obj, semester):
        calendar = self.get_calendar()
        is_technological_school = self.is_technological_school(obj)

        if semester == 1:
            working_weeks_count = get_working_weeks_count(calendar, 1, obj.study_class, is_technological_school)
        else:
            working_weeks_count = get_working_weeks_count(calendar, 2, obj.study_class, is_technological_school)
        semester_hours_count = working_weeks_count * self.get_weekly_hours_count(obj)
        return semester_hours_count // 3

    def get_third_of_hours_count_sem1(self, obj):
        third_of_hours_count_sem1 = self.context.get('third_of_hours_count_sem1')
        if third_of_hours_count_sem1 is not None:
            return third_of_hours_count_sem1
        return self.get_third_of_hours_count_by_semester(obj, 1)

    def get_third_of_hours_count_sem2(self, obj):
        third_of_hours_count_sem2 = self.context.get('third_of_hours_count_sem2')
        if third_of_hours_count_sem2 is not None:
            return third_of_hours_count_sem2
        return self.get_third_of_hours_count_by_semester(obj, 2)

    def get_third_of_hours_count_annual(self, obj):
        third_of_hours_count_annual = self.context.get('third_of_hours_count_annual')
        if third_of_hours_count_annual is not None:
            return third_of_hours_count_annual
        return self.get_third_of_hours_count_by_semester(obj, 1) + \
               self.get_third_of_hours_count_by_semester(obj, 2)

    @staticmethod
    def get_grades_sem1(obj):
        grades = [grade for grade in obj.grades.all() if grade.semester == 1]
        return SubjectGradeSerializer(grades, many=True).data

    @staticmethod
    def get_grades_sem2(obj):
        grades = [grade for grade in obj.grades.all() if grade.semester == 2]
        return SubjectGradeSerializer(grades, many=True).data

    @staticmethod
    def get_abs_sem1(obj):
        absences = [absence for absence in obj.absences.all() if absence.semester == 1]
        return SubjectAbsenceSerializer(absences, many=True).data

    @staticmethod
    def get_abs_sem2(obj):
        absences = [absence for absence in obj.absences.all() if absence.semester == 2]
        return SubjectAbsenceSerializer(absences, many=True).data

    @lru_cache(maxsize=None)
    def fetch_examination_grades(self, obj):
        # This serializer is sometimes used with an instance for which these grades couldn't be prefetched.
        return obj.examination_grades.all()

    def get_second_examination_grades(self, obj):
        grades = [grade for grade in self.fetch_examination_grades(obj)
                  if grade.grade_type == ExaminationGrade.GradeTypes.SECOND_EXAMINATION]
        return ExaminationGradeSerializer(grades, many=True).data

    def get_difference_grades_sem1(self, obj):
        grades = [grade for grade in self.fetch_examination_grades(obj)
                  if grade.grade_type == ExaminationGrade.GradeTypes.DIFFERENCE and grade.semester == 1]
        return ExaminationGradeSerializer(grades, many=True).data

    def get_difference_grades_sem2(self, obj):
        grades = [grade for grade in self.fetch_examination_grades(obj)
                  if grade.grade_type == ExaminationGrade.GradeTypes.DIFFERENCE and grade.semester != 1]
        return ExaminationGradeSerializer(grades, many=True).data


class CatalogsPerSubjectRemarksSerializer(serializers.ModelSerializer):
    remarks = serializers.CharField(max_length=500)

    class Meta:
        model = StudentCatalogPerSubject
        fields = ('remarks',)
