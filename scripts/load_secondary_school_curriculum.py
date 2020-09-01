# this should be run using this command:
# ./manage.py runscript load_secondary_school_curriculum
from django.db import transaction

from edualert.academic_programs.models import GenericAcademicProgram
from edualert.schools.models import SchoolUnitCategory, SchoolUnitProfile
from edualert.study_classes.constants import CLASS_GRADE_MAPPING
from edualert.subjects.models import Subject, ProgramSubjectThrough

SECONDARY_SCHOOL_REGULAR = {
    "subjects": [
        {
            'subject': 'Limba și literatura română',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [4, 4, 4, 4]
        },
        {
            'subject': 'Limba modernă 1',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [2, 2, 2, 2]
        },
        {
            'subject': 'Limba modernă 2',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [2, 2, 2, 2]
        },
        {
            'subject': 'Elemente de limbă latină și de cultură romanică',
            'grades': ['VII'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Matematică',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [4, 4, 4, 4]
        },
        {
            'subject': 'Fizică',
            'grades': ['VI', 'VII', 'VIII'],
            'weekly_hours_count': [2, 2, 2]
        },
        {
            'subject': 'Chimie',
            'grades': ['VII', 'VIII'],
            'weekly_hours_count': [2, 2]
        },
        {
            'subject': 'Biologie',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 2, 2, 1]
        },
        {
            'subject': 'Educație socială',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Istorie',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [2, 1, 1, 2]
        },
        {
            'subject': 'Geografie',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 1, 1, 2]
        },
        {
            'subject': 'Religie',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Educație plastică',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Educație muzicală',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Educație fizică și sport',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [2, 2, 2, 2]
        },
        {
            'subject': 'Educație tehnologică și aplicații practice',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Informatică și TIC',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Consiliere și dezvoltare personală',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 1, 1, 1]
        }
    ],
    "optional_subjects_weekly_hours": {
        "V": 3,
        "VI": 3,
        "VII": 3,
        "VIII": 4
    }
}
SECONDARY_SCHOOL_MINORITY_LANG = {
    "subjects": [
        {
            'subject': 'Limba și literatura română',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [4, 4, 4, 4]
        },
        {
            'subject': 'Limba maternă',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [4, 4, 4, 4]
        },
        {
            'subject': 'Limba modernă 1',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [2, 2, 2, 2]
        },
        {
            'subject': 'Elemente de limbă latină și de cultură romanică',
            'grades': ['VII'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Matematică',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [4, 4, 4, 4]
        },
        {
            'subject': 'Fizică',
            'grades': ['VI', 'VII', 'VIII'],
            'weekly_hours_count': [2, 2, 2]
        },
        {
            'subject': 'Chimie',
            'grades': ['VII', 'VIII'],
            'weekly_hours_count': [2, 2]
        },
        {
            'subject': 'Biologie',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 2, 2, 1]
        },
        {
            'subject': 'Educație socială',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Istorie',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [2, 1, 1, 2]
        },
        {
            'subject': 'Istoria și tradițiile minorităților',
            'grades': ['VI', 'VII'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Geografie',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 1, 1, 2]
        },
        {
            'subject': 'Religie',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Educație plastică',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Educație muzicală',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Educație fizică și sport',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [2, 2, 2, 2]
        },
        {
            'subject': 'Educație tehnologică și aplicații practice',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Informatică și TIC',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Consiliere și dezvoltare personală',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 1, 1, 1]
        }
    ],
    "optional_subjects_weekly_hours": {
        "V": 3,
        "VI": 3,
        "VII": 3,
        "VIII": 4
    }
}
SECONDARY_SCHOOL_ART_MUSIC = {
    "subjects": [
        {
            'subject': 'Limba și literatura română',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [4, 4, 4, 4]
        },
        {
            'subject': 'Limba modernă 1',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [2, 2, 2, 2]
        },
        {
            'subject': 'Limba modernă 2',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [2, 2, 2, 2]
        },
        {
            'subject': 'Elemente de limbă latină și de cultură romanică',
            'grades': ['VII'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Matematică',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [4, 4, 4, 4]
        },
        {
            'subject': 'Fizică',
            'grades': ['VI', 'VII', 'VIII'],
            'weekly_hours_count': [2, 2, 2]
        },
        {
            'subject': 'Chimie',
            'grades': ['VII', 'VIII'],
            'weekly_hours_count': [2, 2]
        },
        {
            'subject': 'Biologie',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 2, 2, 1]
        },
        {
            'subject': 'Educație socială',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Istorie',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [2, 1, 1, 2]
        },
        {
            'subject': 'Geografie',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 1, 1, 2]
        },
        {
            'subject': 'Religie',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Educație plastică',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Instrument principal',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [3, 3, 3, 3]
        },
        {
            'subject': 'Teorie-solfegiu-dicteu',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [2, 2, 2, 2]
        },
        {
            'subject': 'Pian complementar/Instrument auxiliar',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Educație fizică și sport',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [2, 2, 2, 2]
        },
        {
            'subject': 'Educație tehnologică și aplicații practice',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Informatică și TIC',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Consiliere și dezvoltare personală',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 1, 1, 1]
        }
    ],
    "optional_subjects_weekly_hours": {
        "V": 3,
        "VI": 3,
        "VII": 3,
        "VIII": 3
    }
}
SECONDARY_SCHOOL_CHOREOGRAPHY = {
    "subjects": [
        {
            'subject': 'Limba și literatura română',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [4, 4, 4, 4]
        },
        {
            'subject': 'Limba modernă 1',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [2, 2, 2, 2]
        },
        {
            'subject': 'Limba modernă 2',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [2, 2, 2, 2]
        },
        {
            'subject': 'Elemente de limbă latină și de cultură romanică',
            'grades': ['VII'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Matematică',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [4, 4, 4, 4]
        },
        {
            'subject': 'Fizică',
            'grades': ['VI', 'VII', 'VIII'],
            'weekly_hours_count': [2, 2, 2]
        },
        {
            'subject': 'Chimie',
            'grades': ['VII', 'VIII'],
            'weekly_hours_count': [2, 2]
        },
        {
            'subject': 'Biologie',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 2, 2, 1]
        },
        {
            'subject': 'Educație socială',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Istorie',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [2, 1, 1, 2]
        },
        {
            'subject': 'Geografie',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 1, 1, 2]
        },
        {
            'subject': 'Religie',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Educație plastică',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Educație muzicală',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Dans clasic',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [3, 4, 4, 4]
        },
        {
            'subject': 'Ritmică',
            'grades': ['V'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Educație fizică și sport',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [2, 2, 2, 2]
        },
        {
            'subject': 'Educație tehnologică și aplicații practice',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Informatică și TIC',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Consiliere și dezvoltare personală',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 1, 1, 1]
        }
    ],
    "optional_subjects_weekly_hours": {
        "V": 3,
        "VI": 3,
        "VII": 3,
        "VIII": 3
    }
}
SECONDARY_SCHOOL_ART_VISUAL_ARTS = {
    "subjects": [
        {
            'subject': 'Limba și literatura română',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [4, 4, 4, 4]
        },
        {
            'subject': 'Limba modernă 1',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [2, 2, 2, 2]
        },
        {
            'subject': 'Limba modernă 2',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [2, 2, 2, 2]
        },
        {
            'subject': 'Elemente de limbă latină și de cultură romanică',
            'grades': ['VII'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Matematică',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [4, 4, 4, 4]
        },
        {
            'subject': 'Fizică',
            'grades': ['VI', 'VII', 'VIII'],
            'weekly_hours_count': [2, 2, 2]
        },
        {
            'subject': 'Chimie',
            'grades': ['VII', 'VIII'],
            'weekly_hours_count': [2, 2]
        },
        {
            'subject': 'Biologie',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 2, 2, 1]
        },
        {
            'subject': 'Educație socială',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Istorie',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [2, 1, 1, 2]
        },
        {
            'subject': 'Geografie',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 1, 1, 2]
        },
        {
            'subject': 'Religie',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Educație muzicală',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Desen',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [2, 2, 2, 2]
        },
        {
            'subject': 'Pictură',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [2, 2, 2, 2]
        },
        {
            'subject': 'Modelaj',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Educație fizică și sport',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [2, 2, 2, 2]
        },
        {
            'subject': 'Educație tehnologică și aplicații practice',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Informatică și TIC',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Consiliere și dezvoltare personală',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 1, 1, 1]
        }
    ],
    "optional_subjects_weekly_hours": {
        "V": 3,
        "VI": 3,
        "VII": 3,
        "VIII": 3
    }
}
SECONDARY_SCHOOL_SPORT = {
    "subjects": [
        {
            'subject': 'Limba și literatura română',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [4, 4, 4, 4]
        },
        {
            'subject': 'Limba modernă 1',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [2, 2, 2, 2]
        },
        {
            'subject': 'Limba modernă 2',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [2, 2, 2, 2]
        },
        {
            'subject': 'Elemente de limbă latină și de cultură romanică',
            'grades': ['VII'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Matematică',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [4, 4, 4, 4]
        },
        {
            'subject': 'Fizică',
            'grades': ['VI', 'VII', 'VIII'],
            'weekly_hours_count': [2, 2, 2]
        },
        {
            'subject': 'Chimie',
            'grades': ['VII', 'VIII'],
            'weekly_hours_count': [2, 2]
        },
        {
            'subject': 'Biologie',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 2, 2, 1]
        },
        {
            'subject': 'Educație socială',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Istorie',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [2, 1, 1, 2]
        },
        {
            'subject': 'Geografie',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 1, 1, 2]
        },
        {
            'subject': 'Religie',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Educație plastică',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Educație muzicală',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Educație fizică și sport',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [2, 2, 2, 2]
        },
        {
            'subject': 'Pregătire sportivă practică',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [2, 2, 2, 2]
        },
        {
            'subject': 'Educație tehnologică și aplicații practice',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Informatică și TIC',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 1, 1, 1]
        },
        {
            'subject': 'Consiliere și dezvoltare personală',
            'grades': ['V', 'VI', 'VII', 'VIII'],
            'weekly_hours_count': [1, 1, 1, 1]
        }
    ],
    "optional_subjects_weekly_hours": {
        "V": 3,
        "VI": 3,
        "VII": 3,
        "VIII": 3
    }
}


def run():
    with transaction.atomic():
        add_data_for_secondary_school(SchoolUnitCategory.objects.get(name='Școală gimnazială'), SECONDARY_SCHOOL_REGULAR)
        add_data_for_secondary_school(SchoolUnitCategory.objects.get(name='Școală gimnazială în limbă minorități naționale'), SECONDARY_SCHOOL_MINORITY_LANG)
        add_data_for_secondary_school(SchoolUnitCategory.objects.get(name='Școală gimnazială în limba română pentru minorități naționale'), SECONDARY_SCHOOL_MINORITY_LANG)
        add_data_for_secondary_school(SchoolUnitCategory.objects.get(name='Școală gimnazială cu program integrat și suplimentar de artă - muzică'),
                                      SECONDARY_SCHOOL_ART_MUSIC, 'Artistic')
        add_data_for_secondary_school(SchoolUnitCategory.objects.get(name='Școală gimnazială cu program integrat și suplimentar de coregrafie'),
                                      SECONDARY_SCHOOL_CHOREOGRAPHY, 'Artistic')
        add_data_for_secondary_school(SchoolUnitCategory.objects.get(name='Școală gimnazială cu program integrat și suplimentar de artă - arte vizuale'),
                                      SECONDARY_SCHOOL_CHOREOGRAPHY, 'Artistic')
        add_data_for_secondary_school(SchoolUnitCategory.objects.get(name='Școală gimnazială cu program sportiv integrat'), SECONDARY_SCHOOL_SPORT, 'Sportiv')
        set_allows_exemption()


def add_data_for_secondary_school(category, category_map, academic_profile_name=None):
    academic_profile = None
    if academic_profile_name:
        academic_profile = SchoolUnitProfile.objects.get(name=academic_profile_name)
    program = GenericAcademicProgram.objects.create(name=category.name, category=category, academic_profile=academic_profile,
                                                    optional_subjects_weekly_hours=category_map['optional_subjects_weekly_hours'])
    for item in category_map['subjects']:
        subject = get_subject_by_name(item['subject'])
        for class_grade, weekly_hours_count in zip(item['grades'], item['weekly_hours_count']):
            ProgramSubjectThrough.objects.create(generic_academic_program=program, subject=subject, subject_name=subject.name,
                                                 class_grade=class_grade, class_grade_arabic=CLASS_GRADE_MAPPING[class_grade],
                                                 weekly_hours_count=weekly_hours_count, is_mandatory=True)


def set_allows_exemption():
    for subject_name in ['Educație fizică și sport']:
        subject = Subject.objects.get(name=subject_name)
        subject.allows_exemption = True
        subject.save()


def get_subject_by_name(name):
    subject, created = Subject.objects.get_or_create(name=name)
    return subject
