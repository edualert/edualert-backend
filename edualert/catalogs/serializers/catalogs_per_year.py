from rest_framework import serializers

from edualert.catalogs.models import StudentCatalogPerYear
from edualert.profiles.serializers.users import StudentBaseSerializer


class StudentCatalogPerYearSerializer(serializers.ModelSerializer):
    student = StudentBaseSerializer()

    class Meta:
        model = StudentCatalogPerYear
        fields = (
            'id', 'student', 'avg_sem1', 'avg_sem2', 'avg_annual', 'avg_final', 'abs_count_sem1', 'abs_count_sem2',
            'abs_count_annual', 'founded_abs_count_sem1', 'founded_abs_count_sem2', 'founded_abs_count_annual', 'unfounded_abs_count_sem1',
            'unfounded_abs_count_sem2', 'unfounded_abs_count_annual'
        )


class CatalogsPerYearRemarksSerializer(serializers.ModelSerializer):
    remarks = serializers.CharField(max_length=500, allow_blank=True, allow_null=True)

    class Meta:
        model = StudentCatalogPerYear
        fields = ('remarks',)
