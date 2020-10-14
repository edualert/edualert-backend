# this should be run using this command:
# ./manage.py runscript load_highschool_curriculum_theoretical
from django.db import transaction

from edualert.academic_programs.models import GenericAcademicProgram
from edualert.study_classes.constants import CLASS_GRADE_MAPPING
from edualert.subjects.models import Subject, ProgramSubjectThrough

HIGHSCHOOL_PHILOLOGY = {
    "subjects": [
        {
            'subject': 'Limba și literatura română',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [4, 4, 4, 4]
        },
        {
            'subject': 'Limba modernă 1',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [3, 3, 3, 3]
        },
        {
            'subject': 'Limba modernă 2',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 2, 3, 3]
        },
        {
            'subject': 'Limba latină',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 2, 1]
        },
        {
            'subject': 'Comunicare didactică / Tehnici de comunicare',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Matematică',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [2, 2]
        },
        {
            'subject': 'Fizică',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [2, 2]
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
            'subject': 'Matematică şi Ştiinţe ale naturii',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Istorie',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 3, 2, 2]
        },
        {
            'subject': 'Geografie',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 2, 1, 1]
        },
        {
            'subject': 'Socio-umane / Educaţie pentru societate',
            'grades': ['IX', 'XI', 'XII'],
            'weekly_hours_count': [2, 2, 2]
        },
        {
            'subject': 'Socio-umane / Discipline psihologice și pedagogice',
            'grades': ['X'],
            'weekly_hours_count': [2]
        },
        {
            'subject': 'Religie',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Educație muzicală',
            'grades': ['IX'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Educație vizuală',
            'grades': ['IX'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Educație muzicală / Educație vizuală',
            'grades': ['X'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Educație artistică specializată / Artă dramatică',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Educație fizică',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Tehnologia informației și a comunicațiilor',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 1, 1, 1]
        },
        {
            'subject': 'Educație antreprenorială',
            'grades': ['X'],
            'weekly_hours_count': [1]
        }
    ],
    "optional_subjects_weekly_hours": {
        "IX": 1,
        "X": 1,
        "XI": 6,
        "XII": 7
    }
}
HIGHSCHOOL_SOCIAL_SCIENCES = {
    "subjects": [
        {
            'subject': 'Limba și literatura română',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [4, 4, 3, 3]
        },
        {
            'subject': 'Limba modernă 1',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [3, 3, 2, 2]
        },
        {
            'subject': 'Limba modernă 2',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 2, 2, 2]
        },
        {
            'subject': 'Limba latină',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Matematică',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 2, 2, 2]
        },
        {
            'subject': 'Fizică',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [2, 2]
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
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 3, 3, 3]
        },
        {
            'subject': 'Geografie',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 2, 2, 2]
        },
        {
            'subject': 'Socio-umane / Educaţie pentru societate',
            'grades': ['IX', 'XI', 'XII'],
            'weekly_hours_count': [2, 4, 4]
        },
        {
            'subject': 'Socio-umane / Discipline psihologice și pedagogice',
            'grades': ['X'],
            'weekly_hours_count': [2]
        },
        {
            'subject': 'Religie',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Educație muzicală',
            'grades': ['IX'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Educație vizuală',
            'grades': ['IX'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Educație muzicală / Educație vizuală',
            'grades': ['X'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Educație artistică specializată / Artă dramatică',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Educație fizică',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Tehnologia informației și a comunicațiilor',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 1, 2, 1]
        },
        {
            'subject': 'Educație antreprenorială',
            'grades': ['X'],
            'weekly_hours_count': [1]
        }
    ],
    "optional_subjects_weekly_hours": {
        "IX": 1,
        "X": 1,
        "XI": 6,
        "XII": 7
    }
}
HIGHSCHOOL_MATH_CS = {
    "subjects": [
        {
            'subject': 'Limba și literatura română',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [4, 3, 3, 3]
        },
        {
            'subject': 'Limba modernă 1',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 2, 2, 2]
        },
        {
            'subject': 'Limba modernă 2',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 2, 2, 2]
        },
        {
            'subject': 'Matematică',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [4, 4, 4, 4]
        },
        {
            'subject': 'Fizică',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [3, 3, 3, 3]
        },
        {
            'subject': 'Chimie',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 2, 1, 1]
        },
        {
            'subject': 'Biologie',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 2, 1, 1]
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
            'subject': 'Educație muzicală / Educație vizuală',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Educație fizică',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 2, 1, 1]
        },
        {
            'subject': 'Tehnologia informației și a comunicațiilor',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [2, 1]
        },
        {
            'subject': 'Informatică / Pregătire practică de specialitate',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 4, 4]
        },
        {
            'subject': 'Educație antreprenorială',
            'grades': ['X'],
            'weekly_hours_count': [1]
        }
    ],
    "optional_subjects_weekly_hours": {
        "IX": 1,
        "X": 1,
        "XI": 4,
        "XII": 4
    }
}
HIGHSCHOOL_NATURE_SCIENCES = {
    "subjects": [
        {
            'subject': 'Limba și literatura română',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [4, 3, 3, 3]
        },
        {
            'subject': 'Limba modernă 1',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 2, 2, 2]
        },
        {
            'subject': 'Limba modernă 2',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 2, 2, 2]
        },
        {
            'subject': 'Matematică',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [4, 4, 3, 3]
        },
        {
            'subject': 'Fizică',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [3, 3, 3, 3]
        },
        {
            'subject': 'Chimie',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 2, 2, 2]
        },
        {
            'subject': 'Biologie',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 2, 2, 2]
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
            'subject': 'Educație muzicală / Educație vizuală',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Educație fizică',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 2, 1, 1]
        },
        {
            'subject': 'Tehnologia informației și a comunicațiilor',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 1, 2, 1]
        },
        {
            'subject': 'Informatică / Pregătire practică de specialitate',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Educație antreprenorială',
            'grades': ['X'],
            'weekly_hours_count': [1]
        }
    ],
    "optional_subjects_weekly_hours": {
        "IX": 1,
        "X": 1,
        "XI": 5,
        "XII": 6
    }
}


def run():
    with transaction.atomic():
        add_data_for_highschool(GenericAcademicProgram.objects.filter(name__in=['Umanist - Specializarea Filologie',
                                                                                'Umanist - Special - Specializarea Filologie']),
                                HIGHSCHOOL_PHILOLOGY)
        add_data_for_highschool(GenericAcademicProgram.objects.filter(name__in=['Umanist - Specializarea Științe Sociale',
                                                                                'Umanist - Special - Specializarea Științe Sociale']),
                                HIGHSCHOOL_SOCIAL_SCIENCES)
        add_data_for_highschool(GenericAcademicProgram.objects.filter(name__in=['Real - Specializarea Matematică-Informatică',
                                                                                'Real - Special - Specializarea Matematică-Informatică']),
                                HIGHSCHOOL_MATH_CS)
        add_data_for_highschool(GenericAcademicProgram.objects.filter(name__in=['Real - Specializarea Științe ale Naturii',
                                                                                'Real - Special - Specializarea Științe ale Naturii']),
                                HIGHSCHOOL_NATURE_SCIENCES)


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
