# Generated by Django 3.0.4 on 2020-05-26 10:58

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('schools', '0007_auto_20200504_1339'),
    ]

    operations = [
        migrations.CreateModel(
            name='SchoolUnitEnrollmentStats',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.PositiveSmallIntegerField()),
                ('month', models.PositiveSmallIntegerField()),
                ('daily_statistics', django.contrib.postgres.fields.jsonb.JSONField(default=dict)),
            ],
        ),
        migrations.CreateModel(
            name='StudentAtRiskCounts',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.PositiveSmallIntegerField()),
                ('month', models.PositiveSmallIntegerField()),
                ('by_country', models.BooleanField(default=False)),
                ('daily_counts', django.contrib.postgres.fields.jsonb.JSONField(default=dict)),
                ('study_class', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='student_at_risk_counts', related_query_name='student_at_risk_counts', to='study_classes.StudyClass')),
                ('school_unit', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='student_at_risk_counts', related_query_name='student_at_risk_counts', to='schools.RegisteredSchoolUnit'))
            ],
        ),
        migrations.CreateModel(
            name='SchoolUnitStats',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('school_unit_name', models.CharField(max_length=64)),
                ('academic_year', models.PositiveSmallIntegerField()),
                ('avg_sem1', models.DecimalField(blank=True, decimal_places=2, max_digits=4, null=True)),
                ('avg_annual', models.DecimalField(blank=True, decimal_places=2, max_digits=4, null=True)),
                ('unfounded_abs_count_sem1', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('unfounded_abs_count_annual', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('school_unit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='school_unit_stats', related_query_name='school_unit_stats', to='schools.RegisteredSchoolUnit')),
            ],
        ),
    ]
