from django.db import models
from django.contrib.postgres.fields import JSONField


class StudentAtRiskCounts(models.Model):
    year = models.PositiveSmallIntegerField()
    month = models.PositiveSmallIntegerField()
    by_country = models.BooleanField(default=False)
    school_unit = models.ForeignKey(
        'schools.RegisteredSchoolUnit', on_delete=models.CASCADE, null=True, blank=True,
        related_name='student_at_risk_counts', related_query_name='student_at_risk_counts'
    )
    study_class = models.ForeignKey(
        'study_classes.StudyClass', on_delete=models.CASCADE, null=True, blank=True,
        related_name='student_at_risk_counts', related_query_name='student_at_risk_counts'
    )
    daily_counts = JSONField(default=list)

    objects = models.Manager()

    def __str__(self):
        return f'StudentAtRiskCounts {self.id}'
