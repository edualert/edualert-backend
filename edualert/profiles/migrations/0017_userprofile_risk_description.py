# Generated by Django 3.0.4 on 2020-06-24 10:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0016_auto_20200623_1004'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='risk_description',
            field=models.CharField(blank=True, help_text='Only for students.', max_length=254, null=True),
        ),
    ]