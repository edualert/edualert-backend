# this should be run using this command:
# ./manage.py runscript load_highschool_curriculum_seral
from django.db import transaction

from edualert.academic_programs.models import GenericAcademicProgram
from edualert.study_classes.constants import CLASS_GRADE_MAPPING
from edualert.subjects.models import Subject, ProgramSubjectThrough

HIGHSCHOOL_SERAL = {
    "subjects": [
        {
            'subject': 'Limba și literatura română',
            'grades': ['IX', 'X', 'XI'],
            'weekly_hours_count': [3, 2, 2]
        },
        {
            'subject': 'Limba modernă 1',
            'grades': ['IX', 'X', 'XI'],
            'weekly_hours_count': [2, 1, 2]
        },
        {
            'subject': 'Limba modernă 2',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [2, 1]
        },
        {
            'subject': 'Matematică',
            'grades': ['IX', 'X', 'XI'],
            'weekly_hours_count': [2, 1, 2]
        },
        {
            'subject': 'Fizică',
            'grades': ['IX', 'X', 'XI'],
            'weekly_hours_count': [2, 1, 2]
        },
        {
            'subject': 'Chimie',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Biologie',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Istorie',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Geografie',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Socio-umane / Educaţie pentru societate',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Educație antreprenorială',
            'grades': ['X'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Tehnologia informației și a comunicațiilor',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
        }
    ],
    "optional_subjects_weekly_hours": {
        "IX": 6,
        "X": 5,
        "XI": 9
    }
}

HIGHSCHOOL_SERAL_HU_SUBJECTS = HIGHSCHOOL_SERAL["subjects"].copy()
HIGHSCHOOL_SERAL_HU_SUBJECTS.append({
    'subject': 'Limba și literatura maghiară',
    'grades': ['IX', 'X', 'XI'],
    'weekly_hours_count': [3, 2, 2]

})
HIGHSCHOOL_SERAL_HU = {
    "subjects": HIGHSCHOOL_SERAL_HU_SUBJECTS,
    "optional_subjects_weekly_hours": HIGHSCHOOL_SERAL["optional_subjects_weekly_hours"]
}


def run():
    with transaction.atomic():
        add_data_for_highschool(GenericAcademicProgram.objects.filter(name__in=['Servicii - Seral - Comerț',
                                                                                'Servicii - Seral - Economic',
                                                                                'Servicii - Seral - Turism și Alimentație',
                                                                                'Servicii - Seral - Administrativ',
                                                                                'Servicii - Seral - Estetica și Igiena Corpului Omenesc',
                                                                                'Tehnic - Seral - Mecanică',
                                                                                'Tehnic - Seral - Electromecanică',
                                                                                'Tehnic - Seral - Electronică Automatizări',
                                                                                'Tehnic - Seral - Electric',
                                                                                'Tehnic - Seral - Construcții, Instalații și Lucrări Publice',
                                                                                'Tehnic - Seral - Industrie Textilă și Pielărie',
                                                                                'Tehnic - Seral - Fabricarea Produselor din Lemn',
                                                                                'Tehnic - Seral - Tehnice Poligrafice',
                                                                                'Tehnic - Seral - Producție Media',
                                                                                'Tehnic - Seral - Transporturi',
                                                                                'Tehnic - Seral - Chimie Industrială',
                                                                                'Tehnic - Seral - Materiale de Construcții',
                                                                                'Resurse Naturale și Protecția Mediului - Seral - Chimie Industrială',
                                                                                'Resurse Naturale și Protecția Mediului - Seral - Agricultură',
                                                                                'Resurse Naturale și Protecția Mediului - Seral - Industrie Alimentară',
                                                                                'Resurse Naturale și Protecția Mediului - Seral - Silvicultură',
                                                                                'Resurse Naturale și Protecția Mediului - Seral - Protecția Mediului']),
                                HIGHSCHOOL_SERAL)
        add_data_for_highschool(GenericAcademicProgram.objects.filter(name__in=['Servicii - Seral - Comerț - Limba Maghiară',
                                                                                'Servicii - Seral - Economic - Limba Maghiară',
                                                                                'Servicii - Seral - Turism și Alimentație - Limba Maghiară',
                                                                                'Servicii - Seral - Administrativ - Limba Maghiară',
                                                                                'Servicii - Seral - Estetica și Igiena Corpului Omenesc - Limba Maghiară',
                                                                                'Tehnic - Seral - Mecanică - Limba Maghiară',
                                                                                'Tehnic - Seral - Electromecanică - Limba Maghiară',
                                                                                'Tehnic - Seral - Electronică Automatizări - Limba Maghiară',
                                                                                'Tehnic - Seral - Electric - Limba Maghiară',
                                                                                'Tehnic - Seral - Construcții, Instalații și Lucrări Publice - Limba Maghiară',
                                                                                'Tehnic - Seral - Industrie Textilă și Pielărie - Limba Maghiară',
                                                                                'Tehnic - Seral - Fabricarea Produselor din Lemn - Limba Maghiară',
                                                                                'Tehnic - Seral - Tehnice Poligrafice - Limba Maghiară',
                                                                                'Tehnic - Seral - Producție Media - Limba Maghiară',
                                                                                'Tehnic - Seral - Transporturi - Limba Maghiară',
                                                                                'Tehnic - Seral - Chimie Industrială - Limba Maghiară',
                                                                                'Tehnic - Seral - Materiale de Construcții - Limba Maghiară',
                                                                                'Resurse Naturale și Protecția Mediului - Seral - Chimie Industrială - Limba Maghiară',
                                                                                'Resurse Naturale și Protecția Mediului - Seral - Agricultură - Limba Maghiară',
                                                                                'Resurse Naturale și Protecția Mediului - Seral - Industrie Alimentară - Limba Maghiară',
                                                                                'Resurse Naturale și Protecția Mediului - Seral - Silvicultură - Limba Maghiară',
                                                                                'Resurse Naturale și Protecția Mediului - Seral - Protecția Mediului - Limba Maghiară']),
                                HIGHSCHOOL_SERAL_HU)


def add_data_for_highschool(programs, program_map):
    for program in programs:
        program.optional_subjects_weekly_hours = program_map['optional_subjects_weekly_hours']
        program.save()
        for item in program_map['subjects']:
            subject = get_subject_by_name(item['subject'])
            for class_grade, weekly_hours_count in zip(item['grades'], item['weekly_hours_count']):
                ProgramSubjectThrough.objects.create(generic_academic_program=program, subject=subject, subject_name=subject.name,
                                                     class_grade=class_grade, class_grade_arabic=CLASS_GRADE_MAPPING[class_grade],
                                                     weekly_hours_count=weekly_hours_count, is_mandatory=True)


def get_subject_by_name(name):
    subject, created = Subject.objects.get_or_create(name=name)
    return subject
