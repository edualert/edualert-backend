from django.contrib.postgres.fields import JSONField
from django.db import models


class SchoolUnitEnrollmentStats(models.Model):
    year = models.PositiveSmallIntegerField()
    month = models.PositiveSmallIntegerField()
    daily_statistics = JSONField(default=list)

    objects = models.Manager()

    def __str__(self):
        return f'SchoolUniEnrollmentStats {self.id}'


class SchoolUnitStats(models.Model):
    school_unit = models.ForeignKey(
        'schools.RegisteredSchoolUnit', on_delete=models.CASCADE,
        related_name='school_unit_stats', related_query_name='school_unit_stats'
    )
    school_unit_name = models.CharField(max_length=64)
    academic_year = models.PositiveSmallIntegerField()

    avg_sem1 = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    avg_sem2 = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    avg_annual = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)

    unfounded_abs_avg_sem1 = models.PositiveSmallIntegerField(null=True, blank=True)
    unfounded_abs_avg_sem2 = models.PositiveSmallIntegerField(null=True, blank=True)
    unfounded_abs_avg_annual = models.PositiveSmallIntegerField(null=True, blank=True)

    objects = models.Manager()

    class Meta:
        verbose_name_plural = 'school unit stats'

    def __str__(self):
        return f'SchoolUnitStats {self.id}'
