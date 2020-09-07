# Generated by Django 3.0.4 on 2020-03-31 15:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('study_classes', '0001_initial'),
        ('profiles', '0006_userprofile_taught_subjects'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='student_in_class',
            field=models.ForeignKey(blank=True, help_text='Only for students.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='students', related_query_name='student', to='study_classes.StudyClass'),
        ),
    ]