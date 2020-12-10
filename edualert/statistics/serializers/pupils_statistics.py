from rest_framework import serializers

from edualert.catalogs.models import StudentCatalogPerYear
from edualert.catalogs.utils import get_behavior_grade_limit
from edualert.profiles.serializers import LabelSerializer, UserProfileBaseSerializer
from edualert.schools.serializers import RegisteredSchoolUnitBaseSerializer
from edualert.study_classes.serializers import StudyClassNameSerializer


class PupilStatisticsBaseSerializer(serializers.ModelSerializer):
    labels = LabelSerializer(source='student.labels', many=True)
    student_in_class = StudyClassNameSerializer(source='study_class')
    academic_program_name = serializers.CharField(source='study_class.academic_program_name')
    behavior_grade_limit = serializers.SerializerMethodField()
    risk_description = serializers.CharField(source='student.risk_description')

    class Meta:
        model = StudentCatalogPerYear


class PupilStatisticsForORSSerializer(PupilStatisticsBaseSerializer):
    student = serializers.SerializerMethodField()
    school_unit = RegisteredSchoolUnitBaseSerializer(source='student.school_unit')

    class Meta(PupilStatisticsBaseSerializer.Meta):
        fields = ('id', 'student', 'school_unit', 'avg_sem1', 'avg_sem2', 'avg_final', 'second_examinations_count',
                  'unfounded_abs_count_sem1', 'unfounded_abs_count_sem2', 'unfounded_abs_count_annual',
                  'behavior_grade_sem1', 'behavior_grade_sem2', 'behavior_grade_annual', 'behavior_grade_limit',
                  'labels', 'risk_description', 'student_in_class', 'academic_program_name')

    @staticmethod
    def get_student(obj):
        return 'Elev {}'.format(obj.student_id)

    @staticmethod
    def get_behavior_grade_limit(obj):
        academic_profile = obj.student.school_unit.academic_profile
        return get_behavior_grade_limit(academic_profile)


class PupilStatisticsForSchoolEmployeeSerializer(PupilStatisticsBaseSerializer):
    student = UserProfileBaseSerializer()

    class Meta(PupilStatisticsBaseSerializer.Meta):
        fields = ('id', 'student', 'avg_sem1', 'avg_sem2', 'avg_final', 'second_examinations_count',
                  'unfounded_abs_count_sem1', 'unfounded_abs_count_sem2', 'unfounded_abs_count_annual',
                  'behavior_grade_sem1', 'behavior_grade_sem2', 'behavior_grade_annual', 'behavior_grade_limit',
                  'labels', 'risk_description', 'student_in_class', 'academic_program_name')

    def get_behavior_grade_limit(self, obj):
        return self.context.get('behavior_grade_limit', 6)


class StudentsAveragesSerializer(serializers.ModelSerializer):
    student = UserProfileBaseSerializer()

    class Meta:
        model = StudentCatalogPerYear
        fields = ('id', 'student', 'avg_sem1', 'avg_final')


class StudentsAbsencesSerializer(serializers.ModelSerializer):
    student = UserProfileBaseSerializer()

    class Meta:
        model = StudentCatalogPerYear
        fields = ('id', 'student', 'unfounded_abs_count_sem1', 'unfounded_abs_count_annual')


class StudentsBehaviorGradeSerializer(serializers.ModelSerializer):
    student = UserProfileBaseSerializer()
    behavior_grade_limit = serializers.SerializerMethodField()

    class Meta:
        model = StudentCatalogPerYear
        fields = ('id', 'student', 'behavior_grade_sem1', 'behavior_grade_annual', 'behavior_grade_limit')

    def get_behavior_grade_limit(self, obj):
        return self.context.get('behavior_grade_limit', 6)


class StudentAtRiskSerializer(serializers.ModelSerializer):
    student = UserProfileBaseSerializer()
    behavior_grade_limit = serializers.SerializerMethodField()

    class Meta:
        model = StudentCatalogPerYear
        fields = ('id', 'student', 'avg_sem1', 'avg_final', 'unfounded_abs_count_sem1', 'unfounded_abs_count_annual',
                  'second_examinations_count', 'behavior_grade_sem1', 'behavior_grade_annual', 'behavior_grade_limit')

    def get_behavior_grade_limit(self, obj):
        return self.context.get('behavior_grade_limit', 6)


class SchoolStudentAtRiskSerializer(StudentAtRiskSerializer):
    study_class = StudyClassNameSerializer()

    class Meta(StudentAtRiskSerializer.Meta):
        fields = ('id', 'student', 'avg_sem1', 'avg_final', 'unfounded_abs_count_sem1', 'unfounded_abs_count_annual',
                  'second_examinations_count', 'behavior_grade_sem1', 'behavior_grade_annual', 'behavior_grade_limit',
                  'study_class')
