# Generated by Django 3.0.4 on 2020-05-29 14:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('catalogs', '0012_remove_studentcatalogperyear_avg_after_2nd_examination'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='examinationgrade',
            options={'ordering': ['-taken_at', '-created']},
        ),
        migrations.AlterModelOptions(
            name='subjectabsence',
            options={'ordering': ['-taken_at', '-created']},
        ),
        migrations.AlterModelOptions(
            name='subjectgrade',
            options={'ordering': ['-taken_at', '-created']},
        ),
    ]
