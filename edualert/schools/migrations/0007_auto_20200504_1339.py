# Generated by Django 3.0.4 on 2020-05-04 13:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0006_schoolunitcategory_subjects'),
    ]

    operations = [
        migrations.AlterField(
            model_name='registeredschoolunit',
            name='address',
            field=models.CharField(max_length=100),
        ),
    ]
