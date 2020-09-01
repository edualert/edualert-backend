from datetime import datetime

from django.utils import timezone
from django.utils.translation import gettext as _
from rest_framework import views
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from edualert.catalogs.models import SubjectGrade, ExaminationGrade
from edualert.catalogs.utils import get_avg_limit_for_subject, get_behavior_grade_limit
from edualert.common.permissions import IsStudent, IsParent
from edualert.profiles.models import UserProfile

ABSENCE_AUTHORIZATION = 'ABSENCE_AUTHORIZATION'
NEW_AUTHORIZED_ABSENCE = 'NEW_AUTHORIZED_ABSENCE'
NEW_UNAUTHORIZED_ABSENCE = 'NEW_UNAUTHORIZED_ABSENCE'
NEW_GRADE = 'NEW_GRADE'
SECOND_EXAMINATION_AVERAGE = 'SECOND_EXAMINATION_AVERAGE'
DIFFERENCE_AVERAGE = 'DIFFERENCE_AVERAGE'


class OwnChildActivityHistory(views.APIView):
    permission_classes = (IsParent,)

    def get(self, request, *args, **kwargs):
        parent = self.request.user.user_profile
        student = get_object_or_404(
            UserProfile,
            id=self.kwargs['id'],
            user_role=UserProfile.UserRoles.STUDENT,
            parents__id=parent.id,
            school_unit_id=parent.school_unit_id
        )
        activities = get_student_activities(student)

        return Response(sorted(activities, key=lambda x: datetime.strptime(x['date'], '%d-%m-%Y'), reverse=True))


class OwnActivityHistory(views.APIView):
    permission_classes = (IsStudent,)

    def get(self, request, *args, **kwargs):
        student = self.request.user.user_profile
        activities = get_student_activities(student)

        return Response(sorted(activities, key=lambda x: datetime.strptime(x['date'], '%d-%m-%Y'), reverse=True))


def get_student_activities(student):
    now = timezone.now()
    after_limit = now - timezone.timedelta(days=15)
    before_limit = now - timezone.timedelta(hours=2)

    absences = student.absences.select_related('catalog_per_subject') \
        .filter(created__gte=after_limit, created__lte=before_limit)
    grades = student.grades.select_related('catalog_per_subject') \
        .filter(created__gte=after_limit, created__lte=before_limit)
    exam_grades = student.examination_grades.select_related('catalog_per_subject') \
        .filter(created__gte=after_limit, created__lte=before_limit)

    absences_activities = get_absences_activities(absences)
    grades_activities = get_grades_activities(grades)
    exam_grades_activities = get_exam_grades_activities(exam_grades)

    return absences_activities + grades_activities + exam_grades_activities


def get_absences_activities(absences):
    activities = []

    for absence in absences:
        if absence.modified > absence.created + timezone.timedelta(seconds=1) and absence.is_founded:
            activities.append({
                'date': absence.modified.date().strftime('%d-%m-%Y'),
                'subject_name': absence.subject_name,
                'event_type': ABSENCE_AUTHORIZATION,
                'event': _('Authorized absence from {}').format(absence.taken_at.strftime('%d-%m')),
                'is_coordination_subject': absence.catalog_per_subject.is_coordination_subject
            })
        else:
            activities.append({
                'date': absence.taken_at.strftime('%d-%m-%Y'),
                'subject_name': absence.subject_name,
                'event_type': NEW_AUTHORIZED_ABSENCE if absence.is_founded else NEW_UNAUTHORIZED_ABSENCE,
                'event': _('Authorized absence') if absence.is_founded else _('Unauthorized absence'),
                'is_coordination_subject': absence.catalog_per_subject.is_coordination_subject
            })

    return activities


def get_grades_activities(grades):
    activities = []

    for grade in grades:
        is_coordination_subject = grade.catalog_per_subject.is_coordination_subject
        if is_coordination_subject:
            academic_profile = grade.student.school_unit.academic_profile
            behavior_grade_limit = get_behavior_grade_limit(academic_profile)
        else:
            behavior_grade_limit = None

        activities.append({
            'date': grade.taken_at.strftime('%d-%m-%Y'),
            'subject_name': grade.subject_name,
            'event_type': NEW_GRADE,
            'event': _('Grade {}').format(grade.grade) if grade.grade_type == SubjectGrade.GradeTypes.REGULAR
            else _('Thesis grade {}').format(grade.grade),
            'is_coordination_subject': is_coordination_subject,
            'behavior_grade_limit': behavior_grade_limit
        })

    return activities


def get_exam_grades_activities(exam_grades):
    activities = []

    exam_groups = {}
    catalogs_map = {}
    for exam_grade in exam_grades:
        catalog = exam_grade.catalog_per_subject
        if catalog.id in exam_groups:
            exam_groups[catalog.id].append(exam_grade)
        else:
            exam_groups[catalog.id] = [exam_grade]
        catalogs_map[catalog.id] = catalog

    for catalog_id, grades in exam_groups.items():
        group_by_semester = {
            0: {
                ExaminationGrade.GradeTypes.SECOND_EXAMINATION: [],
                ExaminationGrade.GradeTypes.DIFFERENCE: []
            },
            1: [],
            2: []
        }
        for grade in grades:
            if grade.semester is not None:
                group_by_semester[grade.semester].append(grade)
            else:
                group_by_semester[0][grade.grade_type].append(grade)

        catalog = catalogs_map[catalog_id]
        grade_limit = get_avg_limit_for_subject(catalog.study_class, catalog.is_coordination_subject, catalog.subject_id)

        if len(group_by_semester[0][ExaminationGrade.GradeTypes.SECOND_EXAMINATION]) == 2 and \
                catalog.avg_after_2nd_examination is not None:
            grades = group_by_semester[0][ExaminationGrade.GradeTypes.SECOND_EXAMINATION]
            activities.append({
                'date': grades[0].taken_at.strftime('%d-%m-%Y') if grades[0].taken_at > grades[1].taken_at else grades[1].taken_at.strftime('%d-%m-%Y'),
                'subject_name': catalog.subject_name,
                'event_type': SECOND_EXAMINATION_AVERAGE,
                'event': _('Second examination average {}').format(get_printable_average(catalog.avg_after_2nd_examination)),
                'is_coordination_subject': catalog.is_coordination_subject,
                'grade_limit': grade_limit
            })
        if len(group_by_semester[0][ExaminationGrade.GradeTypes.DIFFERENCE]) == 2 and \
                catalog.avg_annual is not None:
            grades = group_by_semester[0][ExaminationGrade.GradeTypes.DIFFERENCE]
            activities.append({
                'date': grades[0].taken_at.strftime('%d-%m-%Y') if grades[0].taken_at > grades[1].taken_at else grades[1].taken_at.strftime('%d-%m-%Y'),
                'subject_name': catalog.subject_name,
                'event_type': DIFFERENCE_AVERAGE,
                'event': _('Difference average {} for class {}').format(get_printable_average(catalog.avg_annual), catalog.study_class.class_grade),
                'is_coordination_subject': catalog.is_coordination_subject,
                'grade_limit': grade_limit
            })
        if len(group_by_semester[1]) == 2 and catalog.avg_sem1 is not None:
            grades = group_by_semester[1]
            activities.append({
                'date': grades[0].taken_at.strftime('%d-%m-%Y') if grades[0].taken_at > grades[1].taken_at else grades[1].taken_at.strftime('%d-%m-%Y'),
                'subject_name': catalog.subject_name,
                'event_type': DIFFERENCE_AVERAGE,
                'event': _('Difference average {} for class {}, semester 1').format(catalog.avg_sem1, catalog.study_class.class_grade),
                'is_coordination_subject': catalog.is_coordination_subject,
                'grade_limit': grade_limit
            })
        if len(group_by_semester[2]) == 2 and catalog.avg_sem2 is not None:
            grades = group_by_semester[2]
            activities.append({
                'date': grades[0].taken_at.strftime('%d-%m-%Y') if grades[0].taken_at > grades[1].taken_at else grades[1].taken_at.strftime('%d-%m-%Y'),
                'subject_name': catalog.subject_name,
                'event_type': DIFFERENCE_AVERAGE,
                'event': _('Difference average {} for class {}, semester 2').format(catalog.avg_sem2, catalog.study_class.class_grade),
                'is_coordination_subject': catalog.is_coordination_subject,
                'grade_limit': grade_limit
            })

    return activities


def get_printable_average(avg):
    if avg == int(avg):
        return '{:.0f}'.format(avg)

    return '{:.1f}'.format(avg)
