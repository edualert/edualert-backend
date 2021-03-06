# Generated by Django 3.0.4 on 2020-04-28 13:21

from django.db import migrations, models
from django.db.models import IntegerChoices, TextChoices


def convert_notification_receiver_types(apps, schema_editor):
    Notification = apps.get_model('notifications', 'Notification')

    class OldReceiverTypes(IntegerChoices):
        CLASS_STUDENTS = 1
        CLASS_PARENTS = 2
        ONE_STUDENT = 3
        ONE_PARENT = 4

    class NewReceiverTypes(TextChoices):
        CLASS_STUDENTS = 'CLASS_STUDENTS'
        CLASS_PARENTS = 'CLASS_PARENTS'
        ONE_STUDENT = 'ONE_STUDENT'
        ONE_PARENT = 'ONE_PARENT'

    for notification in Notification.objects.all():
        receiver_type = int(notification.receiver_type)

        type_mapping = {
            OldReceiverTypes.CLASS_STUDENTS: NewReceiverTypes.CLASS_STUDENTS,
            OldReceiverTypes.CLASS_PARENTS: NewReceiverTypes.CLASS_PARENTS,
            OldReceiverTypes.ONE_STUDENT: NewReceiverTypes.ONE_STUDENT,
            OldReceiverTypes.ONE_PARENT: NewReceiverTypes.ONE_PARENT
        }

        notification.receiver_type = type_mapping[receiver_type]
        notification.save()


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0004_auto_20200415_1220'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='receiver_type',
            field=models.CharField(choices=[('1', 'Class students'), ('2', 'Class parents'), ('3', 'One student'), ('4', 'One parent')], max_length=64),
        ),
        migrations.AlterField(
            model_name='notification',
            name='title',
            field=models.CharField(max_length=100),
        ),
        migrations.RunPython(code=convert_notification_receiver_types, reverse_code=migrations.RunPython.noop)
    ]
