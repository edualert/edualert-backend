# this should be run using this command:
# ./manage.py runscript load_initial_data

from django.core.management import call_command

from edualert.academic_programs.models import GenericAcademicProgram
from edualert.schools.models import SchoolUnitCategory


def run():
    SchoolUnitCategory.objects.all().delete()
    GenericAcademicProgram.objects.all().delete()

    call_command('loaddata', 'categories.json')
    call_command('loaddata', 'academic_profiles.json')
    call_command('loaddata', 'generic_academic_programs.json')
