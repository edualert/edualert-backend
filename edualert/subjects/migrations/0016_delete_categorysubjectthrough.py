# Generated by Django 3.0.4 on 2020-06-29 10:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0008_remove_schoolunitcategory_subjects'),
        ('subjects', '0015_remove_programsubjectthrough_is_core_subject'),
    ]

    operations = [
        migrations.DeleteModel(
            name='CategorySubjectThrough',
        ),
    ]
