import factory
from factory.django import DjangoModelFactory

from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.statistics.models import SchoolUnitStats, StudentAtRiskCounts, SchoolUnitEnrollmentStats


class SchoolUnitStatsFactory(DjangoModelFactory):
    class Meta:
        model = SchoolUnitStats

    school_unit = factory.SubFactory(
        RegisteredSchoolUnitFactory
    )
    school_unit_name = factory.SelfAttribute('school_unit.name')
    academic_year = 2020


class StudentAtRiskCountsFactory(DjangoModelFactory):
    class Meta:
        model = StudentAtRiskCounts

    year = 2020
    month = 4
    daily_counts = [{
        'day': 1,
        'weekday': 'Lu',
        'count': 0
    }]


class SchoolUnitEnrollmentStatsFactory(DjangoModelFactory):
    class Meta:
        model = SchoolUnitEnrollmentStats

    year = 2020
    month = 2
    daily_statistics = [{
        'day': 1,
        'weekday': 'Lu',
        'count': 0
    }]
