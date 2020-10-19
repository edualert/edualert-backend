# this should be run using this command:
# ./manage.py runscript load_highschool_curriculum_prof
from django.db import transaction

from edualert.academic_programs.models import GenericAcademicProgram
from edualert.schools.models import SchoolUnitCategory
from edualert.study_classes.constants import CLASS_GRADE_MAPPING
from edualert.subjects.models import Subject, ProgramSubjectThrough

HIGHSCHOOL_PROF = {
    "subjects": [
        {
            'subject': 'Limba și literatura română',
            'grades': ['IX', 'X', 'XI'],
            'weekly_hours_count': [2, 2, 2]
        },
        {
            'subject': 'Limba modernă 1',
            'grades': ['IX', 'X', 'XI'],
            'weekly_hours_count': [1, 1, 2]
        },
        {
            'subject': 'Limba modernă 2',
            'grades': ['IX', 'X', 'XI'],
            'weekly_hours_count': [1, 1, 1]
        },
        {
            'subject': 'Matematică',
            'grades': ['IX', 'X', 'XI'],
            'weekly_hours_count': [3, 1, 1]
        },
        {
            'subject': 'Fizică',
            'grades': ['IX', 'X', 'XI'],
            'weekly_hours_count': [1, 1, 2]
        },
        {
            'subject': 'Chimie',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [2, 1]
        },
        {
            'subject': 'Biologie',
            'grades': ['IX'],
            'weekly_hours_count': [2]
        },
        {
            'subject': 'Istorie',
            'grades': ['IX'],
            'weekly_hours_count': [2]
        },
        {
            'subject': 'Geografie',
            'grades': ['IX'],
            'weekly_hours_count': [2]
        },
        {
            'subject': 'Socio-umane / Educaţie pentru societate',
            'grades': ['IX'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Socio-umane / Discipline psihologice și pedagogice',
            'grades': ['X'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Educație antreprenorială',
            'grades': ['XI'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Religie',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Educație fizică',
            'grades': ['IX', 'X', 'XI'],
            'weekly_hours_count': [2, 2, 2]
        },
        {
            'subject': 'Consiliere și orientare',
            'grades': ['IX', 'X', 'XI'],
            'weekly_hours_count': [1, 1, 1]
        },
        {
            'subject': 'Tehnologia informației și a comunicațiilor',
            'grades': ['IX'],
            'weekly_hours_count': [2]
        },
        {
            'subject': 'Stagii de pregătire practică',
            'grades': ['IX', 'X', 'XI'],
            'weekly_hours_count': [30, 30, 30]
        }
    ],
    "optional_subjects_weekly_hours": {
        "IX": 9,
        "X": 22,
        "XI": 21
    }
}

HIGHSCHOOL_PROF_HU_SUBJECTS = HIGHSCHOOL_PROF["subjects"].copy()
HIGHSCHOOL_PROF_HU_SUBJECTS.append({
    'subject': 'Limba și literatura maghiară',
    'grades': ['IX', 'X', 'XI'],
    'weekly_hours_count': [2, 2, 2]

})
HIGHSCHOOL_PROF_HU = {
    "subjects": HIGHSCHOOL_PROF_HU_SUBJECTS,
    "optional_subjects_weekly_hours": HIGHSCHOOL_PROF["optional_subjects_weekly_hours"]
}


def run():
    with transaction.atomic():
        add_data_for_highschool(['Servicii - Profesională - Comerț',
                                 'Servicii - Profesională - Economic',
                                 'Servicii - Profesională - Turism și Alimentație',
                                 'Servicii - Profesională - Administrativ',
                                 'Servicii - Profesională - Estetica și Igiena Corpului Omenesc',
                                 'Tehnic - Profesională - Mecanică',
                                 'Tehnic - Profesională - Electromecanică',
                                 'Tehnic - Profesională - Electronică Automatizări',
                                 'Tehnic - Profesională - Electric',
                                 'Tehnic - Profesională - Construcții, Instalații și Lucrări Publice',
                                 'Tehnic - Profesională - Industrie Textilă și Pielărie',
                                 'Tehnic - Profesională - Fabricarea Produselor din Lemn',
                                 'Tehnic - Profesională - Tehnice Poligrafice',
                                 'Tehnic - Profesională - Producție Media',
                                 'Tehnic - Profesională - Transporturi',
                                 'Tehnic - Profesională - Chimie Industrială',
                                 'Tehnic - Profesională - Materiale de Construcții',
                                 'Resurse Naturale și Protecția Mediului - Profesională - Chimie Industrială',
                                 'Resurse Naturale și Protecția Mediului - Profesională - Agricultură',
                                 'Resurse Naturale și Protecția Mediului - Profesională - Industrie Alimentară',
                                 'Resurse Naturale și Protecția Mediului - Profesională - Silvicultură',
                                 'Resurse Naturale și Protecția Mediului - Profesională - Protecția Mediului'],
                                HIGHSCHOOL_PROF)
        add_data_for_highschool(['Servicii - Profesională - Comerț - Limba Maghiară',
                                 'Servicii - Profesională - Economic - Limba Maghiară',
                                 'Servicii - Profesională - Turism și Alimentație - Limba Maghiară',
                                 'Servicii - Profesională - Administrativ - Limba Maghiară',
                                 'Servicii - Profesională - Estetica și Igiena Corpului Omenesc - Limba Maghiară',
                                 'Tehnic - Profesională - Mecanică - Limba Maghiară',
                                 'Tehnic - Profesională - Electromecanică - Limba Maghiară',
                                 'Tehnic - Profesională - Electronică Automatizări - Limba Maghiară',
                                 'Tehnic - Profesională - Electric - Limba Maghiară',
                                 'Tehnic - Profesională - Construcții, Instalații și Lucrări Publice - Limba Maghiară',
                                 'Tehnic - Profesională - Industrie Textilă și Pielărie - Limba Maghiară',
                                 'Tehnic - Profesională - Fabricarea Produselor din Lemn - Limba Maghiară',
                                 'Tehnic - Profesională - Tehnice Poligrafice - Limba Maghiară',
                                 'Tehnic - Profesională - Producție Media - Limba Maghiară',
                                 'Tehnic - Profesională - Transporturi - Limba Maghiară',
                                 'Tehnic - Profesională - Chimie Industrială - Limba Maghiară',
                                 'Tehnic - Profesională - Materiale de Construcții - Limba Maghiară',
                                 'Resurse Naturale și Protecția Mediului - Profesională - Chimie Industrială - Limba Maghiară',
                                 'Resurse Naturale și Protecția Mediului - Profesională - Agricultură - Limba Maghiară',
                                 'Resurse Naturale și Protecția Mediului - Profesională - Industrie Alimentară - Limba Maghiară',
                                 'Resurse Naturale și Protecția Mediului - Profesională - Silvicultură - Limba Maghiară',
                                 'Resurse Naturale și Protecția Mediului - Profesională - Protecția Mediului - Limba Maghiară'],
                                HIGHSCHOOL_PROF_HU)


def add_data_for_highschool(programs_names, program_map):
    for program_name in programs_names:
        program = GenericAcademicProgram.objects.create(name=program_name, category=SchoolUnitCategory.objects.get(name='Liceu - Filieră Tehnologică'))
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
