# this should be run using this command:
# ./manage.py runscript load_highschool_curriculum
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
HIGHSCHOOL_MILITARY_MATH_CS = {
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
            'weekly_hours_count': [3, 3, 2, 3]
        },
        {
            'subject': 'Chimie',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Biologie',
            'grades': ['IX', 'X', 'XI'],
            'weekly_hours_count': [1, 1, 1]
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
            'grades': ['IX', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1]
        },
        {
            'subject': 'Socio-umane / Discipline psihologice și pedagogice',
            'grades': ['X'],
            'weekly_hours_count': [1]
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
            'weekly_hours_count': [2, 1, 3, 3]
        },
        {
            'subject': 'Tehnologia informației și a comunicațiilor',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 2]
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
        },
        {
            'subject': 'Ordine și securitate publică / Pregătire militară',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 2, 2, 2]
        }
    ],
    "optional_subjects_weekly_hours": {
        "IX": 1,
        "X": 1,
        "XI": 2,
        "XII": 2
    }
}
HIGHSCHOOL_MILITARY_SOCIAL_SCIENCES = {
    "subjects": [
        {
            'subject': 'Limba și literatura română',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [4, 4, 4, 4]
        },
        {
            'subject': 'Limba modernă 1',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 2, 3, 3]
        },
        {
            'subject': 'Limba modernă 2',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 2, 2, 2]
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
            'weekly_hours_count': [2, 2, 3, 4]
        },
        {
            'subject': 'Geografie',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Socio-umane / Educaţie pentru societate',
            'grades': ['IX', 'XI', 'XII'],
            'weekly_hours_count': [2, 4, 2]
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
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Educație vizuală',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Educație fizică',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 2, 2]
        },
        {
            'subject': 'Pregătire sportivă practică / Atac și autoapărare',
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
        },
        {
            'subject': 'Ordine și securitate publică / Pregătire militară',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 2, 2, 2]
        }
    ],
    "optional_subjects_weekly_hours": {
        "IX": 1,
        "X": 1,
        "XI": 3,
        "XII": 4
    }
}
HIGHSCHOOL_ARTISTIC_MUSIC = {
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
            'weekly_hours_count': [1, 1, 2, 2]
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
            'grades': ['IX', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1]
        },
        {
            'subject': 'Socio-umane / Discipline psihologice și pedagogice',
            'grades': ['X'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Religie',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Educație muzicală',
            'grades': ['X'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Educație vizuală',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Educație artistică specializată / Artă dramatică',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [10, 10, 14, 14]
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
        "XI": 4,
        "XII": 4
    }
}
HIGHSCHOOL_ARTISTIC_CHOREOGRAPHY = {
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
            'weekly_hours_count': [1, 1, 2, 2]
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
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
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
            'grades': ['IX', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1]
        },
        {
            'subject': 'Socio-umane / Discipline psihologice și pedagogice',
            'grades': ['X'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Religie',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Educație muzicală',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Educație vizuală',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Dans clasic',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [8, 8, 10, 10]
        },
        {
            'subject': 'Dans contemporan',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Dans de caracter',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Duet clasic',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [1, 2]
        },
        {
            'subject': 'Repertoriu individual',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 2, 2]
        },
        {
            'subject': 'Istoria baletului',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Educație fizică',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Tehnologia informației și a comunicațiilor',
            'grades': ['IX', 'X', 'XI'],
            'weekly_hours_count': [2, 1, 1]
        },
        {
            'subject': 'Educație antreprenorială',
            'grades': ['X'],
            'weekly_hours_count': [1]
        }
    ],
    "optional_subjects_weekly_hours": {
        "IX": 2,
        "X": 2,
        "XI": 4,
        "XII": 4
    }
}
HIGHSCHOOL_ARTISTIC_ACTING = {
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
            'weekly_hours_count': [1, 1, 2, 2]
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
            'grades': ['IX', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1]
        },
        {
            'subject': 'Socio-umane / Discipline psihologice și pedagogice',
            'grades': ['X'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Religie',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Educație muzicală',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Educație vizuală',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Arta actorului',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [3, 3, 3, 3]
        },
        {
            'subject': 'Euritmie',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [2, 2]
        },
        {
            'subject': 'Elemente de estetică şi teoria spectacolului',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 2, 2]
        },
        {
            'subject': 'Istoria teatrului şi a artei spectacolului universal şi românesc',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 2, 2, 2]
        },
        {
            'subject': 'Artele spectacolului',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Management artistic',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Iniţiere vocală',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Educație fizică',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 2, 2]
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
        "XI": 5,
        "XII": 5
    }
}
HIGHSCHOOL_ARTISTIC_ARCHITECTURE = {
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
            'weekly_hours_count': [1, 1, 2, 2]
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
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Geografie',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Socio-umane / Educaţie pentru societate',
            'grades': ['IX', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1]
        },
        {
            'subject': 'Socio-umane / Discipline psihologice și pedagogice',
            'grades': ['X'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Religie',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Educație muzicală',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Educație vizuală',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Studiul formelor în desen',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 2, 3, 3]
        },
        {
            'subject': 'Studiul formelor în culoare şi studiul culorii',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Studiul formelor în volum',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Crochiuri',
            'grades': ['IX', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1]
        },
        {
            'subject': 'Desen proiectiv',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [2, 2]
        },
        {
            'subject': 'Elemente de perspectivă',
            'grades': ['X'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Istoria artelor şi a arhitecturii',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Atelier de specialitate',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [4, 4]
        },
        {
            'subject': 'Perspectivă şi desen proiectiv',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [2, 2]
        },
        {
            'subject': 'Istoria arhitecturii / Istoria artelor ambientale / Istoria designului',
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
            'grades': ['IX', 'X'],
            'weekly_hours_count': [2, 1]
        },
        {
            'subject': 'Informatică / Pregătire practică de specialitate',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [2, 2]
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
        "XI": 3,
        "XII": 3
    }
}
HIGHSCHOOL_ARTISTIC_DESIGN = {
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
            'weekly_hours_count': [1, 1, 2, 2]
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
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Geografie',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Socio-umane / Educaţie pentru societate',
            'grades': ['IX', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1]
        },
        {
            'subject': 'Socio-umane / Discipline psihologice și pedagogice',
            'grades': ['X'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Religie',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Educație muzicală',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Educație vizuală',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Studiul formelor în desen',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 2, 3, 3]
        },
        {
            'subject': 'Studiul formelor în culoare şi studiul culorii',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Studiul formelor în volum',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Crochiuri',
            'grades': ['IX', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1]
        },
        {
            'subject': 'Desen proiectiv',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [2, 2]
        },
        {
            'subject': 'Elemente de perspectivă',
            'grades': ['X'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Istoria artelor şi a arhitecturii',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Atelier de specialitate',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [4, 4]
        },
        {
            'subject': 'Perspectivă şi desen proiectiv',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [2, 2]
        },
        {
            'subject': 'Istoria arhitecturii / Istoria artelor ambientale / Istoria designului',
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
            'grades': ['IX', 'X'],
            'weekly_hours_count': [2, 1]
        },
        {
            'subject': 'Informatică / Pregătire practică de specialitate',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [2, 2]
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
        "XI": 3,
        "XII": 3
    }
}
HIGHSCHOOL_ARTISTIC_DECOR = {
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
            'weekly_hours_count': [1, 1, 2, 2]
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
            'grades': ['IX', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1]
        },
        {
            'subject': 'Socio-umane / Discipline psihologice și pedagogice',
            'grades': ['X'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Religie',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Educație muzicală',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Educație vizuală',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Studiul formelor în desen',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 2, 3, 3]
        },
        {
            'subject': 'Studiul formelor în culoare şi studiul culorii',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [2, 2]
        },
        {
            'subject': 'Studiul formelor în volum',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [2, 2]
        },
        {
            'subject': 'Studiul compoziţiei',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Crochiuri',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Istoria artelor şi a arhitecturii',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Atelier de specialitate',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [4, 5]
        },
        {
            'subject': 'Studiul corpului şi al figurii umane, în culoare / în volum',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [4, 3]
        },
        {
            'subject': 'Istoria artelor plastice / Istoria artelor decorative',
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
            'grades': ['IX', 'X'],
            'weekly_hours_count': [2, 1]
        },
        {
            'subject': 'Informatică / Pregătire practică de specialitate',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [2, 2]
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
        "XI": 3,
        "XII": 3
    }
}
HIGHSCHOOL_ARTISTIC_CULTURAL_ASSETS = {
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
            'weekly_hours_count': [1, 1, 2, 2]
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
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Geografie',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Socio-umane / Educaţie pentru societate',
            'grades': ['IX'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Socio-umane / Discipline psihologice și pedagogice',
            'grades': ['X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1]
        },
        {
            'subject': 'Religie',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Educație muzicală',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Educație vizuală',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Educație artistică specializată / Artă dramatică',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [8, 8, 11, 11]
        },
        {
            'subject': 'Educație fizică',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Tehnologia informației și a comunicațiilor',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [2, 1]
        },
        {
            'subject': 'Informatică / Pregătire practică de specialitate',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [2, 2]
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
        "XI": 3,
        "XII": 3
    }
}
HIGHSCHOOL_ORTHODOX_THEOLOGY = {
    "subjects": [
        {
            'subject': 'Limba și literatura română',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [4, 4, 3, 3]
        },
        {
            'subject': 'Limba modernă 1',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 2, 2, 2]
        },
        {
            'subject': 'Limba modernă 2',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 2, 2]
        },
        {
            'subject': 'Limba latină',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Limba greacă',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
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
            'grades': ['IX', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1]
        },
        {
            'subject': 'Socio-umane / Discipline psihologice și pedagogice',
            'grades': ['X'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Religie',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Studiu biblic al Vechiului Testament',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Studiu biblic al Noului Testament',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Dogmatică',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 2, 2]
        },
        {
            'subject': 'Spiritualitate',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Muzică bisericească',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Istoria Bisericii Ortodoxe Române',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [1, 2]
        },
        {
            'subject': 'Istoria Bisericească Universală',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Catehetică şi Omiletică',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Tipic şi Liturgică',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [2, 2]
        },
        {
            'subject': 'Educație muzicală',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Educație vizuală',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
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
        "IX": 2,
        "X": 2,
        "XI": 3,
        "XII": 3
    }
}
HIGHSCHOOL_CHURCH_MUSIC = {
    "subjects": [
        {
            'subject': 'Limba și literatura română',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [4, 4, 3, 3]
        },
        {
            'subject': 'Limba modernă 1',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 2, 2, 2]
        },
        {
            'subject': 'Limba modernă 2',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 2, 2]
        },
        {
            'subject': 'Limba latină',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Limba greacă',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
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
            'grades': ['IX', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1]
        },
        {
            'subject': 'Socio-umane / Discipline psihologice și pedagogice',
            'grades': ['X'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Religie',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Studiu biblic al Vechiului Testament',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Studiu biblic al Noului Testament',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Tipic şi Liturgică',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Cântare practică bisericească',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Muzică bisericească',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 2, 3, 3]
        },
        {
            'subject': 'Dogmatică',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [2, 2]
        },
        {
            'subject': 'Spiritualitate',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Ansamblu coral',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Istoria Bisericii Ortodoxe Române',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Istoria Bisericească Universală',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Catehetică',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Educație muzicală',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Educație vizuală',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
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
        "IX": 2,
        "X": 2,
        "XI": 3,
        "XII": 3
    }
}
HIGHSCHOOL_CULTURAL_HERITAGE = {
    "subjects": [
        {
            'subject': 'Limba și literatura română',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [4, 4, 3, 3]
        },
        {
            'subject': 'Limba modernă 1',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 2, 2, 2]
        },
        {
            'subject': 'Limba modernă 2',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 2, 2]
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
            'grades': ['IX', 'X', 'XI'],
            'weekly_hours_count': [1, 1, 1]
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
            'grades': ['IX', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1]
        },
        {
            'subject': 'Socio-umane / Discipline psihologice și pedagogice',
            'grades': ['X'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Religie',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Studiu biblic al Vechiului Testament',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Studiu biblic al Noului Testament',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Dogmatică',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [2, 2]
        },
        {
            'subject': 'Istoria Bisericii Ortodoxe Române',
            'grades': ['XII'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Istoria Bisericească Universală',
            'grades': ['XI'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Educație muzicală',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Educație vizuală',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Studiul formelor şi desenul',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 2, 2]
        },
        {
            'subject': 'Studiul culorilor şi pictură de icoană',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 2, 3]
        },
        {
            'subject': 'Istoria artelor – Arta eclezială',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Sculptură',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Sculptură decorativă',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Studiul materialelor de lucru în arta eclesială',
            'grades': ['XI'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Restaurare de icoană şi lemn policrom',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Istoria artelor',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Studiul tehnicilor vechi şi tradiţionale',
            'grades': ['XII'],
            'weekly_hours_count': [1]
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
        "IX": 2,
        "X": 2,
        "XI": 3,
        "XII": 3
    }
}
HIGHSCHOOL_THEOLOGY = {
    "subjects": [
        {
            'subject': 'Limba și literatura română',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [4, 4, 3, 3]
        },
        {
            'subject': 'Limba modernă 1',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 2, 2, 2]
        },
        {
            'subject': 'Limba modernă 2',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 2, 2]
        },
        {
            'subject': 'Limba latină',
            'grades': ['XI'],
            'weekly_hours_count': [2]
        },
        {
            'subject': 'Matematică',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 2, 2, 1]
        },
        {
            'subject': 'Științe',
            'grades': ['XI', 'XII'],
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
            'weekly_hours_count': [2, 2]
        },
        {
            'subject': 'Biologie',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [2, 2]
        },
        {
            'subject': 'Istorie',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 2]
        },
        {
            'subject': 'Geografie',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Socio-umane / Educaţie pentru societate',
            'grades': ['IX', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1]
        },
        {
            'subject': 'Socio-umane / Discipline psihologice și pedagogice',
            'grades': ['X'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Religie',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Discipline teologice / Discipline de specialitate',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [6, 6, 4, 6]
        },
        {
            'subject': 'Educație muzicală',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Educație vizuală',
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
            'weekly_hours_count': [2, 1, 1, 1]
        },
        {
            'subject': 'Educație antreprenorială',
            'grades': ['X'],
            'weekly_hours_count': [1]
        }
    ],
    "optional_subjects_weekly_hours": {
        "IX": 2,
        "X": 2,
        "XI": 5,
        "XII": 5
    }
}
HIGHSCHOOL_SPORT = {
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
            'weekly_hours_count': [1, 1, 2, 2]
        },
        {
            'subject': 'Matematică',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 2, 1, 1]
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
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
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
            'grades': ['IX', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1]
        },
        {
            'subject': 'Socio-umane / Discipline psihologice și pedagogice',
            'grades': ['X'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Religie',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Educație muzicală',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Educație vizuală',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Educație fizică',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 2, 2]
        },
        {
            'subject': 'Pregătire sportivă teoretică',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 2, 12, 12]
        },
        {
            'subject': 'Pregătire sportivă practică / Atac și autoapărare',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [8, 8]
        },
        {
            'subject': 'Tehnologia informației și a comunicațiilor',
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
        "XI": 4,
        "XII": 4
    }
}
HIGHSCHOOL_EDUCATOR_TEACHER = {
    "subjects": [
        {
            'subject': 'Limba și literatura română',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [4, 4, 4, 4]
        },
        {
            'subject': 'Limba modernă 1',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 2, 2, 2]
        },
        {
            'subject': 'Limba modernă 2',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 2, 1, 2]
        },
        {
            'subject': 'Metodica predării limbii şi literaturii române',
            'grades': ['XI'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Matematică',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 2, 1, 1]
        },
        {
            'subject': 'Metodica predării matematicii / activităţilor matematicii',
            'grades': ['XI'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Aritmetică',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Științe ale naturii',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [1, 2]
        },
        {
            'subject': 'Metodica predării ştiinţelor naturii',
            'grades': ['XI'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Fizică',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
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
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Geografie',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Metodica predării istoriei şi geografiei',
            'grades': ['XI'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Socio-umane / Educaţie pentru societate',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Socio-umane / Discipline psihologice și pedagogice',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [3, 3, 6, 7]
        },
        {
            'subject': 'Religie',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Educație muzicală',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Educație vizuală',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Educaţie muzicală şi educaţie plastică',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [1, 2]
        },
        {
            'subject': 'Metodica predării educaţiei muzicale şi a educaţiei plastice',
            'grades': ['XI'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Educație fizică',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Metodica predării educaţiei fizice',
            'grades': ['XI'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Tehnologia informației și a comunicațiilor',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 2, 1, 1]
        },
        {
            'subject': 'Informatică / Pregătire practică de specialitate',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [3, 3]
        },
        {
            'subject': 'Educație antreprenorială',
            'grades': ['X'],
            'weekly_hours_count': [1]
        }
    ],
    "optional_subjects_weekly_hours": {
        "IX": 2,
        "X": 2,
        "XI": 2,
        "XII": 2
    }
}
HIGHSCHOOL_EDUCATOR_CHILD_CARER = {
    "subjects": [
        {
            'subject': 'Limba și literatura română',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [4, 4, 3, 3]
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
            'weekly_hours_count': [2, 2, 1, 1]
        },
        {
            'subject': 'Științe',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [1, 1]
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
            'subject': 'Socio-umane / Discipline psihologice și pedagogice',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [3, 3, 3, 5]
        },
        {
            'subject': 'Discipline teologice / Discipline de specialitate',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [3, 3]
        },
        {
            'subject': 'Religie',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Educație muzicală',
            'grades': ['IX', 'XI'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Educație vizuală',
            'grades': ['X', 'XII'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Educație artistică specializată / Artă dramatică',
            'grades': ['XI'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Educație fizică',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Pregătire sportivă teoretică',
            'grades': ['XII'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Tehnologia informației și a comunicațiilor',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 1, 1, 1]
        },
        {
            'subject': 'Informatică / Pregătire practică de specialitate',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [3, 3, 4, 4]
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
        "XI": 2,
        "XII": 2
    }
}
HIGHSCHOOL_PEDAGOG = {
    "subjects": [
        {
            'subject': 'Limba și literatura română',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [4, 4, 3, 3]
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
            'subject': 'Comunicare didactică / Tehnici de comunicare',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Matematică',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 2, 1, 1]
        },
        {
            'subject': 'Științe',
            'grades': ['XI', 'XII'],
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
            'subject': 'Socio-umane / Discipline psihologice și pedagogice',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 6, 7]
        },
        {
            'subject': 'Religie',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Educație muzicală',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Educație vizuală',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Educație artistică specializată / Artă dramatică',
            'grades': ['XI'],
            'weekly_hours_count': [1]
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
            'subject': 'Informatică / Pregătire practică de specialitate',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [3, 3]
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
HIGHSCHOOL_SCHOOL_MEDIATOR = {
    "subjects": [
        {
            'subject': 'Limba și literatura română',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [4, 4, 3, 3]
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
            'subject': 'Comunicare didactică / Tehnici de comunicare',
            'grades': ['IX', 'X', 'XI'],
            'weekly_hours_count': [1, 1, 1]
        },
        {
            'subject': 'Matematică',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 2, 1, 1]
        },
        {
            'subject': 'Științe',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [1, 1]
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
            'subject': 'Socio-umane / Discipline psihologice și pedagogice',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 2, 6, 6]
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
            'subject': 'Informatică / Pregătire practică de specialitate',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [3, 3, 5, 6]
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
        "XI": 3,
        "XII": 3
    }
}
HIGHSCHOOL_EXTRACURRICULAR = {
    "subjects": [
        {
            'subject': 'Limba și literatura română',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [4, 4, 3, 3]
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
            'weekly_hours_count': [2, 2, 1, 2]
        },
        {
            'subject': 'Științe',
            'grades': ['XI', 'XII'],
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
            'subject': 'Socio-umane / Discipline psihologice și pedagogice',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 3, 4, 6]
        },
        {
            'subject': 'Religie',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Educație muzicală',
            'grades': ['IX', 'XI'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Educație vizuală',
            'grades': ['IX', 'XII'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Educație artistică specializată / Artă dramatică',
            'grades': ['X', 'XI'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Educație fizică',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 2, 2]
        },
        {
            'subject': 'Tehnologia informației și a comunicațiilor',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 1, 1, 1]
        },
        {
            'subject': 'Informatică / Pregătire practică de specialitate',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [3, 3, 4, 4]
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
        "XI": 2,
        "XII": 2
    }
}
HIGHSCHOOL_LIBRARIAN = {
    "subjects": [
        {
            'subject': 'Limba și literatura română',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [4, 4, 3, 3]
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
            'subject': 'Comunicare didactică / Tehnici de comunicare',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Matematică',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 2, 1, 1]
        },
        {
            'subject': 'Științe',
            'grades': ['XI', 'XII'],
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
            'subject': 'Socio-umane / Discipline psihologice și pedagogice',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 6, 6]
        },
        {
            'subject': 'Religie',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Educație muzicală',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Educație vizuală',
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
            'weekly_hours_count': [2, 1, 1, 1]
        },
        {
            'subject': 'Informatică / Pregătire practică de specialitate',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [3, 3]
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
        "XII": 5
    }
}
HIGHSCHOOL_TOURISM_GUIDE_ORTHODOX = {
    "subjects": [
        {
            'subject': 'Limba și literatura română',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [4, 4, 3, 3]
        },
        {
            'subject': 'Limba modernă 1',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [3, 3, 3, 3]
        },
        {
            'subject': 'Limba modernă 2',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 2, 2]
        },
        {
            'subject': 'Matematică',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 2, 1, 1]
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
            'subject': 'Studiu biblic al Vechiului Testament',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Studiu biblic al Noului Testament',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Dogmatică',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [2, 2]
        },
        {
            'subject': 'Spiritualitate',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Muzică bisericească',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Istoria Bisericii Ortodoxe Române',
            'grades': ['IX'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Istoria Bisericească Universală',
            'grades': ['X'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Geografia turismului religios ortodox',
            'grades': ['IX'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Itinerarii turistice religioase ortodoxe în România şi peste graniţe',
            'grades': ['X'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Istoria culturii şi spiritualităţii artei monahale',
            'grades': ['XI'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Economia întreprinderii turistice şi elemente de legislaţie',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Contabilitate',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Marketing în turism',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Tehnologia activităţii de turism',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Tehnologia hotelieră',
            'grades': ['XII'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Practică de specialitate',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [3, 3]
        },
        {
            'subject': 'Educație muzicală',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Educație vizuală',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
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
        "IX": 2,
        "X": 2,
        "XI": 3,
        "XII": 3
    }
}
HIGHSCHOOL_TOURISM_GUIDE_GREEK_CATHOLIC = {
    "subjects": [
        {
            'subject': 'Limba și literatura română',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [4, 4, 4, 4]
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
            'subject': 'Limba latină',
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
            'subject': 'Științe',
            'grades': ['XI', 'XII'],
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
            'subject': 'Studiu biblic',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 2, 1, 2]
        },
        {
            'subject': 'Catehism',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Istoria religiilor',
            'grades': ['XI'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Istoria Bisericii',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Istoria artei sacre',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Turism şi patrimoniu cultural',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Geografia turismului',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Literatura universală creştină',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Economia turismului',
            'grades': ['XII'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Contabilitate',
            'grades': ['XI'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Marketing în turism',
            'grades': ['XII'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Tehnologia activităţii de turism',
            'grades': ['XI'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Tehnologia hotelieră',
            'grades': ['XII'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Practică de specialitate',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Educație muzicală',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Educație vizuală',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
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
        "IX": 2,
        "X": 2,
        "XI": 4,
        "XII": 3
    }
}
HIGHSCHOOL_TOURISM_GUIDE_ROMAN_CATHOLIC_HU = {
    "subjects": [
        {
            'subject': 'Limba și literatura română',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [3, 3, 4, 4]
        },
        {
            'subject': 'Limba și literatura maghiară',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [3, 3, 4, 4]
        },
        {
            'subject': 'Literatura universală',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [1, 1]
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
            'subject': 'Limba latină',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 2, 2, 1]
        },
        {
            'subject': 'Limba italiană',
            'grades': ['IX', 'X'],
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
            'subject': 'Științe',
            'grades': ['XI', 'XII'],
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
            'subject': 'Studiu biblic',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 2, 2, 2]
        },
        {
            'subject': 'Catehism',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 2]
        },
        {
            'subject': 'Spiritualitate',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Geografia turismului religios',
            'grades': ['XI'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Artă religioasă',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Economia turismului religios',
            'grades': ['XII'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Marketing în turism',
            'grades': ['XII'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Tehnologia activităţii de turism',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Practică de specialitate',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 2, 1]
        },
        {
            'subject': 'Educație muzicală',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Educație vizuală',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
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
        "XI": 2,
        "XII": 2
    }
}
HIGHSCHOOL_TOURISM_GUIDE_ROMAN_CATHOLIC = {
    "subjects": [
        {
            'subject': 'Limba și literatura română',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [3, 3, 4, 4]
        },
        {
            'subject': 'Literatura universală',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [1, 1]
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
            'subject': 'Limba latină',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 2, 2, 1]
        },
        {
            'subject': 'Limba greacă biblică',
            'grades': ['IX', 'X'],
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
            'subject': 'Științe',
            'grades': ['XI', 'XII'],
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
            'subject': 'Studiu biblic',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [2, 2, 2, 2]
        },
        {
            'subject': 'Catehism',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 2]
        },
        {
            'subject': 'Spiritualitate',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Geografia turismului religios',
            'grades': ['XI'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Artă religioasă',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Economia turismului religios',
            'grades': ['XII'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Marketing în turism',
            'grades': ['XII'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Tehnologia activităţii de turism',
            'grades': ['XI', 'XII'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Practică de specialitate',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 2, 1]
        },
        {
            'subject': 'Educație muzicală',
            'grades': ['IX', 'X', 'XI', 'XII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Educație vizuală',
            'grades': ['IX', 'X'],
            'weekly_hours_count': [1, 1]
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
        "XI": 2,
        "XII": 2
    }
}
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
            'grades': ['IX', 'X', 'XI'],
            'weekly_hours_count': [1, 1, 2]
        },
        {
            'subject': 'Socio-umane / Discipline psihologice și pedagogice',
            'grades': ['XII'],
            'weekly_hours_count': [2]
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
            'weekly_hours_count': [1, 1, 1, 1, 1]
        },
        {
            'subject': 'Educație antreprenorială',
            'grades': ['X'],
            'weekly_hours_count': [1]
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
            'weekly_hours_count': [1, 1, 1, 1, 1]
        },
        {
            'subject': 'Educație antreprenorială',
            'grades': ['X'],
            'weekly_hours_count': [1]
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
            'weekly_hours_count': [1, 1, 1, 1, 1]
        },
        {
            'subject': 'Educație antreprenorială',
            'grades': ['X'],
            'weekly_hours_count': [1]
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
            'grades': ['IX', 'X', 'XI'],
            'weekly_hours_count': [1, 1, 1]
        },
        {
            'subject': 'Socio-umane / Discipline psihologice și pedagogice',
            'grades': ['XII'],
            'weekly_hours_count': [1]
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
            'weekly_hours_count': [1, 1, 1, 1, 1]
        },
        {
            'subject': 'Educație antreprenorială',
            'grades': ['X'],
            'weekly_hours_count': [1]
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
        add_data_for_highschool(GenericAcademicProgram.objects.filter(name='Specializarea Matematică-Informatică'), HIGHSCHOOL_MILITARY_MATH_CS)
        add_data_for_highschool(GenericAcademicProgram.objects.filter(name='Specializarea Științe Sociale'), HIGHSCHOOL_MILITARY_SOCIAL_SCIENCES)
        add_data_for_highschool(GenericAcademicProgram.objects.filter(name='Specializarea Muzică'), HIGHSCHOOL_ARTISTIC_MUSIC)
        add_data_for_highschool(GenericAcademicProgram.objects.filter(name='Specializarea Coregrafie'), HIGHSCHOOL_ARTISTIC_CHOREOGRAPHY)
        add_data_for_highschool(GenericAcademicProgram.objects.filter(name='Specializarea Arta Actorului'), HIGHSCHOOL_ARTISTIC_ACTING)
        add_data_for_highschool(GenericAcademicProgram.objects.filter(name='Specializarea Arhitectură'), HIGHSCHOOL_ARTISTIC_ARCHITECTURE)
        add_data_for_highschool(GenericAcademicProgram.objects.filter(name='Specializarea Arte Ambientale și Design'), HIGHSCHOOL_ARTISTIC_DESIGN)
        add_data_for_highschool(GenericAcademicProgram.objects.filter(name='Specializarea Arte Plastice și Decorative'), HIGHSCHOOL_ARTISTIC_DECOR)
        add_data_for_highschool(GenericAcademicProgram.objects.filter(name='Specializarea Conservare-Restaurare Bunuri Culturale'), HIGHSCHOOL_ARTISTIC_CULTURAL_ASSETS)
        add_data_for_highschool(GenericAcademicProgram.objects.filter(name='Specializarea Teologie Ortodoxă'), HIGHSCHOOL_ORTHODOX_THEOLOGY)
        add_data_for_highschool(GenericAcademicProgram.objects.filter(name='Specializarea Muzică Bisericească'), HIGHSCHOOL_CHURCH_MUSIC)
        add_data_for_highschool(GenericAcademicProgram.objects.filter(name='Specializarea Patrimoniu Cultural'), HIGHSCHOOL_CULTURAL_HERITAGE)
        add_data_for_highschool(GenericAcademicProgram.objects.filter(name__in=['Specializarea Teologie Romano-Catolică (de limba română)',
                                                                                'Specializarea Teologie Romano-Catolică (de limba maghiară)',
                                                                                'Specializarea Teologie Greco-Catolică',
                                                                                'Specializarea Teologie Reformată',
                                                                                'Specializarea Teologie Penticostală',
                                                                                'Specializarea Teologie Baptistă',
                                                                                'Specializarea Teologie Unitariană',
                                                                                'Specializarea Teologie Adventistă',
                                                                                'Specializarea Teologie Musulmană']),
                                HIGHSCHOOL_THEOLOGY)
        add_data_for_highschool(GenericAcademicProgram.objects.filter(name='Specializarea Ghid Turism Religios (cult ortodox)'), HIGHSCHOOL_TOURISM_GUIDE_ORTHODOX)
        add_data_for_highschool(GenericAcademicProgram.objects.filter(name='Specializarea Ghid Turism Religios (cult greco-catolic)'), HIGHSCHOOL_TOURISM_GUIDE_GREEK_CATHOLIC)
        add_data_for_highschool(GenericAcademicProgram.objects.filter(name='Specializarea Ghid Turism Religios (cult romano-catolic, de limba maghiară)'),
                                HIGHSCHOOL_TOURISM_GUIDE_ROMAN_CATHOLIC_HU)
        add_data_for_highschool(GenericAcademicProgram.objects.filter(name='Specializarea Ghid Turism Religios (cult romano-catolic, de limba română)'),
                                HIGHSCHOOL_TOURISM_GUIDE_ROMAN_CATHOLIC)
        add_data_for_highschool(GenericAcademicProgram.objects.filter(academic_profile__name='Sportiv'), HIGHSCHOOL_SPORT)
        add_data_for_highschool(GenericAcademicProgram.objects.filter(name='Specializarea Învățător/ Educatoare'), HIGHSCHOOL_EDUCATOR_TEACHER)
        add_data_for_highschool(GenericAcademicProgram.objects.filter(name='Specializarea Educator-Puericultor'), HIGHSCHOOL_EDUCATOR_CHILD_CARER)
        add_data_for_highschool(GenericAcademicProgram.objects.filter(name='Specializarea Pedagog Școlar'), HIGHSCHOOL_PEDAGOG)
        add_data_for_highschool(GenericAcademicProgram.objects.filter(name='Specializarea Mediator Școlar'), HIGHSCHOOL_SCHOOL_MEDIATOR)
        add_data_for_highschool(GenericAcademicProgram.objects.filter(name='Specializarea Instructor pentru Activități Extrașcolare'), HIGHSCHOOL_EXTRACURRICULAR)
        add_data_for_highschool(GenericAcademicProgram.objects.filter(name='Specializarea Instructor-Animator'), HIGHSCHOOL_EXTRACURRICULAR)
        add_data_for_highschool(GenericAcademicProgram.objects.filter(name='Specializarea Bibliotecar-Documentarist'), HIGHSCHOOL_LIBRARIAN)
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
