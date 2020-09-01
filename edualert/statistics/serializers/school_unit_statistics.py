from rest_framework import serializers

from edualert.schools.models import RegisteredSchoolUnit
from edualert.statistics.models import SchoolUnitStats


class SchoolUnitStatsAverageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolUnitStats
        fields = ('school_unit_name', 'avg_sem1', 'avg_annual')


class SchoolUnitStatsAbsencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolUnitStats
        fields = ('school_unit_name', 'unfounded_abs_avg_sem1', 'unfounded_abs_avg_annual')


class RegisteredSchoolUnitLastChangeInCatalogSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegisteredSchoolUnit
        fields = ('id', 'name', 'last_change_in_catalog')


class RegisteredSchoolUnitRiskSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegisteredSchoolUnit
        fields = ('id', 'name', 'students_at_risk_count')
