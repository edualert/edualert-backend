from rest_framework import serializers

from edualert.study_classes.models import StudyClass


class StudyClassesAveragesSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudyClass
        fields = ('id', 'class_grade', 'class_letter', 'avg_sem1', 'avg_annual')


class StudyClassesAbsencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudyClass
        fields = ('id', 'class_grade', 'class_letter', 'unfounded_abs_avg_sem1', 'unfounded_abs_avg_annual')


class StudyClassesRiskSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudyClass
        fields = ('id', 'class_grade', 'class_letter', 'students_at_risk_count')
