import datetime

from django.db import transaction
from django.db.models import Min
from django.http import Http404
from methodtools import lru_cache

from django.utils import timezone
from django.utils.translation import gettext as _
from rest_framework import generics, status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from edualert.academic_calendars.utils import get_current_academic_calendar
from edualert.catalogs.models import StudentCatalogPerYear, StudentCatalogPerSubject
from edualert.catalogs.utils import update_last_change_in_catalog
from edualert.common.constants import POST, PUT, PATCH
from edualert.common.permissions import IsPrincipal, IsTeacherOrPrincipal
from edualert.notifications.models import Notification
from edualert.profiles.models import UserProfile
from edualert.study_classes.models import StudyClass
from edualert.study_classes.serializers import StudyClassListSerializer, StudyClassDetailSerializer, \
    StudyClassNameSerializer, StudyClassCreateUpdateSerializer, StudyClassPartiallyUpdateSerializer, \
    StudyClassClonedToNextYearSerializer
from edualert.study_classes.tasks import get_catalogs_per_year, get_catalogs_per_subject, get_study_class_subjects
from edualert.study_classes.utils import get_school_cycle_for_class_grade
from edualert.subjects.models import ProgramSubjectThrough
from edualert.subjects.serializers import SubjectSerializer


def get_current_school_cycle(study_class):
    calendar = get_current_academic_calendar()
    semester = 2 if calendar and timezone.now().date() >= calendar.second_semester.starts_at else 1
    if semester == 1:
        current_cycle = [
            grade for grade in get_school_cycle_for_class_grade(study_class.class_grade_arabic)
            if grade < study_class.class_grade_arabic
        ]
    else:
        current_cycle = [
            grade for grade in get_school_cycle_for_class_grade(study_class.class_grade_arabic)
            if grade <= study_class.class_grade_arabic
        ]

    return current_cycle


class StudyClassNameList(generics.ListAPIView):
    permission_classes = (IsTeacherOrPrincipal,)
    pagination_class = None
    serializer_class = StudyClassNameSerializer

    def get_queryset(self):
        profile = self.request.user.user_profile

        if profile.user_role == UserProfile.UserRoles.PRINCIPAL:
            return StudyClass.objects.filter(academic_year=self.kwargs['academic_year'],
                                             school_unit=self.request.user.user_profile.school_unit).distinct()

        return StudyClass.objects.filter(academic_year=self.kwargs['academic_year'], teachers=profile).distinct()


class StudyClassList(generics.CreateAPIView):
    permission_classes = (IsPrincipal,)
    pagination_class = None

    @lru_cache(maxsize=None)
    def get_school_unit(self):
        return self.request.user.user_profile.school_unit

    @lru_cache(maxsize=None)
    def get_current_academic_calendar(self):
        return get_current_academic_calendar()

    def get_queryset(self):
        return StudyClass.objects.filter(academic_year=self.kwargs['academic_year'],
                                         school_unit=self.get_school_unit())

    def get_serializer_class(self):
        if self.request.method == POST:
            return StudyClassCreateUpdateSerializer
        return StudyClassListSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['principal_school'] = self.get_school_unit()
        context['academic_year'] = self.kwargs['academic_year']
        return context

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        response_data = {}

        for study_class in queryset:
            serializer = self.get_serializer(study_class)
            if study_class.class_grade in response_data:
                response_data[study_class.class_grade].append(serializer.data)
            else:
                response_data[study_class.class_grade] = [serializer.data, ]

        return Response(response_data)

    def post(self, request, *args, **kwargs):
        current_calendar = self.get_current_academic_calendar()
        if not current_calendar:
            return Response({'message': _('No academic calendar defined.')}, status=status.HTTP_400_BAD_REQUEST)

        if self.kwargs['academic_year'] != current_calendar.academic_year:
            return Response({'message': _('A new study class can be added only for the current academic year.')},
                            status=status.HTTP_400_BAD_REQUEST)

        # TODO uncomment after it's tested
        # if timezone.now().date() > datetime.date(current_calendar.created.year, 9, 15):
        #     return Response({'message': _('Cannot create a study class anymore.')},
        #                     status=status.HTTP_400_BAD_REQUEST)

        return self.create(request, *args, **kwargs)


class StudyClassDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsPrincipal,)
    lookup_field = 'id'

    @lru_cache(maxsize=None)
    def get_school_unit(self):
        return self.request.user.user_profile.school_unit

    def get_queryset(self):
        return StudyClass.objects.filter(school_unit=self.get_school_unit()).select_related('class_master')

    @lru_cache(maxsize=None)
    def get_object(self):
        return super().get_object()

    def get_serializer_class(self):
        if self.request.method == PUT:
            return StudyClassCreateUpdateSerializer
        if self.request.method == PATCH:
            return StudyClassPartiallyUpdateSerializer
        return StudyClassDetailSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['principal_school'] = self.get_school_unit()
        context['academic_year'] = self.get_object().academic_year
        return context

    def check_if_operation_allowed(self, operation_name, check_date_limit=True):
        current_calendar = get_current_academic_calendar()
        if not current_calendar:
            return _('No academic calendar defined.')

        study_class = self.get_object()
        if study_class.academic_year != current_calendar.academic_year:
            return _('Cannot {} a study class from a previous year.').format(operation_name)

        # TODO uncomment after it's tested
        # if check_date_limit and timezone.now().date() > datetime.date(current_calendar.created.year, 9, 15):
        #     return _('Cannot {} the study class.').format(operation_name)

    def put(self, request, *args, **kwargs):
        error_msg = self.check_if_operation_allowed(_('update'))
        if error_msg:
            return Response({'message': error_msg}, status=status.HTTP_400_BAD_REQUEST)

        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        error_msg = self.check_if_operation_allowed(_('update'), check_date_limit=False)
        if error_msg:
            return Response({'message': error_msg}, status=status.HTTP_400_BAD_REQUEST)

        return self.partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        error_msg = self.check_if_operation_allowed(_('delete'))
        if error_msg:
            return Response({'message': error_msg}, status=status.HTTP_400_BAD_REQUEST)

        study_class = self.get_object()
        if self.get_serializer().get_has_previous_catalog_data(study_class):
            return Response({'message': _('Cannot delete the study class.')}, status=status.HTTP_400_BAD_REQUEST)

        return self.destroy(request, *args, **kwargs)


class StudyClassClonedToNextYear(generics.RetrieveAPIView):
    permission_classes = (IsPrincipal,)
    lookup_field = 'id'
    serializer_class = StudyClassClonedToNextYearSerializer

    def get_queryset(self):
        school_unit_id = self.request.user.user_profile.school_unit_id
        return StudyClass.objects.filter(school_unit_id=school_unit_id).select_related('class_master')

    def retrieve(self, request, *args, **kwargs):
        current_calendar = get_current_academic_calendar()
        if not current_calendar:
            raise Http404()

        instance = self.get_object()
        if instance.academic_year != current_calendar.academic_year - 1:
            return Response({'message': _('Can only clone study classes from previous academic year.')}, status=status.HTTP_400_BAD_REQUEST)
        if instance.class_grade_arabic in [4, 8, 12, 13]:
            return Response({'message': _('This study class cannot be cloned.')}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class StudyClassReceiverCounts(APIView):
    permission_classes = (IsTeacherOrPrincipal,)

    def get(self, *args, **kwargs):
        profile = self.request.user.user_profile

        if profile.user_role == UserProfile.UserRoles.PRINCIPAL:
            study_classes = StudyClass.objects.filter(school_unit_id=profile.school_unit_id)
        else:
            study_classes = profile.study_classes

        study_class = get_object_or_404(
            study_classes,
            id=self.kwargs.get('id')
        )

        if self.request.query_params.get('receiver_type') == Notification.ReceiverTypes.CLASS_PARENTS:
            receivers = UserProfile.objects.filter(child__student_in_class_id=study_class.id)
        else:
            receivers = UserProfile.objects.filter(student_in_class_id=study_class.id)
        receivers = receivers.only('phone_number', 'email')

        return Response({
            'total_count': len(receivers),
            'emails_count': len([receiver for receiver in receivers if not receiver.email]),
            'phone_numbers_count': len([receiver for receiver in receivers if not receiver.email])
        })


class DifferenceSubjectList(APIView):
    permission_classes = (IsPrincipal,)

    def get(self, request, *args, **kwargs):
        request_user_school_unit = self.request.user.user_profile.school_unit_id
        student = get_object_or_404(
            UserProfile.objects.select_related('student_in_class__academic_program'),
            id=self.kwargs['student_id'],
            user_role=UserProfile.UserRoles.STUDENT,
            student_in_class__isnull=False,
            school_unit_id=request_user_school_unit
        )
        study_class = get_object_or_404(
            StudyClass.objects.filter(
                school_unit_id=request_user_school_unit
            ).select_related(
                'academic_program'
            ),
            id=self.kwargs['study_class_id']
        )

        if student.student_in_class.class_grade != study_class.class_grade:
            return Response({'message': _('Cannot move students to a class from another grade.')}, status=status.HTTP_400_BAD_REQUEST)
        if student.student_in_class.academic_year != study_class.academic_year:
            return Response({'message': _('Cannot move students to a class from another year.')}, status=status.HTTP_400_BAD_REQUEST)

        difference_subjects = {}
        current_academic_program_id = getattr(student.student_in_class, 'academic_program_id', None)
        target_academic_program_id = getattr(study_class, 'academic_program_id', None)
        if current_academic_program_id == target_academic_program_id:
            return Response(difference_subjects)

        current_cycle = get_current_school_cycle(study_class)

        # Get the subjects the student studied in the current school cycle
        catalogs_per_subject = student.student_catalogs_per_subject.filter(
            study_class__class_grade_arabic__in=current_cycle
        ).select_related('study_class')
        studied_subjects = {}
        for catalog in catalogs_per_subject:
            class_grade = catalog.study_class.class_grade
            if studied_subjects.get(class_grade):
                studied_subjects[class_grade].append(catalog.subject_id)
            else:
                studied_subjects[class_grade] = [catalog.subject_id]

        # Get the subjects taught in the academic program in the current school cycle
        subject_through_for_target_program_set = ProgramSubjectThrough.objects.filter(
            generic_academic_program_id=study_class.academic_program.generic_academic_program_id,
            class_grade_arabic__in=current_cycle
        ).select_related(
            'subject'
        )

        for subject_through in subject_through_for_target_program_set:
            if subject_through.subject_id not in studied_subjects.get(subject_through.class_grade, []):
                subject_data = SubjectSerializer(subject_through.subject).data
                if difference_subjects.get(subject_through.class_grade):
                    difference_subjects[subject_through.class_grade].append(subject_data)
                else:
                    difference_subjects[subject_through.class_grade] = [subject_data]

        return Response(difference_subjects)


class MoveStudentPossibleStudyClasses(generics.ListAPIView):
    permission_classes = (IsPrincipal,)
    serializer_class = StudyClassNameSerializer
    pagination_class = None

    @lru_cache(maxsize=None)
    def get_student(self):
        return get_object_or_404(
            UserProfile.objects.select_related(
                'student_in_class'
            ),
            user_role=UserProfile.UserRoles.STUDENT,
            id=self.kwargs['id'],
            student_in_class__isnull=False,
            school_unit_id=self.request.user.user_profile.school_unit_id
        )

    def get_queryset(self):
        student = self.get_student()
        current_study_class = student.student_in_class
        school_unit = self.request.user.user_profile.school_unit

        study_classes = school_unit.study_classes.filter(
            class_grade_arabic=current_study_class.class_grade_arabic,
            academic_year=current_study_class.academic_year
        ).exclude(
            id=current_study_class.id
        ).order_by(
            'class_letter'
        )

        if current_study_class.class_grade_arabic not in [0, 5, 9]:
            previous_year_catalog = student.student_catalogs_per_year.filter(
                academic_year=current_study_class.academic_year - 1
            ).first()

            if previous_year_catalog:
                previous_final_grade = previous_year_catalog.avg_final
                past_classes_with_lower_entry_grade = school_unit.study_classes.filter(
                    academic_year=current_study_class.academic_year - 1,
                    class_grade_arabic=current_study_class.class_grade_arabic - 1
                ).annotate(
                    min_final_grade=Min('student_catalog_per_year__avg_final')
                ).filter(min_final_grade__lte=previous_final_grade)

                study_classes = study_classes.filter(
                    class_letter__in=past_classes_with_lower_entry_grade.values_list('class_letter', flat=True)
                )

        return study_classes


class MoveStudent(generics.GenericAPIView):
    permission_classes = (IsPrincipal,)
    serializer_class = StudyClassDetailSerializer

    def get_student(self):
        return get_object_or_404(
            UserProfile.objects.select_related('student_in_class'),
            user_role=UserProfile.UserRoles.STUDENT,
            id=self.kwargs['student_id'],
            student_in_class__isnull=False,
            school_unit_id=self.request.user.user_profile.school_unit_id
        )

    def get_study_class(self):
        return get_object_or_404(
            StudyClass.objects.select_related('school_unit'),
            id=self.kwargs['study_class_id'],
            school_unit_id=self.request.user.user_profile.school_unit_id
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({
            'principal_school': self.request.user.user_profile.school_unit,
        })
        return context

    @staticmethod
    def validate_destination_study_class(student, current_study_class, destination_study_class):
        if current_study_class == destination_study_class:
            return Response({'message': _('The student is already in this study class.')}, status=status.HTTP_400_BAD_REQUEST)
        if current_study_class.class_grade != destination_study_class.class_grade:
            return Response({'message': _('Cannot move students to a class from another grade.')}, status=status.HTTP_400_BAD_REQUEST)
        if current_study_class.academic_year != destination_study_class.academic_year:
            return Response({'message': _('Cannot move students to a class from another year.')}, status=status.HTTP_400_BAD_REQUEST)

        if destination_study_class.class_grade_arabic not in [0, 5, 9]:
            student_previous_year_catalog = student.student_catalogs_per_year.filter(
                academic_year=current_study_class.academic_year - 1
            ).first()

            if student_previous_year_catalog:
                previous_year_study_class = StudyClass.objects.filter(
                    school_unit_id=student.school_unit_id,
                    academic_year=destination_study_class.academic_year - 1,
                    class_grade_arabic=destination_study_class.class_grade_arabic - 1
                ).annotate(
                    min_final_grade=Min('student_catalog_per_year__avg_final')
                ).first()

                if previous_year_study_class and student_previous_year_catalog.avg_final and previous_year_study_class.min_final_grade \
                        and student_previous_year_catalog.avg_final < previous_year_study_class.min_final_grade:
                    return Response({'message': _("This student doesn't have the required average for this study class.")}, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def move_student_data(student, current_study_class, destination_study_class):
        current_cycle_grades = [
            grade for grade in get_school_cycle_for_class_grade(current_study_class.class_grade_arabic)
            if grade <= current_study_class.class_grade_arabic
        ]

        catalogs_per_year = get_catalogs_per_year(student, current_cycle_grades)
        catalogs_per_subject = get_catalogs_per_subject(student, current_cycle_grades)
        updated_catalogs_per_year = []
        updated_catalogs_per_subject = []
        created_catalogs_per_subject = []

        for grade in current_cycle_grades:
            catalog_per_year = catalogs_per_year.get(grade)
            if not catalog_per_year:
                continue

            if grade == current_study_class.class_grade_arabic:
                # Change catalog per year's study class.
                catalog_per_year.study_class = destination_study_class
                updated_catalogs_per_year.append(catalog_per_year)

                catalogs_per_subject_for_grade = catalogs_per_subject.get(grade)
                if not catalogs_per_subject_for_grade:
                    continue

                for catalog in catalogs_per_subject_for_grade:
                    catalog.is_enrolled = False

                # Change the study class and teachers for the common subject's catalogs and create the missing catalogs.
                class_subjects = get_study_class_subjects(destination_study_class)
                for subject in class_subjects:
                    found = False
                    for catalog in catalogs_per_subject_for_grade:
                        if catalog.subject_id == subject.subject_id:
                            catalog.teacher = subject.teacher
                            catalog.study_class = destination_study_class
                            catalog.is_enrolled = True
                            found = True
                            break
                    if not found and not subject.is_optional_subject:
                        created_catalogs_per_subject.append(
                            StudentCatalogPerSubject(student=student, teacher=subject.teacher, study_class=destination_study_class,
                                                     academic_year=destination_study_class.academic_year, subject=subject.subject,
                                                     subject_name=subject.subject_name, is_coordination_subject=subject.is_coordination_subject, is_enrolled=True)
                        )

                for catalog in catalogs_per_subject_for_grade:
                    updated_catalogs_per_subject.append(catalog)

            else:
                study_class = StudyClass.objects.filter(school_unit_id=student.school_unit_id,
                                                        academic_year=catalog_per_year.academic_year,
                                                        class_grade_arabic=grade,
                                                        class_letter=destination_study_class.class_letter).first()
                if not study_class:
                    continue

                # Change catalog per year's study class.
                catalog_per_year.study_class = study_class
                updated_catalogs_per_year.append(catalog_per_year)

                catalogs_per_subject_for_grade = catalogs_per_subject.get(grade)
                if not catalogs_per_subject_for_grade:
                    continue

                for catalog in catalogs_per_subject_for_grade:
                    catalog.is_enrolled = False

                # Change the study class for the common subject's catalogs and create the missing catalogs.
                subjects = get_study_class_subjects(study_class)
                for subject in subjects:
                    found = False
                    for catalog in catalogs_per_subject_for_grade:
                        if catalog.subject_id == subject.subject_id:
                            catalog.study_class = study_class
                            catalog.is_enrolled = True
                            found = True
                            break
                    if not found:
                        created_catalogs_per_subject.append(
                            StudentCatalogPerSubject(student=student, teacher=subject.teacher, study_class=study_class,
                                                     academic_year=study_class.academic_year, subject=subject.subject,
                                                     subject_name=subject.subject_name,
                                                     is_coordination_subject=subject.is_coordination_subject,
                                                     is_enrolled=not subject.is_optional_subject)
                        )

                for catalog in catalogs_per_subject_for_grade:
                    updated_catalogs_per_subject.append(catalog)

        StudentCatalogPerYear.objects.bulk_update(updated_catalogs_per_year, ['study_class'])
        StudentCatalogPerSubject.objects.bulk_update(updated_catalogs_per_subject, ['study_class', 'teacher', 'is_enrolled'])
        StudentCatalogPerSubject.objects.bulk_create(created_catalogs_per_subject)

    def post(self, request, *args, **kwargs):
        student = self.get_student()
        current_study_class = student.student_in_class
        destination_study_class = self.get_study_class()

        # Validate the destination study class
        response = self.validate_destination_study_class(student, current_study_class, destination_study_class)
        if response:
            return response

        with transaction.atomic():
            # Change the student's current class
            student.student_in_class = destination_study_class
            student.save()

            # Move student's data (from previous & current year) to the new class
            self.move_student_data(student, current_study_class, destination_study_class)

            update_last_change_in_catalog(self.request.user.user_profile)

        serializer = self.get_serializer(current_study_class)
        return Response(serializer.data)
