# Generated by Django 3.0.4 on 2020-05-04 13:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subjects', '0009_subject_should_be_in_taught_subjects'),
    ]

    operations = [
        migrations.AlterField(
            model_name='categorysubjectthrough',
            name='subject_name',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='programsubjectthrough',
            name='subject_name',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='subject',
            name='name',
            field=models.CharField(max_length=100, unique=True),
        ),
    ]
