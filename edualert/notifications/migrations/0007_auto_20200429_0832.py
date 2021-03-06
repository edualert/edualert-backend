# Generated by Django 3.0.4 on 2020-04-29 08:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('study_classes', '0006_auto_20200422_0930'),
        ('profiles', '0012_auto_20200415_1238'),
        ('notifications', '0006_auto_20200428_1444'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='notification',
            name='target_study_class_grade',
        ),
        migrations.RemoveField(
            model_name='notification',
            name='target_study_class_letter',
        ),
        migrations.RemoveField(
            model_name='targetuserthrough',
            name='child',
        ),
        migrations.RemoveField(
            model_name='targetuserthrough',
            name='child_full_name',
        ),
        migrations.AddField(
            model_name='targetuserthrough',
            name='children',
            field=models.ManyToManyField(blank=True, help_text='Only if the target is one parent.', related_name='_targetuserthrough_children_+', to='profiles.UserProfile'),
        ),
        migrations.AlterField(
            model_name='notification',
            name='target_study_class',
            field=models.ForeignKey(blank=True, help_text='For all receiver types except for one parent (who can have children in different study classes).', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='received_notifications', related_query_name='received_notification', to='study_classes.StudyClass'),
        ),
    ]
