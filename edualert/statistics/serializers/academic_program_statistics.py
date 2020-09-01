from rest_framework import serializers

from edualert.academic_programs.models import AcademicProgram


class AcademicProgramsAverageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicProgram
        fields = ('id', 'name', 'avg_sem1', 'avg_annual')


class AcademicProgramsAbsencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicProgram
        fields = ('id', 'name', 'unfounded_abs_avg_sem1', 'unfounded_abs_avg_annual')


class AcademicProgramsRiskSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicProgram
        fields = ('id', 'name', 'students_at_risk_count')
