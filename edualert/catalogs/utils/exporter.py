from django.conf import settings

from edualert.catalogs.models import ExaminationGrade, SubjectGrade


def get_catalog_csv_representation(catalog, study_class):
    examination_grades = catalog.examination_grades.all()
    subject_grades = catalog.grades.all()
    absences = catalog.absences.all()

    written_difference_grade1_sem1 = ''
    written_difference_grade2_sem1 = ''
    oral_difference_grade1_sem1 = ''
    oral_difference_grade2_sem1 = ''
    written_difference_grade1_sem2 = ''
    written_difference_grade2_sem2 = ''
    oral_difference_grade1_sem2 = ''
    oral_difference_grade2_sem2 = ''
    written_difference_grade1_annual = ''
    written_difference_grade2_annual = ''
    oral_difference_grade1_annual = ''
    oral_difference_grade2_annual = ''
    oral_second_examination_grade1 = ''
    oral_second_examination_grade2 = ''
    written_second_examination_grade1 = ''
    written_second_examination_grade2 = ''

    grades_sem1 = []
    grades_sem2 = []
    thesis_sem1 = ''
    thesis_sem2 = ''

    founded_abs_sem1 = []
    founded_abs_sem2 = []
    unfounded_abs_sem1 = []
    unfounded_abs_sem2 = []

    for grade in examination_grades:
        grade_repr = f'{grade.taken_at.strftime(settings.DATE_FORMAT)}: '
        grade1_repr = grade_repr + str(grade.grade1)
        grade2_repr = grade_repr + str(grade.grade2)
        if grade.grade_type == ExaminationGrade.GradeTypes.DIFFERENCE:
            if grade.examination_type == ExaminationGrade.ExaminationTypes.ORAL:
                if grade.semester == 1:
                    oral_difference_grade1_sem1 = grade1_repr
                    oral_difference_grade2_sem1 = grade2_repr
                elif grade.semester == 2:
                    oral_difference_grade1_sem2 = grade1_repr
                    oral_difference_grade2_sem2 = grade2_repr
                else:
                    oral_difference_grade1_annual = grade1_repr
                    oral_difference_grade2_annual = grade2_repr

            elif grade.examination_type == ExaminationGrade.ExaminationTypes.WRITTEN:
                if grade.semester == 1:
                    written_difference_grade1_sem1 = grade1_repr
                    written_difference_grade2_sem1 = grade2_repr
                elif grade.semester == 2:
                    written_difference_grade1_sem2 = grade1_repr
                    written_difference_grade2_sem2 = grade2_repr
                else:
                    written_difference_grade1_annual = grade1_repr
                    written_difference_grade2_annual = grade2_repr

        elif grade.grade_type == ExaminationGrade.GradeTypes.SECOND_EXAMINATION:
            if grade.examination_type == ExaminationGrade.ExaminationTypes.ORAL:
                oral_second_examination_grade1 = grade1_repr
                oral_second_examination_grade2 = grade2_repr
            elif grade.examination_type == ExaminationGrade.ExaminationTypes.WRITTEN:
                written_second_examination_grade1 = grade1_repr
                written_second_examination_grade2 = grade2_repr

    for grade in subject_grades:
        grade_repr = f'{grade.taken_at.strftime(settings.DATE_FORMAT)}: {grade.grade}'
        if grade.grade_type == SubjectGrade.GradeTypes.REGULAR:
            if grade.semester == 1:
                grades_sem1.append(grade_repr)
            elif grade.semester == 2:
                grades_sem2.append(grade_repr)
        if grade.grade_type == SubjectGrade.GradeTypes.THESIS:
            if grade.semester == 1:
                thesis_sem1 = grade_repr
            elif grade.semester == 2:
                thesis_sem2 = grade_repr

    for absence in absences:
        absence_repr = absence.taken_at.strftime(settings.DATE_FORMAT)
        if absence.is_founded:
            if absence.semester == 1:
                founded_abs_sem1.append(absence_repr)
            elif absence.semester == 2:
                founded_abs_sem2.append(absence_repr)
        else:
            if absence.semester == 1:
                unfounded_abs_sem1.append(absence_repr)
            elif absence.semester == 2:
                unfounded_abs_sem2.append(absence_repr)

    return {
        'Nume': catalog.student.full_name,
        'Clasă': study_class.class_grade + ' ' + study_class.class_letter,
        'Etichete': '; '.join([label.text for label in catalog.student.labels.all()]),
        'Note sem. I': '; '.join(grades_sem1),
        'Teză sem. I': thesis_sem1,
        'Medie sem. I': catalog.avg_sem1,
        'Note sem. II': '; '.join(grades_sem2),
        'Teză sem. II': thesis_sem2,
        'Medie sem. II': catalog.avg_sem2,
        'Medie anuală': catalog.avg_final,
        'Diferență sem. I Oral Prof. I': oral_difference_grade1_sem1,
        'Diferență sem. I Oral Prof. II': oral_difference_grade2_sem1,
        'Diferență sem. I Scris Prof. I': written_difference_grade1_sem1,
        'Diferență sem. I Scris Prof. II': written_difference_grade2_sem1,
        'Diferență sem. II Oral Prof. I': oral_difference_grade1_sem2,
        'Diferență sem. II Oral Prof. II': oral_difference_grade2_sem2,
        'Diferență sem. II Scris Prof. I': written_difference_grade1_sem2,
        'Diferență sem. II Scris Prof. II': written_difference_grade2_sem2,
        'Diferență anuală Oral Prof. I': oral_difference_grade1_annual,
        'Diferență anuală Oral Prof. II': oral_difference_grade2_annual,
        'Diferență anuală Scris Prof. I': written_difference_grade1_annual,
        'Diferență anuală Scris Prof. II': written_difference_grade2_annual,
        'Corigență Oral Prof. I': oral_second_examination_grade1,
        'Corigență Oral Prof. II': oral_second_examination_grade2,
        'Corigență Scris Prof. I': written_second_examination_grade1,
        'Corigență Scris Prof. II': written_second_examination_grade2,
        'Absențe motivate sem. I': '; '.join(founded_abs_sem1),
        'Absențe nemotivate sem. I': '; '.join(unfounded_abs_sem1),
        'Absențe motivate sem. II': '; '.join(founded_abs_sem2),
        'Absențe nemotivate sem. II': '; '.join(unfounded_abs_sem2),
        'Observații': catalog.remarks,
        'Teste inițiale / finale': catalog.wants_level_testing_grade,
        'Teză': catalog.wants_thesis,
        'Simulări': catalog.wants_simulation,
        'Scutit': catalog.is_exempted,
        'Înregistrat opțional': catalog.is_enrolled
    }
