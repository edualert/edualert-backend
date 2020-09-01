# Generated by Django 3.0.4 on 2020-05-19 10:24

from django.db import migrations, models
from django.db.models import TextChoices, IntegerChoices


def convert_grades(apps, schema_editor):
    ExaminationGrade = apps.get_model('catalogs', 'ExaminationGrade')
    SubjectGrade = apps.get_model('catalogs', 'SubjectGrade')

    class GradeTypes(TextChoices):
        REGULAR = "REGULAR"
        THESIS = "THESIS"

    class ExaminationTypes(TextChoices):
        WRITTEN = "WRITTEN"
        ORAL = "ORAL"

    class ExaminationGradeTypes(TextChoices):
        SECOND_EXAMINATION = 'SECOND_EXAMINATION'
        DIFFERENCE = 'DIFFERENCE'

    class OldGradeTypes(IntegerChoices):
        REGULAR = 1
        THESIS = 2

    class OldExaminationTypes(IntegerChoices):
        WRITTEN = 1
        ORAL = 2

    class OldExaminationGradeTypes(IntegerChoices):
        SECOND_EXAMINATION = 1
        DIFFERENCE = 2

    for grade in ExaminationGrade.objects.all():
        if grade.grade_type == OldExaminationGradeTypes.SECOND_EXAMINATION:
            grade.grade_type = ExaminationGradeTypes.SECOND_EXAMINATION
        elif grade.grade_type == OldExaminationGradeTypes.DIFFERENCE:
            grade.grade_type = ExaminationGradeTypes.DIFFERENCE

        if grade.examination_type == OldExaminationTypes.WRITTEN:
            grade.examination_type = ExaminationTypes.WRITTEN
        elif grade.examination_type == OldExaminationTypes.ORAL:
            grade.examination_type = ExaminationTypes.ORAL
        grade.save()

    for grade in SubjectGrade.objects.all():
        if grade.grade_type == OldGradeTypes.REGULAR:
            grade.grade_type = GradeTypes.REGULAR
        elif grade.grade_type == OldGradeTypes.THESIS:
            grade.grade_type = GradeTypes.THESIS
        grade.save()


class Migration(migrations.Migration):

    dependencies = [
        ('catalogs', '0007_examinationgrade_semester'),
    ]

    operations = [
        migrations.AlterField(
            model_name='examinationgrade',
            name='examination_type',
            field=models.CharField(choices=[('WRITTEN', 'Written'), ('ORAL', 'Oral')], max_length=64),
        ),
        migrations.AlterField(
            model_name='examinationgrade',
            name='grade_type',
            field=models.CharField(choices=[('SECOND_EXAMINATION', 'Second examination'), ('DIFFERENCE', 'Difference')], max_length=64),
        ),
        migrations.AlterField(
            model_name='examinationgrade',
            name='semester',
            field=models.PositiveSmallIntegerField(blank=True, help_text='Only for Difference grades.', null=True),
        ),
        migrations.AlterField(
            model_name='subjectgrade',
            name='grade_type',
            field=models.CharField(choices=[('REGULAR', 'Regular'), ('THESIS', 'Thesis')], max_length=64),
        ),
        migrations.RunPython(code=convert_grades, reverse_code=migrations.RunPython.noop)
    ]
