# Generated by Django 3.0.4 on 2020-05-19 14:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('catalogs', '0008_auto_20200519_1024'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='examinationgrade',
            options={'ordering': ['-taken_at', 'created']},
        ),
        migrations.AlterModelOptions(
            name='subjectabsence',
            options={'ordering': ['-taken_at', 'created']},
        ),
        migrations.AlterModelOptions(
            name='subjectgrade',
            options={'ordering': ['-taken_at', 'created']},
        ),
    ]
