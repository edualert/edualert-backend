# Generated by Django 3.0.4 on 2020-05-28 12:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('catalogs', '0011_auto_20200526_1045'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='studentcatalogperyear',
            name='avg_after_2nd_examination',
        ),
    ]