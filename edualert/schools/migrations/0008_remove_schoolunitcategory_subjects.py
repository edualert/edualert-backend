# Generated by Django 3.0.4 on 2020-06-29 10:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0007_auto_20200504_1339'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='schoolunitcategory',
            name='subjects',
        ),
    ]