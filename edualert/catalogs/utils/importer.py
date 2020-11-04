import csv
import datetime
from gettext import gettext as _

from django.conf import settings
from django.db import DatabaseError
from django.utils import timezone
from django.utils.translation import pgettext

from edualert.academic_calendars.models import SchoolEvent
from edualert.academic_calendars.utils import get_current_academic_calendar, get_second_semester_end_events
from edualert.catalogs.models import StudentCatalogPerSubject, SubjectGrade, SubjectAbsence, ExaminationGrade
from edualert.catalogs.utils import compute_averages, change_averages_after_examination_grade_operation, \
    has_technological_category, get_current_semester
from edualert.catalogs.tasks import update_absences_counts_for_students_task
from edualert.profiles.models import Label, UserProfile
from edualert.subjects.models import ProgramSubjectThrough


class CatalogsImporter:
    report = {
        "errors": {}
    }
    file = None
    number_of_catalogs = 0
    study_class = None
    subject = None
    today = None
    current_calendar = None
    differences_event = None
    second_examinations_event = None
    is_technological_school = False
    second_semester_end_events = None
    subject_through = None
    field_mapping = {
        'Nume': 'full_name',
        'Etichete': 'labels',
        'Note sem. I': 'grades_sem1',
        'Note sem. II': 'grades_sem2',
        'Teză sem. I': 'thesis_sem1',
        'Teză sem. II': 'thesis_sem2',
        'Diferență sem. I Oral Prof. I': 'oral_difference1_sem1',
        'Diferență sem. I Oral Prof. II': 'oral_difference2_sem1',
        'Diferență sem. I Scris Prof. I': 'written_difference1_sem1',
        'Diferență sem. I Scris Prof. II': 'written_difference2_sem1',
        'Diferență sem. II Oral Prof. I': 'oral_difference1_sem2',
        'Diferență sem. II Oral Prof. II': 'oral_difference2_sem2',
        'Diferență sem. II Scris Prof. I': 'written_difference1_sem2',
        'Diferență sem. II Scris Prof. II': 'written_difference2_sem2',
        'Diferență anuală Oral Prof. I': 'oral_difference1_annual',
        'Diferență anuală Oral Prof. II': 'oral_difference2_annual',
        'Diferență anuală Scris Prof. I': 'written_difference1_annual',
        'Diferență anuală Scris Prof. II': 'written_difference2_annual',
        'Corigență Oral Prof. I': 'oral_second_examination1',
        'Corigență Oral Prof. II': 'oral_second_examination2',
        'Corigență Scris Prof. I': 'written_second_examination1',
        'Corigență Scris Prof. II': 'written_second_examination2',
        'Absențe motivate sem. I': 'founded_abs_sem1',
        'Absențe motivate sem. II': 'founded_abs_sem2',
        'Absențe nemotivate sem. I': 'unfounded_abs_sem1',
        'Absențe nemotivate sem. II': 'unfounded_abs_sem2',
        'Teste inițiale / finale': 'wants_level_testing_grade',
        'Observații': 'remarks',
        'Teză': 'wants_thesis',
        'Simulări': 'wants_simulation',
        'Scutit': 'is_exempted',
        'Înregistrat opțional': 'is_enrolled'
    }
    grade_fields = [
        'thesis_sem1', 'thesis_sem2', 'oral_difference1_sem1', 'oral_difference2_sem1', 'written_difference1_sem1',
        'written_difference2_sem1', 'oral_difference1_sem2', 'oral_difference2_sem2', 'written_difference1_sem2',
        'written_difference2_sem2', 'oral_difference1_annual', 'oral_difference2_annual', 'written_difference1_annual',
        'written_difference2_annual', 'oral_second_examination1', 'oral_second_examination2', 'written_second_examination1',
        'written_second_examination2', 'grades_sem1', 'grades_sem2'
    ]

    def __init__(self, file, study_class, subject, current_calendar):
        self.report = {'errors': {}}
        self.file = file
        self.study_class = study_class
        self.subject = subject
        self.today = timezone.now().date()
        self.current_calendar = current_calendar or get_current_academic_calendar()
        self.reverse_field_mapping = {value: field for field, value in self.field_mapping.items()}

    def import_catalogs_and_get_report(self):
        catalogs = self._fetch_from_csv()
        self._save(catalogs)
        self._update_report_with_statistics()
        return self.report

    def _fetch_from_csv(self):
        return csv.DictReader(self.file)

    def _save(self, catalog_data):
        catalogs_to_update = []
        catalog_fields_to_update = ['remarks', 'wants_level_testing_grade', 'wants_thesis', 'wants_simulation', 'is_exempted', 'is_enrolled']
        catalogs_with_difference_grades = []
        catalogs_with_second_examination_grades = []
        self.is_technological_school = has_technological_category(self.study_class.school_unit)
        self.second_semester_end_events = get_second_semester_end_events(self.current_calendar)
        self.examination_events = self._get_examination_events()

        self.subject_through = ProgramSubjectThrough.objects.filter(
            class_grade=self.study_class.class_grade,
            generic_academic_program_id=self.study_class.academic_program.generic_academic_program_id,
            subject=self.subject
        ).first()

        for index, catalog_dict in enumerate(catalog_data):
            self.number_of_catalogs += 1

            # Clean data
            cleaned_data = self._clean_data(catalog_dict)
            errors = cleaned_data.pop('errors', None)
            if errors:
                self._add_row_to_report(index + 1, errors)
                continue

            # Get the profile instances
            user_profile = UserProfile.objects.filter(
                user_role=UserProfile.UserRoles.STUDENT,
                student_in_class_id=self.study_class.id,
                full_name=cleaned_data['full_name']
            ).first()
            if not user_profile:
                self._add_row_to_report(index + 1, {self.reverse_field_mapping['full_name']: _("A student with this name doesn't exist yet.")})
                continue

            # Get the catalog instance
            catalog = StudentCatalogPerSubject.objects.filter(
                student_id=user_profile.id,
                study_class_id=self.study_class.id,
                academic_year=self.current_calendar.academic_year
            ).prefetch_related(
                'grades', 'examination_grades'
            ).first()
            if not catalog:
                self._add_row_to_report(index + 1, {self.reverse_field_mapping['full_name']: _("A catalog for this student and subject doesn't exist yet.")})
                continue

            existing_examination_grades = self._get_examination_grades(catalog)

            # Validate data
            validated_data = self._validate_data(catalog, cleaned_data, existing_examination_grades)
            errors = validated_data.pop('errors', None)
            if errors:
                self._add_row_to_report(index + 1, errors)
                continue

            # Delete old examination, thesis and regular grades if they need to be overridden
            if catalog.is_enrolled:
                has_difference_grade = False
                has_second_examination_grade = False

                if validated_data['oral_difference1_sem1'] and validated_data['oral_difference2_sem1'] and existing_examination_grades.get('oral_difference_sem1'):
                    existing_examination_grades['oral_difference_sem1'].delete()
                    has_difference_grade = True
                    
                if validated_data['written_difference1_sem1'] and validated_data['written_difference2_sem1'] and existing_examination_grades.get('written_difference_sem1'):
                    existing_examination_grades['written_difference_sem1'].delete()
                    has_difference_grade = True

                if validated_data['oral_difference1_sem2'] and validated_data['oral_difference2_sem2'] and existing_examination_grades.get('oral_difference_sem2'):
                    existing_examination_grades['oral_difference_sem2'].delete()
                    has_difference_grade = True

                if validated_data['written_difference1_sem2'] and validated_data['written_difference2_sem2'] and existing_examination_grades.get('written_difference_sem2'):
                    existing_examination_grades['written_difference_sem2'].delete()
                    has_difference_grade = True
                    
                if validated_data['written_difference1_annual'] and validated_data['written_difference2_annual'] and existing_examination_grades.get('written_difference_annual'):
                    existing_examination_grades['written_difference_annual'].delete()
                    has_difference_grade = True
                
                if validated_data['oral_difference1_annual'] and validated_data['oral_difference2_annual'] and existing_examination_grades.get('oral_difference_annual'):
                    existing_examination_grades['oral_difference_annual'].delete()
                    has_difference_grade = True

                if validated_data['oral_second_examination1'] and validated_data['oral_second_examination2'] and existing_examination_grades.get('oral_second_examination'):
                    existing_examination_grades['oral_second_examination'].delete()
                    has_second_examination_grade = True

                if validated_data['written_second_examination1'] and validated_data['written_second_examination2'] and existing_examination_grades.get('written_second_examination'):
                    existing_examination_grades['written_second_examination'].delete()
                    has_second_examination_grade = True

                if has_difference_grade:
                    catalogs_with_difference_grades.append(catalog)
                if has_second_examination_grade:
                    catalogs_with_second_examination_grades.append(catalog)

                if validated_data['grades_sem1'] and self.subject.is_coordination:
                    SubjectGrade.objects.filter(
                        catalog_per_subject=catalog,
                        semester=1,
                        grade_type=SubjectGrade.GradeTypes.REGULAR
                    ).delete()
                if validated_data['grades_sem2'] and self.subject.is_coordination:
                    SubjectGrade.objects.filter(
                        catalog_per_subject=catalog,
                        semester=2,
                        grade_type=SubjectGrade.GradeTypes.REGULAR
                    ).delete()

                for grade in catalog.grades.all():
                    if grade.grade_type == SubjectGrade.GradeTypes.THESIS:
                        if validated_data['thesis_sem1'] and grade.semester == 1:
                            grade.delete()
                        elif validated_data['thesis_sem2'] and grade.semester == 2:
                            grade.delete()

            try:
                # Create/Update the instances
                user_profile.labels.add(*validated_data['labels'])
                for field in catalog_fields_to_update:
                    setattr(catalog, field, validated_data[field])

                if catalog.is_enrolled:
                    for field, validated_data_key in zip(
                            ['founded_abs_count_sem1', 'founded_abs_count_sem2', 'unfounded_abs_count_sem1', 'unfounded_abs_count_sem2'],
                            ['founded_abs_sem1', 'founded_abs_sem2', 'unfounded_abs_sem1', 'unfounded_abs_sem2']
                    ):
                        setattr(catalog, field, getattr(catalog, field) + len(validated_data[validated_data_key]))
                    catalog.founded_abs_count_annual = catalog.founded_abs_count_sem1 + catalog.founded_abs_count_sem2
                    catalog.unfounded_abs_count_annual = catalog.unfounded_abs_count_sem1 + catalog.unfounded_abs_count_sem2

                    grades_to_create, absences_to_create, examination_grades_to_create = self._create_grades_and_absences(validated_data, catalog, user_profile)
                    SubjectGrade.objects.bulk_create(grades_to_create)
                    SubjectAbsence.objects.bulk_create(absences_to_create)
                    ExaminationGrade.objects.bulk_create(examination_grades_to_create)
                catalogs_to_update.append(catalog)

            except DatabaseError:
                self._add_row_to_report(index + 1, {'general_errors': _('An error occurred while creating the catalog')})

        StudentCatalogPerSubject.objects.bulk_update(
            catalogs_to_update,
            fields=[
                *catalog_fields_to_update,
                'founded_abs_count_sem1', 'founded_abs_count_sem2', 'unfounded_abs_count_sem1', 'unfounded_abs_count_sem2',
                'founded_abs_count_annual', 'unfounded_abs_count_annual'
            ]
        )

        for catalog in catalogs_to_update:
            catalog.refresh_from_db()

        catalogs_to_update_averages_for = [catalog for catalog in catalogs_to_update if catalog.is_enrolled]
        self._update_averages(catalogs_to_update_averages_for, catalogs_with_difference_grades, catalogs_with_second_examination_grades)

    def _clean_data(self, catalog_dict):
        accepted_fields = self.field_mapping.keys()
        sent_fields = catalog_dict.keys()
        errors = {field: _('This field is required.') for field in accepted_fields if field not in sent_fields}

        cleaned_data = {
            'full_name': catalog_dict.get('Nume'),
            'labels': [label.strip() for label in catalog_dict.get('Etichete', '').split(';')],
            'remarks': catalog_dict.get('Observații')
        }

        # Clean grades and absences
        for grade_key in self.grade_fields:
            csv_key = self.reverse_field_mapping[grade_key]
            grades = catalog_dict[csv_key].replace(' ', '').split(';') if csv_key in catalog_dict else []

            if not any(grades):
                cleaned_data[grade_key] = []
                continue

            for grade in grades:
                date_error = None
                taken_at, grade_value, error = self._validate_and_clean_grade(grade)
                if taken_at and grade_value:
                    taken_at, date_error = self._validate_and_clean_date(taken_at)

                if error or date_error:
                    errors[csv_key] = error or date_error
                    continue

                if grade_key in cleaned_data:
                    cleaned_data[grade_key].append((taken_at, grade_value))
                else:
                    cleaned_data[grade_key] = [(taken_at, grade_value)]

        for absence_key in ['Absențe motivate sem. I', 'Absențe motivate sem. II', 'Absențe nemotivate sem. I', 'Absențe nemotivate sem. II', ]:
            for absence in catalog_dict[absence_key].replace(' ', '').split(';') if absence_key in catalog_dict else []:
                taken_at, error = self._validate_and_clean_date(absence)
                if error:
                    errors[absence_key] = error
                    continue

                cleaned_data_key = self.field_mapping[absence_key]
                if cleaned_data_key in cleaned_data:
                    cleaned_data[cleaned_data_key].append(taken_at)
                else:
                    cleaned_data[cleaned_data_key] = [taken_at]

        for field in ['Teste inițiale / finale', 'Teză', 'Simulări', 'Scutit', 'Înregistrat opțional']:
            if field in catalog_dict:
                value = catalog_dict[field].lower()
                if value not in ['da', 'nu']:
                    errors[field] = _('Must be either "Da" or "Nu".')
                    continue

                cleaned_data[self.field_mapping[field]] = True if value == 'da' else False

        cleaned_data['errors'] = errors
        return cleaned_data

    def _validate_data(self, catalog, data, existing_examination_grades):
        errors = {}
        outside_first_semester_error = _('Must be inside the first semester.')
        outside_second_semester_error = _('Must be inside the second semester.')

        # Validate labels
        actual_labels = Label.objects.filter(user_role=UserProfile.UserRoles.STUDENT, text__in=data['labels'])
        if len(actual_labels) != len(data['labels']):
            errors[self.reverse_field_mapping['labels']] = _('Labels must exist, be unique, and be for the student user role.')
        data['labels'] = actual_labels

        # Validate grades
        for grade_key in self.grade_fields:
            if grade_key not in ['grades_sem1', 'grades_sem2'] and len(data[grade_key]) > 1:
                errors[self.reverse_field_mapping[grade_key]] = _('Only one grade allowed.')

            if self.subject.is_coordination:
                if grade_key not in ['grades_sem1', 'grades_sem2'] and data[grade_key]:
                    errors[self.reverse_field_mapping[grade_key]] = _('This field is not allowed for coordination subjects.')
                elif grade_key in ['grades_sem1', 'grades_sem2'] and len(data[grade_key]) > 1:
                    errors[self.reverse_field_mapping[grade_key]] = _('Maximum one grade per semester allowed for coordination grades.')

        for field in ['grades_sem1', 'thesis_sem1']:
            for grade in data[field]:
                if not get_current_semester(
                        grade[0], self.current_calendar, self.second_semester_end_events, self.study_class.class_grade_arabic, self.is_technological_school
                ) == 1:
                    errors[self.reverse_field_mapping[field]] = outside_first_semester_error

        for field in ['grades_sem2', 'thesis_sem2']:
            for grade in data[field]:
                if not get_current_semester(
                        grade[0], self.current_calendar, self.second_semester_end_events, self.study_class.class_grade_arabic, self.is_technological_school
                ) == 2:
                    errors[self.reverse_field_mapping[field]] = outside_second_semester_error

        sem1_differences_keys = ['oral_difference1_sem1', 'oral_difference2_sem1', 'written_difference1_sem1', 'written_difference2_sem1']
        sem2_differences_keys = ['oral_difference1_sem2', 'oral_difference2_sem2', 'written_difference1_sem2', 'written_difference2_sem2']
        annual_differences_keys = ['oral_difference1_annual', 'oral_difference2_annual', 'written_difference1_annual', 'written_difference2_annual']
        second_examination_keys = ['oral_second_examination1', 'oral_second_examination2', 'written_second_examination1', 'written_second_examination2']

        sem1_differences = [data[key] for key in sem1_differences_keys]
        sem2_differences = [data[key] for key in sem2_differences_keys]
        annual_differences = [data[key] for key in annual_differences_keys]
        second_examinations = [data[key] for key in second_examination_keys]

        for differences, fields in zip([sem1_differences, sem2_differences, annual_differences], [sem1_differences_keys, sem2_differences_keys, annual_differences_keys]):
            if not (all(differences) or not any(differences)):
                for field in fields:
                    errors[self.reverse_field_mapping[field]] = _('Cannot add difference unless all fields for this semester are provided.')

        has_grades_sem1 = any(data['grades_sem1']) or any(data['thesis_sem1'])
        has_grades_sem2 = any(data['grades_sem2']) or any(data['thesis_sem2'])

        for grade in catalog.grades.all():
            if grade.semester == 1:
                has_grades_sem1 = True
            elif grade.semester == 2:
                has_grades_sem2 = True
            if has_grades_sem1 and has_grades_sem2:
                break

        for has_grade, fields_to_check in zip([has_grades_sem1, has_grades_sem2], [sem1_differences_keys, sem2_differences_keys]):
            if has_grade:
                for field in fields_to_check:
                    if data[field]:
                        errors[self.reverse_field_mapping[field]] = _('Cannot have difference grades if there already are grades for this semester.')

        if has_grades_sem1 or has_grades_sem2 or any(existing_examination_grades.values()) or any(sem1_differences) or any(sem2_differences) or any(second_examinations):
            for field in annual_differences_keys:
                if data[field]:
                    errors[self.reverse_field_mapping[field]] = _('Cannot have difference grades if there already are grades this year.')

        for examination_keys, examination_event in [
            ([*sem1_differences_keys, *sem2_differences_keys, *annual_differences_keys], 'difference'),
            (second_examination_keys, 'second_examination')
        ]:
            for examination_key in examination_keys:
                for grade in data[examination_key]:
                    if not self.examination_events[examination_event] or \
                            not self.examination_events[examination_event].starts_at <= grade[0] <= self.examination_events[examination_event].ends_at:
                        errors[self.reverse_field_mapping[examination_key]] = _('Must be during the examination event.')

        # Validate absences
        for field in ['founded_abs_sem1', 'unfounded_abs_sem1']:
            for absence in data[field]:
                if not get_current_semester(
                        absence, self.current_calendar, self.second_semester_end_events, self.study_class.class_grade_arabic, self.is_technological_school
                ) == 1:
                    errors[self.reverse_field_mapping[field]] = outside_first_semester_error

        for field in ['founded_abs_sem2', 'unfounded_abs_sem2']:
            for absence in data[field]:
                if not get_current_semester(
                        absence, self.current_calendar, self.second_semester_end_events, self.study_class.class_grade_arabic, self.is_technological_school
                ) == 2:
                    errors[self.reverse_field_mapping[field]] = outside_second_semester_error

        # Validate remarks
        if len(data['remarks']) > 500:
            errors[self.reverse_field_mapping['remarks']] = _('Maximum 500 characters allowed.')

        # Validate boolean fields
        if not data['wants_thesis']:
            thesis_error = _("Thesis grades are not allowed if the user doesn't want thesis.")
            if data['thesis_sem1']:
                errors[self.reverse_field_mapping['thesis_sem1']] = thesis_error

            if data['thesis_sem2']:
                errors[self.reverse_field_mapping['thesis_sem2']] = thesis_error

            for grade in catalog.grades.all():
                if grade.grade_type == SubjectGrade.GradeTypes.THESIS:
                    errors[self.reverse_field_mapping['wants_thesis']] = _('This field cannot be false if the student already has thesis grades.')
                    break

        if data['is_exempted'] and not self.subject.allows_exemption:
            errors[self.reverse_field_mapping['is_exempted']] = _('The subject does not allow exemption.')

        if self.subject_through and not data['is_enrolled']:
            errors[self.reverse_field_mapping['is_enrolled']] = _('Must be enrolled to all mandatory subjects.')

        data['errors'] = errors
        return data

    def _create_grades_and_absences(self, validated_data, catalog, student):
        grades_to_create = []
        absences_to_create = []
        examination_grades_to_create = []

        grade_kwargs = {
            'catalog_per_subject': catalog,
            'student': student,
            'subject_name': self.subject.name,
            'academic_year': self.current_calendar.academic_year,
        }
        absence_kwargs = {
            'catalog_per_subject': catalog,
            'student': student,
            'subject_name': self.subject.name,
            'academic_year': self.current_calendar.academic_year,
        }

        for grade in validated_data['grades_sem1']:
            grades_to_create.append(SubjectGrade(
                **grade_kwargs,
                semester=1,
                taken_at=grade[0],
                grade=grade[1],
                grade_type=SubjectGrade.GradeTypes.REGULAR
            ))
        for grade in validated_data['grades_sem2']:
            grades_to_create.append(SubjectGrade(
                **grade_kwargs,
                semester=2,
                taken_at=grade[0],
                grade=grade[1],
                grade_type=SubjectGrade.GradeTypes.REGULAR
            ))

        for grade in validated_data['thesis_sem1']:
            grades_to_create.append(SubjectGrade(
                **grade_kwargs,
                semester=1,
                taken_at=grade[0],
                grade=grade[1],
                grade_type=SubjectGrade.GradeTypes.THESIS
            ))
        for grade in validated_data['thesis_sem2']:
            grades_to_create.append(SubjectGrade(
                **grade_kwargs,
                semester=2,
                taken_at=grade[0],
                grade=grade[1],
                grade_type=SubjectGrade.GradeTypes.THESIS
            ))

        for absence in validated_data['founded_abs_sem1']:
            absences_to_create.append(SubjectAbsence(
                **absence_kwargs,
                semester=1,
                taken_at=absence,
                is_founded=True
            ))
        for absence in validated_data['founded_abs_sem2']:
            absences_to_create.append(SubjectAbsence(
                **absence_kwargs,
                semester=2,
                taken_at=absence,
                is_founded=True
            ))
        for absence in validated_data['unfounded_abs_sem1']:
            absences_to_create.append(SubjectAbsence(
                **absence_kwargs,
                semester=1,
                taken_at=absence,
                is_founded=False
            ))
        for absence in validated_data['unfounded_abs_sem2']:
            absences_to_create.append(SubjectAbsence(
                **absence_kwargs,
                semester=2,
                taken_at=absence,
                is_founded=False
            ))

        for grade in validated_data['oral_difference1_sem1']:
            examination_grades_to_create.append(
                ExaminationGrade(
                    **grade_kwargs,
                    examination_type=ExaminationGrade.ExaminationTypes.ORAL,
                    grade_type=ExaminationGrade.GradeTypes.DIFFERENCE,
                    grade1=validated_data['oral_difference1_sem1'][0][1],
                    grade2=validated_data['oral_difference2_sem1'][0][1],
                    taken_at=grade[0],
                    semester=1
                )
            )
        for grade in validated_data['oral_difference1_sem2']:
            examination_grades_to_create.append(
                ExaminationGrade(
                    **grade_kwargs,
                    examination_type=ExaminationGrade.ExaminationTypes.ORAL,
                    grade_type=ExaminationGrade.GradeTypes.DIFFERENCE,
                    grade1=validated_data['oral_difference1_sem2'][0][1],
                    grade2=validated_data['oral_difference2_sem2'][0][1],
                    taken_at=grade[0],
                    semester=2
                )
            )
        for grade in validated_data['oral_difference1_annual']:
            examination_grades_to_create.append(
                ExaminationGrade(
                    **grade_kwargs,
                    examination_type=ExaminationGrade.ExaminationTypes.ORAL,
                    grade_type=ExaminationGrade.GradeTypes.DIFFERENCE,
                    grade1=validated_data['oral_difference1_annual'][0][1],
                    grade2=validated_data['oral_difference2_annual'][0][1],
                    taken_at=grade[0],
                )
            )
        for grade in validated_data['written_difference1_sem1']:
            examination_grades_to_create.append(
                ExaminationGrade(
                    **grade_kwargs,
                    examination_type=ExaminationGrade.ExaminationTypes.WRITTEN,
                    grade_type=ExaminationGrade.GradeTypes.DIFFERENCE,
                    grade1=validated_data['written_difference1_sem1'][0][1],
                    grade2=validated_data['written_difference2_sem1'][0][1],
                    taken_at=grade[0],
                    semester=1
                )
            )
        for grade in validated_data['written_difference1_sem2']:
            examination_grades_to_create.append(
                ExaminationGrade(
                    **grade_kwargs,
                    examination_type=ExaminationGrade.ExaminationTypes.WRITTEN,
                    grade_type=ExaminationGrade.GradeTypes.DIFFERENCE,
                    grade1=validated_data['written_difference1_sem2'][0][1],
                    grade2=validated_data['written_difference2_sem2'][0][1],
                    taken_at=grade[0],
                    semester=2
                )
            )
        for grade in validated_data['written_difference1_annual']:
            examination_grades_to_create.append(
                ExaminationGrade(
                    **grade_kwargs,
                    examination_type=ExaminationGrade.ExaminationTypes.WRITTEN,
                    grade_type=ExaminationGrade.GradeTypes.DIFFERENCE,
                    grade1=validated_data['written_difference1_annual'][0][1],
                    grade2=validated_data['written_difference2_annual'][0][1],
                    taken_at=grade[0],
                )
            )
        for grade in validated_data['oral_second_examination1']:
            examination_grades_to_create.append(
                ExaminationGrade(
                    **grade_kwargs,
                    examination_type=ExaminationGrade.ExaminationTypes.ORAL,
                    grade_type=ExaminationGrade.GradeTypes.SECOND_EXAMINATION,
                    grade1=validated_data['oral_second_examination1'][0][1],
                    grade2=validated_data['oral_second_examination2'][0][1],
                    taken_at=grade[0]
                )
            )
        for grade in validated_data['written_second_examination1']:
            examination_grades_to_create.append(
                ExaminationGrade(
                    **grade_kwargs,
                    examination_type=ExaminationGrade.ExaminationTypes.WRITTEN,
                    grade_type=ExaminationGrade.GradeTypes.SECOND_EXAMINATION,
                    grade1=validated_data['written_second_examination1'][0][1],
                    grade2=validated_data['written_second_examination2'][0][1],
                    taken_at=grade[0]
                )
            )

        return grades_to_create, absences_to_create, examination_grades_to_create

    def _update_averages(self, catalogs, catalogs_with_difference_grades, catalogs_with_second_examination_grades):
        compute_averages(catalogs, 1, is_async=False)
        compute_averages(catalogs, 2, is_async=False)

        if catalogs_with_difference_grades:
            change_averages_after_examination_grade_operation(
                catalogs_with_difference_grades, grade_type=ExaminationGrade.GradeTypes.DIFFERENCE, semester=1,
            )
            change_averages_after_examination_grade_operation(
                catalogs_with_difference_grades, grade_type=ExaminationGrade.GradeTypes.DIFFERENCE, semester=2,
            )
            change_averages_after_examination_grade_operation(
                catalogs_with_difference_grades, grade_type=ExaminationGrade.GradeTypes.DIFFERENCE, semester=None,
            )
        if catalogs_with_second_examination_grades:
            change_averages_after_examination_grade_operation(
                catalogs_with_second_examination_grades, grade_type=ExaminationGrade.GradeTypes.SECOND_EXAMINATION, semester=None,
            )

        catalog_ids = [catalog.id for catalog in catalogs]
        update_absences_counts_for_students_task.delay(catalog_ids)

    def _get_examination_events(self):
        events = SchoolEvent.objects.filter(academic_year_calendar_id=self.current_calendar.id)
        examination_events = {'difference': None, 'second_examination': None}
        for event in events:
            if event.event_type == SchoolEvent.EventTypes.DIFERENTE:
                examination_events['difference'] = event
            if event.event_type == SchoolEvent.EventTypes.CORIGENTE:
                examination_events['second_examination'] = event
        return examination_events

    @staticmethod
    def _get_examination_grades(catalog):
        examination_grades = catalog.examination_grades.all()
        grades = {}
        for grade in examination_grades:
            if grade.semester == 1:
                if grade.examination_type == ExaminationGrade.ExaminationTypes.ORAL:
                    grades['oral_difference_sem1'] = grade
                if grade.examination_type == ExaminationGrade.ExaminationTypes.WRITTEN:
                    grades['written_difference_sem2'] = grade
            elif grade.semester == 2:
                if grade.examination_type == ExaminationGrade.ExaminationTypes.ORAL:
                    grades['oral_difference_sem2'] = grade
                elif grade.examination_type == ExaminationGrade.ExaminationTypes.WRITTEN:
                    grades['written_difference_sem2'] = grade
            else:
                if grade.grade_type == ExaminationGrade.GradeTypes.DIFFERENCE:
                    if grade.examination_type == ExaminationGrade.ExaminationTypes.ORAL:
                        grades['oral_difference_annual'] = grade
                    elif grade.examination_type == ExaminationGrade.ExaminationTypes.WRITTEN:
                        grades['written_difference_annual'] = grade
                elif grade.grade_type == ExaminationGrade.GradeTypes.SECOND_EXAMINATION:
                    if grade.examination_type == ExaminationGrade.ExaminationTypes.ORAL:
                        grades['oral_second_examination'] = grade
                    elif grade.examination_type == ExaminationGrade.ExaminationTypes.WRITTEN:
                        grades['written_second_examination'] = grade

        return grades

    @staticmethod
    def _validate_and_clean_grade(grade):
        error = ''
        try:
            taken_at, grade_value = grade.replace(' ', '').split(':')
            grade_value = int(grade_value)

            if not 1 <= grade_value <= 10:
                error = _('Grade must be between 1 and 10.')

            return taken_at, grade_value, error
        except ValueError:
            error = _('Must be in the format DD-MM-YYYY: grade.')
            return None, None, error

    def _validate_and_clean_date(self, date):
        error = ''
        try:
            date = datetime.datetime.strptime(date.replace(' ', ''), settings.DATE_FORMAT).date()

            if date > self.today:
                error = _('Date must be in the past.')

            return date, error
        except ValueError:
            error = _('Date must be in the format DD-MM-YYYY')
            return None, error

    def _add_row_to_report(self, row_number, error_details):
        self.report['errors'][row_number] = error_details

    def _update_report_with_statistics(self):
        actual_saved_catalogs = self.number_of_catalogs - len(self.report['errors'])
        self.report['report'] = pgettext(
            'catalogs', '{} out of {} {} saved successfully.'
        ).format(actual_saved_catalogs, self.number_of_catalogs, _('catalog') if self.number_of_catalogs == 1 else _('catalogs'))
