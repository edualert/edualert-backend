# Generated by Django 3.0.4 on 2020-05-04 13:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('study_classes', '0006_auto_20200422_0930'),
    ]

    operations = [
        migrations.AlterField(
            model_name='teacherclassthrough',
            name='subject_name',
            field=models.CharField(max_length=100),
        ),
    ]