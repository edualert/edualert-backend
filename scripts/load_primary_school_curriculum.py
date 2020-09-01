# this should be run using this command:
# ./manage.py runscript load_primary_school_curriculum
from django.db import transaction

from edualert.academic_programs.models import GenericAcademicProgram
from edualert.schools.models import SchoolUnitCategory, SchoolUnitProfile
from edualert.study_classes.constants import CLASS_GRADE_MAPPING
from edualert.subjects.models import Subject, ProgramSubjectThrough

PRIMARY_SCHOOL_REGULAR = {
    "subjects": [
        {
            'subject': 'Comunicare în limba română',
            'grades': ['P', 'I', 'II'],
            'weekly_hours_count': [5, 7, 6]
        },
        {
            'subject': 'Limba și literatura română',
            'grades': ['III', 'IV'],
            'weekly_hours_count': [5, 5]
        },
        {
            'subject': 'Limba modernă',
            'grades': ['P', 'I', 'II', 'III', 'IV'],
            'weekly_hours_count': [1, 1, 1, 2, 2]
        },
        {
            'subject': 'Matematică și explorarea mediului',
            'grades': ['P', 'I', 'II'],
            'weekly_hours_count': [4, 4, 5]
        },
        {
            'subject': 'Matematică',
            'grades': ['III', 'IV'],
            'weekly_hours_count': [4, 4]
        },
        {
            'subject': 'Științe ale naturii',
            'grades': ['III', 'IV'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Istorie',
            'grades': ['IV'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Geografie',
            'grades': ['IV'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Educație civică',
            'grades': ['III', 'IV'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Religie',
            'grades': ['P', 'I', 'II', 'III', 'IV'],
            'weekly_hours_count': [1, 1, 1, 1, 1]
        },
        {
            'subject': 'Educație fizică',
            'grades': ['P', 'I', 'II', 'III', 'IV'],
            'weekly_hours_count': [2, 2, 2, 2, 2]
        },
        {
            'subject': 'Joc și mișcare',
            'grades': ['III', 'IV'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Muzică și mișcare',
            'grades': ['P', 'I', 'II', 'III', 'IV'],
            'weekly_hours_count': [2, 2, 2, 1, 1]
        },
        {
            'subject': 'Arte vizuale și abilități practice',
            'grades': ['P', 'I', 'II', 'III', 'IV'],
            'weekly_hours_count': [2, 2, 2, 2, 1]
        },
        {
            'subject': 'Dezvoltare personală',
            'grades': ['P', 'I', 'II'],
            'weekly_hours_count': [2, 1, 1]
        }
    ],
    "optional_subjects_weekly_hours": {
        "P": 1,
        "I": 1,
        "II": 1,
        "III": 1,
        "IV": 1
    }
}
PRIMARY_SCHOOL_MINORITY_LANG = {
    "subjects": [
        {
            'subject': 'Comunicare în limba română',
            'grades': ['P', 'I', 'II'],
            'weekly_hours_count': [3, 4, 4]
        },
        {
            'subject': 'Limba și literatura română',
            'grades': ['III', 'IV'],
            'weekly_hours_count': [4, 4]
        },
        {
            'subject': 'Comunicare în limba maternă',
            'grades': ['P', 'I', 'II'],
            'weekly_hours_count': [5, 7, 6]
        },
        {
            'subject': 'Limba și literatura maternă',
            'grades': ['III', 'IV'],
            'weekly_hours_count': [5, 5]
        },
        {
            'subject': 'Limba modernă',
            'grades': ['P', 'I', 'II', 'III', 'IV'],
            'weekly_hours_count': [1, 1, 1, 2, 2]
        },
        {
            'subject': 'Matematică și explorarea mediului',
            'grades': ['P', 'I', 'II'],
            'weekly_hours_count': [4, 4, 5]
        },
        {
            'subject': 'Matematică',
            'grades': ['III', 'IV'],
            'weekly_hours_count': [4, 4]
        },
        {
            'subject': 'Științe ale naturii',
            'grades': ['III', 'IV'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Istorie',
            'grades': ['IV'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Geografie',
            'grades': ['IV'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Educație civică',
            'grades': ['III', 'IV'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Religie',
            'grades': ['P', 'I', 'II', 'III', 'IV'],
            'weekly_hours_count': [1, 1, 1, 1, 1]
        },
        {
            'subject': 'Educație fizică',
            'grades': ['P', 'I', 'II', 'III', 'IV'],
            'weekly_hours_count': [2, 2, 2, 2, 2]
        },
        {
            'subject': 'Joc și mișcare',
            'grades': ['III', 'IV'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Muzică și mișcare',
            'grades': ['P', 'I', 'II', 'III', 'IV'],
            'weekly_hours_count': [2, 2, 2, 1, 1]
        },
        {
            'subject': 'Arte vizuale și abilități practice',
            'grades': ['P', 'I', 'II', 'III', 'IV'],
            'weekly_hours_count': [2, 2, 2, 2, 1]
        },
        {
            'subject': 'Dezvoltare personală',
            'grades': ['P', 'I', 'II'],
            'weekly_hours_count': [2, 1, 1]
        }
    ],
    "optional_subjects_weekly_hours": {
        "P": 1,
        "I": 1,
        "II": 1,
        "III": 1,
        "IV": 1
    }
}
PRIMARY_SCHOOL_MINORITY_RO_LANG = {
    "subjects": [
        {
            'subject': 'Comunicare în limba română',
            'grades': ['P', 'I', 'II'],
            'weekly_hours_count': [5, 7, 6]
        },
        {
            'subject': 'Limba și literatura română',
            'grades': ['III', 'IV'],
            'weekly_hours_count': [5, 5]
        },
        {
            'subject': 'Comunicare în limba maternă',
            'grades': ['P', 'I', 'II'],
            'weekly_hours_count': [3, 4, 4]
        },
        {
            'subject': 'Limba și literatura maternă',
            'grades': ['III', 'IV'],
            'weekly_hours_count': [4, 4]
        },
        {
            'subject': 'Limba modernă',
            'grades': ['P', 'I', 'II', 'III', 'IV'],
            'weekly_hours_count': [1, 1, 1, 2, 2]
        },
        {
            'subject': 'Matematică și explorarea mediului',
            'grades': ['P', 'I', 'II'],
            'weekly_hours_count': [4, 4, 5]
        },
        {
            'subject': 'Matematică',
            'grades': ['III', 'IV'],
            'weekly_hours_count': [4, 4]
        },
        {
            'subject': 'Științe ale naturii',
            'grades': ['III', 'IV'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Istorie',
            'grades': ['IV'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Geografie',
            'grades': ['IV'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Educație civică',
            'grades': ['III', 'IV'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Religie',
            'grades': ['P', 'I', 'II', 'III', 'IV'],
            'weekly_hours_count': [1, 1, 1, 1, 1]
        },
        {
            'subject': 'Educație fizică',
            'grades': ['P', 'I', 'II', 'III', 'IV'],
            'weekly_hours_count': [2, 2, 2, 2, 2]
        },
        {
            'subject': 'Joc și mișcare',
            'grades': ['III', 'IV'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Muzică și mișcare',
            'grades': ['P', 'I', 'II', 'III', 'IV'],
            'weekly_hours_count': [2, 2, 2, 1, 1]
        },
        {
            'subject': 'Arte vizuale și abilități practice',
            'grades': ['P', 'I', 'II', 'III', 'IV'],
            'weekly_hours_count': [2, 2, 2, 2, 1]
        },
        {
            'subject': 'Dezvoltare personală',
            'grades': ['P', 'I', 'II'],
            'weekly_hours_count': [2, 1, 1]
        }
    ],
    "optional_subjects_weekly_hours": {
        "P": 1,
        "I": 1,
        "II": 1,
        "III": 1,
        "IV": 1
    }
}
PRIMARY_SCHOOL_ART_MUSIC = {
    "subjects": [
        {
            'subject': 'Comunicare în limba română',
            'grades': ['P', 'I', 'II'],
            'weekly_hours_count': [5, 7, 6]
        },
        {
            'subject': 'Limba și literatura română',
            'grades': ['III', 'IV'],
            'weekly_hours_count': [5, 5]
        },
        {
            'subject': 'Limba modernă',
            'grades': ['P', 'I', 'II', 'III', 'IV'],
            'weekly_hours_count': [1, 1, 1, 2, 2]
        },
        {
            'subject': 'Matematică și explorarea mediului',
            'grades': ['P', 'I', 'II'],
            'weekly_hours_count': [4, 4, 5]
        },
        {
            'subject': 'Matematică',
            'grades': ['III', 'IV'],
            'weekly_hours_count': [4, 4]
        },
        {
            'subject': 'Științe ale naturii',
            'grades': ['III', 'IV'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Istorie',
            'grades': ['IV'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Geografie',
            'grades': ['IV'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Educație civică',
            'grades': ['III', 'IV'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Religie',
            'grades': ['P', 'I', 'II', 'III', 'IV'],
            'weekly_hours_count': [1, 1, 1, 1, 1]
        },
        {
            'subject': 'Educație fizică',
            'grades': ['P', 'I', 'II', 'III', 'IV'],
            'weekly_hours_count': [2, 2, 2, 2, 2]
        },
        {
            'subject': 'Joc și mișcare',
            'grades': ['III', 'IV'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Muzică și mișcare',
            'grades': ['P', 'I', 'II', 'III', 'IV'],
            'weekly_hours_count': [2, 2, 2, 1, 1]
        },
        {
            'subject': 'Instrument',
            'grades': ['I', 'II', 'III', 'IV'],
            'weekly_hours_count': [2, 2, 2, 2]
        },
        {
            'subject': 'Teorie-solfegiu-dicteu',
            'grades': ['I', 'II', 'III', 'IV'],
            'weekly_hours_count': [2, 2, 2, 2]
        },
        {
            'subject': 'Arte vizuale și abilități practice',
            'grades': ['P', 'I', 'II', 'III', 'IV'],
            'weekly_hours_count': [2, 2, 2, 2, 1]
        },
        {
            'subject': 'Dezvoltare personală',
            'grades': ['P', 'I', 'II'],
            'weekly_hours_count': [2, 1, 1]
        }
    ],
    "optional_subjects_weekly_hours": {
        "P": 1,
        "I": 1,
        "II": 1,
        "III": 1,
        "IV": 1
    }
}
PRIMARY_SCHOOL_CHOREOGRAPHY = {
    "subjects": [
        {
            'subject': 'Comunicare în limba română',
            'grades': ['P', 'I', 'II'],
            'weekly_hours_count': [5, 7, 6]
        },
        {
            'subject': 'Limba și literatura română',
            'grades': ['III', 'IV'],
            'weekly_hours_count': [5, 5]
        },
        {
            'subject': 'Limba modernă',
            'grades': ['P', 'I', 'II', 'III', 'IV'],
            'weekly_hours_count': [1, 1, 1, 2, 2]
        },
        {
            'subject': 'Matematică și explorarea mediului',
            'grades': ['P', 'I', 'II'],
            'weekly_hours_count': [4, 4, 5]
        },
        {
            'subject': 'Matematică',
            'grades': ['III', 'IV'],
            'weekly_hours_count': [4, 4]
        },
        {
            'subject': 'Științe ale naturii',
            'grades': ['III', 'IV'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Istorie',
            'grades': ['IV'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Geografie',
            'grades': ['IV'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Educație civică',
            'grades': ['III', 'IV'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Religie',
            'grades': ['P', 'I', 'II', 'III', 'IV'],
            'weekly_hours_count': [1, 1, 1, 1, 1]
        },
        {
            'subject': 'Educație fizică',
            'grades': ['P', 'I', 'II', 'III', 'IV'],
            'weekly_hours_count': [2, 2, 2, 2, 2]
        },
        {
            'subject': 'Joc și mișcare',
            'grades': ['III', 'IV'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Muzică și mișcare',
            'grades': ['P', 'I', 'II', 'III', 'IV'],
            'weekly_hours_count': [2, 2, 2, 1, 1]
        },
        {
            'subject': 'Dans clasic',
            'grades': ['IV'],
            'weekly_hours_count': [7]
        },
        {
            'subject': 'Ritmică',
            'grades': ['IV'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Arte vizuale și abilități practice',
            'grades': ['P', 'I', 'II', 'III', 'IV'],
            'weekly_hours_count': [2, 2, 2, 2, 1]
        },
        {
            'subject': 'Dezvoltare personală',
            'grades': ['P', 'I', 'II'],
            'weekly_hours_count': [2, 1, 1]
        }
    ],
    "optional_subjects_weekly_hours": {
        "P": 1,
        "I": 1,
        "II": 1,
        "III": 1,
        "IV": 1
    }
}
PRIMARY_SCHOOL_SPORT = {
    "subjects": [
        {
            'subject': 'Comunicare în limba română',
            'grades': ['P', 'I', 'II'],
            'weekly_hours_count': [5, 7, 6]
        },
        {
            'subject': 'Limba și literatura română',
            'grades': ['III', 'IV'],
            'weekly_hours_count': [5, 5]
        },
        {
            'subject': 'Limba modernă',
            'grades': ['P', 'I', 'II', 'III', 'IV'],
            'weekly_hours_count': [1, 1, 1, 2, 2]
        },
        {
            'subject': 'Matematică și explorarea mediului',
            'grades': ['P', 'I', 'II'],
            'weekly_hours_count': [4, 4, 5]
        },
        {
            'subject': 'Matematică',
            'grades': ['III', 'IV'],
            'weekly_hours_count': [4, 4]
        },
        {
            'subject': 'Științe ale naturii',
            'grades': ['III', 'IV'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Istorie',
            'grades': ['IV'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Geografie',
            'grades': ['IV'],
            'weekly_hours_count': [1]
        },
        {
            'subject': 'Educație civică',
            'grades': ['III', 'IV'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Religie',
            'grades': ['P', 'I', 'II', 'III', 'IV'],
            'weekly_hours_count': [1, 1, 1, 1, 1]
        },
        {
            'subject': 'Educație fizică',
            'grades': ['P', 'I', 'II', 'III', 'IV'],
            'weekly_hours_count': [2, 2, 2, 2, 2]
        },
        {
            'subject': 'Joc și mișcare',
            'grades': ['III', 'IV'],
            'weekly_hours_count': [1, 1]
        },
        {
            'subject': 'Pregătire sportivă practică',
            'grades': ['I', 'II', 'III', 'IV'],
            'weekly_hours_count': [4, 4, 4, 4]
        },
        {
            'subject': 'Muzică și mișcare',
            'grades': ['P', 'I', 'II', 'III', 'IV'],
            'weekly_hours_count': [2, 2, 2, 1, 1]
        },
        {
            'subject': 'Arte vizuale și abilități practice',
            'grades': ['P', 'I', 'II', 'III', 'IV'],
            'weekly_hours_count': [2, 2, 2, 2, 1]
        },
        {
            'subject': 'Dezvoltare personală',
            'grades': ['P', 'I', 'II'],
            'weekly_hours_count': [2, 1, 1]
        }
    ],
    "optional_subjects_weekly_hours": {
        "P": 1,
        "I": 1,
        "II": 1,
        "III": 1,
        "IV": 1
    }
}


def run():
    with transaction.atomic():
        coordination_subject = get_subject_by_name('Dirigenție')
        coordination_subject.is_coordination = True
        coordination_subject.should_be_in_taught_subjects = False
        coordination_subject.save()

        add_data_for_primary_school(SchoolUnitCategory.objects.get(name='Școală primară'), PRIMARY_SCHOOL_REGULAR)
        add_data_for_primary_school(SchoolUnitCategory.objects.get(name='Școală primară în limbă minorități naționale'), PRIMARY_SCHOOL_MINORITY_LANG)
        add_data_for_primary_school(SchoolUnitCategory.objects.get(name='Școală primară în limba română pentru minorități naționale'), PRIMARY_SCHOOL_MINORITY_RO_LANG)
        add_data_for_primary_school(SchoolUnitCategory.objects.get(name='Școală primară cu program integrat și suplimentar de artă - muzică'), PRIMARY_SCHOOL_ART_MUSIC, 'Artistic')
        add_data_for_primary_school(SchoolUnitCategory.objects.get(name='Școală primară cu program integrat și suplimentar de coregrafie'), PRIMARY_SCHOOL_CHOREOGRAPHY, 'Artistic')
        add_data_for_primary_school(SchoolUnitCategory.objects.get(name='Școală primară cu program sportiv integrat'), PRIMARY_SCHOOL_SPORT, 'Sportiv')

        set_allows_exemption()


def add_data_for_primary_school(category, category_map, academic_profile_name=None):
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
    for subject_name in ['Religie', 'Educație fizică']:
        subject = Subject.objects.get(name=subject_name)
        subject.allows_exemption = True
        subject.save()


def get_subject_by_name(name):
    subject, created = Subject.objects.get_or_create(name=name)
    return subject
