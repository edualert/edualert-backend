from django.db.models.functions import Lower
from methodtools import lru_cache
from rest_framework import serializers

from edualert.academic_calendars.utils import get_current_academic_calendar
from edualert.catalogs.models import StudentCatalogPerYear, StudentCatalogPerSubject
from edualert.catalogs.serializers import StudentCatalogPerSubjectWithTeacherSerializer
from edualert.catalogs.utils import has_technological_category, get_avg_limit_for_subject, get_behavior_grade_limit, \
    get_working_weeks_count, get_weekly_hours_count
from edualert.profiles.models import UserProfile
from edualert.profiles.serializers import UserProfileBaseSerializer, LabelSerializer
from edualert.study_classes.models import StudyClass


class StudyClassForSchoolSituationSerializer(serializers.ModelSerializer):
    class_master = UserProfileBaseSerializer()

    class Meta:
        model = StudyClass
        fields = ('id', 'class_grade', 'class_letter', 'academic_program_name', 'class_master')


class SchoolSituationSerializer(serializers.ModelSerializer):
    study_class = serializers.SerializerMethodField()
    labels = LabelSerializer(many=True)
    catalogs_per_subjects = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ('id', 'full_name', 'study_class', 'labels', 'risk_description', 'catalogs_per_subjects')

    @lru_cache(maxsize=None)
    def get_calendar(self):
        return get_current_academic_calendar()

    def get_academic_year(self):
        academic_year = self.context['request'].query_params.get('academic_year')
        if academic_year:
            return academic_year

        calendar = self.get_calendar()
        if not calendar:
            return None

        return calendar.academic_year

    @lru_cache(maxsize=None)
    def retrieve_study_class(self, obj):
        academic_year = self.get_academic_year()
        if not academic_year:
            return None

        catalog_per_year = StudentCatalogPerYear.objects.filter(student=obj, academic_year=academic_year).first()
        if not catalog_per_year:
            return None

        return catalog_per_year.study_class

    def get_study_class(self, obj):
        study_class = self.retrieve_study_class(obj)
        if not study_class:
            return None
        return StudyClassForSchoolSituationSerializer(study_class).data

    def get_catalogs_per_subjects(self, obj):
        study_class = self.retrieve_study_class(obj)
        if not study_class:
            return None

        is_technological_school = has_technological_category(study_class.school_unit)
        self.context.update({
            'working_weeks_count_sem1': get_working_weeks_count(self.get_calendar(), 1, study_class, is_technological_school),
            'working_weeks_count_sem2': get_working_weeks_count(self.get_calendar(), 2, study_class, is_technological_school)
        })

        return StudentCatalogPerSubjectWithTeacherSerializer(
            instance=obj.student_catalogs_per_subject.filter(academic_year=study_class.academic_year, is_enrolled=True)
                .select_related('teacher', 'study_class__school_unit__academic_profile', 'study_class__academic_program')
                .prefetch_related('grades', 'absences', 'examination_grades')
                .order_by('-is_coordination_subject', Lower('subject_name')),
            many=True,
            context=self.context
        ).data


class StudentStatisticsSerializer(serializers.ModelSerializer):
    behavior_grade_limit = serializers.SerializerMethodField()

    class Meta:
        model = StudentCatalogPerYear
        fields = (
            'behavior_grade_sem1', 'behavior_grade_annual', 'behavior_grade_limit', 'abs_count_sem1', 'class_place_by_avg_sem1', 'class_place_by_avg_annual',
            'abs_count_annual', 'founded_abs_count_sem1', 'founded_abs_count_annual', 'unfounded_abs_count_sem1', 'unfounded_abs_count_annual',
            'school_place_by_avg_sem1', 'school_place_by_avg_annual', 'class_place_by_abs_sem1', 'class_place_by_abs_annual', 'school_place_by_abs_sem1', 'school_place_by_abs_annual',
            'avg_sem1', 'avg_annual',
        )

    @staticmethod
    def get_behavior_grade_limit(obj):
        academic_profile = obj.student.school_unit.academic_profile
        return get_behavior_grade_limit(academic_profile)


class StudentSubjectsAtRiskSerializer(serializers.ModelSerializer):
    avg_limit = serializers.SerializerMethodField()
    third_of_hours_count_sem1 = serializers.SerializerMethodField()
    third_of_hours_count_annual = serializers.SerializerMethodField()

    class Meta:
        model = StudentCatalogPerSubject
        fields = ('id', 'subject_name', 'avg_sem1', 'avg_final', 'avg_limit',
                  'unfounded_abs_count_sem1', 'unfounded_abs_count_annual',
                  'third_of_hours_count_sem1', 'third_of_hours_count_annual')

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

    def get_third_of_hours_count_annual(self, obj):
        return self.get_third_of_hours_count_by_semester(obj, 1) + \
               self.get_third_of_hours_count_by_semester(obj, 2)
