# Generated by Django 3.0.4 on 2020-05-26 15:07

from django.db import migrations

from edualert.academic_calendars.utils import get_current_academic_calendar


def create_stats_for_schools(apps, schema_editor):
    RegisteredSchoolUnit = apps.get_model('schools', 'RegisteredSchoolUnit')
    SchoolUnitStats = apps.get_model('statistics', 'SchoolUnitStats')

    calendar = get_current_academic_calendar()
    if calendar:
        for school in RegisteredSchoolUnit.objects.all():
            SchoolUnitStats.objects.create(school_unit=school, school_unit_name=school.name, academic_year=calendar.academic_year)


class Migration(migrations.Migration):

    dependencies = [
        ('statistics', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='schoolunitstats',
            old_name='unfounded_abs_count_annual',
            new_name='unfounded_abs_avg_annual',
        ),
        migrations.RenameField(
            model_name='schoolunitstats',
            old_name='unfounded_abs_count_sem1',
            new_name='unfounded_abs_avg_sem1',
        ),
        migrations.RunPython(code=create_stats_for_schools, reverse_code=migrations.RunPython.noop),
    ]
