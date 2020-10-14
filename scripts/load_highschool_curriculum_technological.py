# this should be run using this command:
# ./manage.py runscript load_highschool_curriculum_technological
from django.db import transaction

from edualert.academic_programs.models import GenericAcademicProgram
from edualert.study_classes.constants import CLASS_GRADE_MAPPING
from edualert.subjects.models import Subject, ProgramSubjectThrough

HIGHSCHOOL_TECHNOLOGICAL_GR_A = {
    "subjects": [
        {
            'subject': 'Limba și literatura română',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [3, 3, 3, 3]
        },
        {
            'subject': 'Limba modernă 1',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 2, 2, 2]
        },
        {
            'subject': 'Limba modernă 2',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 1, 2, 2]
        },
        {
            'subject': 'Matematică',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [3, 3, 3, 3]
        },
        {
            'subject': 'Fizică',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [2, 2]
        },
        {
            'subject': 'Chimie',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [2, 1]
        },
        {
            'subject': 'Biologie',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Istorie',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 2, 1]
        },
        {
            'subject': 'Geografie',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 2]
        },
        {
            'subject': 'Socio-umane / Educaţie pentru societate',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 2, 2]
        },
        {
            'subject': 'Religie',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Educație fizică',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 2, 1, 1]
        },
        {
            'subject': 'Tehnologia informației și a comunicațiilor',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Educație antreprenorială',
            'grades': ['X'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Stagii de pregătire practică',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [30, 30, 30, 30]
        }
    ],
    "optional_subjects_weekly_hours": {
        "IX": 9,
        "X": 10,
        "XI": 12,
        "XII": 11
    }
}
HIGHSCHOOL_TECHNOLOGICAL_GR_B = {
    "subjects": [
        {
            'subject': 'Limba și literatura română',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [3, 3, 3, 3]
        },
        {
            'subject': 'Limba modernă 1',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 2, 2, 2]
        },
        {
            'subject': 'Limba modernă 2',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 1, 2, 2]
        },
        {
            'subject': 'Matematică',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [3, 3, 3, 3]
        },
        {
            'subject': 'Fizică',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 2, 2, 2]
        },
        {
            'subject': 'Chimie',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 1, 1, 1]
        },
        {
            'subject': 'Biologie',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Istorie',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Geografie',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Socio-umane / Educaţie pentru societate',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Religie',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Educație fizică',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Tehnologia informației și a comunicațiilor',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Educație antreprenorială',
            'grades': ['X'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Stagii de pregătire practică',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [30, 30, 30, 30]
        }
    ],
    "optional_subjects_weekly_hours": {
        "IX": 9,
        "X": 10,
        "XI": 11,
        "XII": 11
    }
}
HIGHSCHOOL_TECHNOLOGICAL_GR_C = {
    "subjects": [
        {
            'subject': 'Limba și literatura română',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [3, 3, 3, 3]
        },
        {
            'subject': 'Limba modernă 1',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 2, 2, 2]
        },
        {
            'subject': 'Limba modernă 2',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 1, 2, 2]
        },
        {
            'subject': 'Matematică',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [3, 3, 3, 3]
        },
        {
            'subject': 'Fizică',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 2, 1, 1]
        },
        {
            'subject': 'Chimie',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 1, 2, 2]
        },
        {
            'subject': 'Biologie',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Istorie',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Geografie',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Socio-umane / Educaţie pentru societate',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Religie',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Educație fizică',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Tehnologia informației și a comunicațiilor',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Educație antreprenorială',
            'grades': ['X'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Stagii de pregătire practică',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [30, 30, 30, 30]
        }
    ],
    "optional_subjects_weekly_hours": {
        "IX": 9,
        "X": 10,
        "XI": 11,
        "XII": 11
    }
}
HIGHSCHOOL_TECHNOLOGICAL_GR_D = {
    "subjects": [
        {
            'subject': 'Limba și literatura română',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [3, 3, 3, 3]
        },
        {
            'subject': 'Limba modernă 1',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 2, 2, 2]
        },
        {
            'subject': 'Limba modernă 2',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 1, 2, 2]
        },
        {
            'subject': 'Matematică',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [3, 3, 3, 3]
        },
        {
            'subject': 'Fizică',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [2, 2]
        },
        {
            'subject': 'Chimie',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 1, 2, 1]
        },
        {
            'subject': 'Biologie',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 2]
        },
        {
            'subject': 'Istorie',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Geografie',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Socio-umane / Educaţie pentru societate',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Religie',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Educație fizică',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Tehnologia informației și a comunicațiilor',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Educație antreprenorială',
            'grades': ['X'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Stagii de pregătire practică',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [30, 30, 30, 30]
        }
    ],
    "optional_subjects_weekly_hours": {
        "IX": 9,
        "X": 10,
        "XI": 11,
        "XII": 11
    }
}


def run():
    with transaction.atomic():
        add_data_for_highschool(GenericAcademicProgram.objects.filter(name__in=['Servicii - Comerț',
                                                                                'Servicii - Economic',
                                                                                'Servicii - Turism și Alimentație',
                                                                                'Servicii - Administrativ',
                                                                                'Servicii - Estetica și Igiena Corpului Omenesc',
                                                                                'Servicii - Special - Comerț',
                                                                                'Servicii - Special - Economic',
                                                                                'Servicii - Special - Turism și Alimentație',
                                                                                'Servicii - Special - Administrativ',
                                                                                'Servicii - Special - Estetica și Igiena Corpului Omenesc']),
                                HIGHSCHOOL_TECHNOLOGICAL_GR_A)
        add_data_for_highschool(GenericAcademicProgram.objects.filter(name__in=['Tehnic - Mecanică',
                                                                                'Tehnic - Electromecanică',
                                                                                'Tehnic - Electronică Automatizări',
                                                                                'Tehnic - Electric',
                                                                                'Tehnic - Construcții, Instalații și Lucrări Publice',
                                                                                'Tehnic - Industrie Textilă și Pielărie',
                                                                                'Tehnic - Fabricarea Produselor din Lemn',
                                                                                'Tehnic - Tehnice Poligrafice',
                                                                                'Tehnic - Producție Media',
                                                                                'Tehnic - Transporturi',
                                                                                'Tehnic - Special - Mecanică',
                                                                                'Tehnic - Special - Electromecanică',
                                                                                'Tehnic - Special - Electronică Automatizări',
                                                                                'Tehnic - Special - Electric',
                                                                                'Tehnic - Special - Construcții, Instalații și Lucrări Publice',
                                                                                'Tehnic - Special - Industrie Textilă și Pielărie',
                                                                                'Tehnic - Special - Fabricarea Produselor din Lemn',
                                                                                'Tehnic - Special - Tehnice Poligrafice',
                                                                                'Tehnic - Special - Producție Media']),
                                HIGHSCHOOL_TECHNOLOGICAL_GR_B)
        add_data_for_highschool(GenericAcademicProgram.objects.filter(name__in=['Tehnic - Chimie Industrială',
                                                                                'Tehnic - Materiale de Construcții',
                                                                                'Tehnic - Special - Chimie Industrială',
                                                                                'Tehnic - Special - Materiale de Construcții',
                                                                                'Resurse Naturale și Protecția Mediului - Chimie Industrială']),
                                HIGHSCHOOL_TECHNOLOGICAL_GR_C)
        add_data_for_highschool(GenericAcademicProgram.objects.filter(name__in=['Resurse Naturale și Protecția Mediului - Agricultură',
                                                                                'Resurse Naturale și Protecția Mediului - Industrie Alimentară',
                                                                                'Resurse Naturale și Protecția Mediului - Silvicultură',
                                                                                'Resurse Naturale și Protecția Mediului - Protecția Mediului',
                                                                                'Resurse Naturale și Protecția Mediului - Special - Agricultură',
                                                                                'Resurse Naturale și Protecția Mediului - Special - Industrie Alimentară',
                                                                                'Resurse Naturale și Protecția Mediului - Special - Silvicultură',
                                                                                'Resurse Naturale și Protecția Mediului - Special - Protecția Mediului']),
                                HIGHSCHOOL_TECHNOLOGICAL_GR_D)


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
