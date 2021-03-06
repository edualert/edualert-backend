# Generated by Django 3.0.4 on 2020-05-26 10:45

from django.db import migrations, models


def set_behavior_grades(apps, schema_editor):
    StudentCatalogPerYear = apps.get_model('catalogs', 'studentcatalogperyear')

    for catalog in StudentCatalogPerYear.objects.all():
        catalog.behavior_grade_sem1 = 10
        catalog.behavior_grade_sem2 = 10
        catalog.behavior_grade_annual = 10
        catalog.save()


class Migration(migrations.Migration):

    dependencies = [
        ('catalogs', '0010_auto_20200525_0938'),
    ]

    operations = [
        migrations.RunPython(code=set_behavior_grades, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name='studentcatalogperyear',
            name='behavior_grade_annual',
            field=models.DecimalField(decimal_places=2, default=10, max_digits=4),
        ),
        migrations.AlterField(
            model_name='studentcatalogperyear',
            name='behavior_grade_sem1',
            field=models.PositiveSmallIntegerField(default=10),
        ),
        migrations.AlterField(
            model_name='studentcatalogperyear',
            name='behavior_grade_sem2',
            field=models.PositiveSmallIntegerField(default=10),
        ),
    ]
