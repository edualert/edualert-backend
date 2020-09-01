# Generated by Django 3.0.4 on 2020-04-16 14:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('subjects', '0006_auto_20200413_0914'),
    ]

    operations = [
        migrations.AlterField(
            model_name='programsubjectthrough',
            name='subject',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='program_subjects_through', related_query_name='program_subject_through', to='subjects.Subject'),
        ),
    ]
