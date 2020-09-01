from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.db.models.functions import Lower
from django.utils.translation import gettext as _
from methodtools import lru_cache
from rest_framework import serializers

from edualert.academic_programs.models import AcademicProgram
from edualert.catalogs.models import StudentCatalogPerYear, StudentCatalogPerSubject
from edualert.catalogs.tasks import create_behavior_grades_task
from edualert.common.fields import PrimaryKeyRelatedField
from edualert.profiles.models import UserProfile
from edualert.schools.constants import BEHAVIOR_GRADE_EXCEPTIONS_PROFILES
from edualert.statistics.tasks import create_students_at_risk_counts_for_study_class_task
from edualert.study_classes.models import StudyClass, TeacherClassThrough
from edualert.study_classes.tasks import import_students_data
from edualert.subjects.models import Subject, ProgramSubjectThrough
from edualert.subjects.serializers import SubjectSerializer, TaughtSubjectSerializer, SimpleProgramSubjectThroughSerializer
from edualert.study_classes.constants import CLASS_GRADE_MAPPING, CATEGORY_LEVELS_CLASS_MAPPING, CLASS_GRADE_REVERSE_MAPPING


class TeacherClassThroughSerializer(serializers.ModelSerializer):
    teacher = serializers.SerializerMethodField()

    class Meta:
        model = TeacherClassThrough
        fields = ('id', 'teacher', 'subject_id', 'subject_name')

    @staticmethod
    def get_teacher(obj):
        from edualert.profiles.serializers import UserProfileBaseSerializer
        return UserProfileBaseSerializer(obj.teacher).data


class TeacherClassThroughCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherClassThrough
        fields = ('teacher', 'subject')


class TeacherClassThroughPartiallyUpdateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=True)

    class Meta:
        model = TeacherClassThrough
        fields = ('id', 'teacher')


class TeacherClassThroughOwnStudyClassSerializer(serializers.ModelSerializer):
    subjects = serializers.SerializerMethodField()

    class Meta:
        model = TeacherClassThrough
        fields = ('id', 'study_class_id', 'class_grade', 'class_letter', 'academic_program_name', 'subjects', 'is_class_master')

    def get_subjects(self, obj):
        subjects = Subject.objects.filter(
            teacher_class_through__teacher=self.context['user_profile'],
            teacher_class_through__academic_year=self.context['academic_year'],
            teacher_class_through__study_class=obj.study_class,
            is_coordination=False
        )
        return SubjectSerializer(instance=subjects, many=True).data


class TeacherClassThroughAssignedStudyClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherClassThrough
        fields = ('id', 'study_class_id', 'class_grade', 'class_letter',
                  'subject_id', 'subject_name', 'is_optional_subject')


class StudyClassNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudyClass
        fields = ('id', 'class_grade', 'class_letter')


class StudyClassBaseSerializer(serializers.ModelSerializer):
    has_previous_catalog_data = serializers.SerializerMethodField()

    class Meta:
        model = StudyClass

    def get_has_previous_catalog_data(self, obj):
        return obj.class_grade_arabic not in (0, 5, 9) and \
               StudyClass.objects.filter(school_unit=self.context['principal_school'], academic_year=obj.academic_year - 1,
                                         class_grade_arabic=obj.class_grade_arabic - 1, class_letter=obj.class_letter).exists()


class StudyClassListSerializer(StudyClassBaseSerializer):
    class Meta(StudyClassBaseSerializer.Meta):
        fields = ('id', 'class_grade', 'class_letter', 'academic_program_name', 'has_previous_catalog_data')


class StudyClassDetailSerializer(StudyClassBaseSerializer):
    class_master = serializers.SerializerMethodField()
    teachers_class_through = serializers.SerializerMethodField()
    students = serializers.SerializerMethodField()

    class Meta(StudyClassBaseSerializer.Meta):
        fields = ('id', 'class_grade', 'class_letter', 'academic_year', 'academic_program', 'academic_program_name',
                  'class_master', 'teachers_class_through', 'students', 'has_previous_catalog_data')

    @staticmethod
    def get_class_master(obj):
        from edualert.profiles.serializers import UserProfileBaseSerializer
        return UserProfileBaseSerializer(obj.class_master).data

    @staticmethod
    def get_teachers_class_through(obj):
        return TeacherClassThroughSerializer(instance=obj.teacher_class_through.exclude(is_coordination_subject=True)
                                             .order_by(Lower('subject_name')).select_related('teacher', 'subject'),
                                             many=True).data

    @staticmethod
    def get_students(obj):
        from edualert.profiles.serializers import UserProfileBaseSerializer

        students = [catalog.student for catalog in obj.student_catalogs_per_year.all().select_related('student').order_by(Lower('student__full_name'))]
        return UserProfileBaseSerializer(instance=students, many=True).data


class StudyClassCreateUpdateSerializer(StudyClassBaseSerializer):
    teachers_class_through = TeacherClassThroughCreateUpdateSerializer(many=True, write_only=True)
    students = PrimaryKeyRelatedField(
        queryset=UserProfile.objects.filter(user_role=UserProfile.UserRoles.STUDENT, is_active=True),
        many=True, write_only=True
    )

    class Meta(StudyClassBaseSerializer.Meta):
        fields = ('id', 'class_grade', 'class_letter', 'academic_year', 'academic_program', 'academic_program_name',
                  'class_master', 'teachers_class_through', 'students', 'has_previous_catalog_data')
        read_only_fields = ('academic_year', 'academic_program_name')
        extra_kwargs = {
            'academic_program': {'write_only': True}
        }

    def validate(self, attrs):
        school_unit = self.context['principal_school']
        academic_year = self.context['academic_year']
        class_grade = attrs['class_grade']
        class_master = attrs['class_master']
        has_previous_catalog_data = self.get_has_previous_catalog_data(self.instance) if self.instance else False

        if class_grade not in CLASS_GRADE_MAPPING or \
                CATEGORY_LEVELS_CLASS_MAPPING[class_grade] not in school_unit.categories.values_list('category_level', flat=True):
            raise serializers.ValidationError({'class_grade': _('Invalid class grade.')})
        if self.instance and class_grade != self.instance.class_grade and has_previous_catalog_data:
            raise serializers.ValidationError({'class_grade': _('Cannot change the class grade for a class that has previous catalog data.')})

        exclude = {'id': self.instance.id} if self.instance else {}
        if StudyClass.objects.filter(school_unit_id=school_unit.id, academic_year=academic_year,
                                     class_grade=class_grade, class_letter=attrs['class_letter']) \
                .exclude(**exclude).exists():
            raise serializers.ValidationError({'general_errors': _('This study class already exists.')})

        if (not self.instance or self.instance.class_master != class_master) \
                and (class_master.user_role != UserProfile.UserRoles.TEACHER or
                     not class_master.is_active or
                     class_master.school_unit_id != school_unit.id or
                     class_master.mastering_study_classes.filter(academic_year=academic_year).exists()):
            raise serializers.ValidationError({'class_master': _('Invalid user.')})

        academic_program = attrs.get('academic_program')
        if academic_program is None:
            raise serializers.ValidationError({'academic_program': _('This field is required.')})
        if academic_program.academic_year != academic_year or academic_program.school_unit_id != school_unit.id or \
                academic_program.generic_academic_program.category.category_level != CATEGORY_LEVELS_CLASS_MAPPING[class_grade]:
            raise serializers.ValidationError({'academic_program': _('Invalid academic program.')})

        if self.instance and academic_program != self.instance.academic_program and has_previous_catalog_data:
            raise serializers.ValidationError({'academic_program': _('Cannot change the academic program for a class that has previous catalog data.')})

        # Validate subjects against the academic program mandatory & optional subjects.
        teachers_class_through = attrs['teachers_class_through']
        program_subjects = set(academic_program.program_subjects_through.filter(class_grade=class_grade).values_list('subject_id', flat=True))
        program_subjects.update(set(academic_program.generic_academic_program.program_subjects_through
                                    .filter(class_grade=class_grade).values_list('subject_id', flat=True)))
        request_subjects = set(teacher_class_through['subject'].id for teacher_class_through in teachers_class_through)
        if program_subjects != request_subjects:
            raise serializers.ValidationError({'teachers_class_through': _('The subjects do not correspond with the academic program subjects.')})

        class_grade_arabic = CLASS_GRADE_MAPPING[class_grade]
        for teacher_class_through in teachers_class_through:
            teacher = teacher_class_through['teacher']
            subject = teacher_class_through['subject']
            if teacher.user_role != UserProfile.UserRoles.TEACHER or not teacher.is_active or teacher.school_unit_id != school_unit.id:
                raise serializers.ValidationError({'teachers_class_through': _('At least one teacher is invalid.')})
            if subject not in teacher.taught_subjects.all() and \
                    ((class_grade_arabic in range(0, 5) and teacher != class_master) or
                     (class_grade_arabic in range(5, 14) and subject not in academic_program.optional_subjects.all())):
                raise serializers.ValidationError({'teachers_class_through': _('Teacher {} does not teach {}.').format(teacher.full_name, subject.name)})

        for student in attrs['students']:
            if student.school_unit_id != school_unit.id or student.student_in_class not in [None, self.instance]:
                raise serializers.ValidationError({'students': _('At least one student is invalid.')})

        attrs['academic_program_name'] = academic_program.name if academic_program else None
        attrs['class_grade_arabic'] = class_grade_arabic
        attrs['teachers_class_through'].append(
            {
                "teacher": class_master,
                "subject": Subject.objects.get(is_coordination=True)
            }
        )
        if not self.instance:
            attrs['school_unit'] = school_unit
            attrs['academic_year'] = academic_year

        return attrs

    def create(self, validated_data):
        teachers_class_through = validated_data.pop('teachers_class_through')
        students = validated_data.pop('students')

        instance = StudyClass.objects.create(**validated_data)

        optional_subjects = self.get_optional_subjects(instance.academic_program, instance)

        # Add class teachers
        self.create_teachers_class_through(instance, teachers_class_through, instance.academic_year, optional_subjects)

        # Add class students
        self.add_students_to_class(instance, students, instance.academic_year, teachers_class_through, optional_subjects)

        create_students_at_risk_counts_for_study_class_task.delay(instance.id)

        return instance

    def update(self, instance, validated_data):
        teachers_class_through = validated_data.pop('teachers_class_through')
        students = validated_data.pop('students')
        academic_program = validated_data.get('academic_program')
        old_academic_program = instance.academic_program

        if academic_program != old_academic_program:
            academic_program.classes_count += 1
            academic_program.save()
            if old_academic_program is not None and old_academic_program.classes_count > 0:
                old_academic_program.classes_count -= 1
                old_academic_program.save()

        instance = super().update(instance, validated_data)

        optional_subjects = self.get_optional_subjects(academic_program, instance)

        # Update teachers
        TeacherClassThrough.objects.filter(study_class=instance).delete()
        self.create_teachers_class_through(instance, teachers_class_through, instance.academic_year, optional_subjects)

        # Update students
        # Remove all students from class, because it's more efficient than updating all teachers for each of them.
        existing_students = UserProfile.objects.filter(user_role=UserProfile.UserRoles.STUDENT, student_in_class=instance)
        StudentCatalogPerYear.objects.filter(student__in=existing_students, study_class=instance).delete()
        StudentCatalogPerSubject.objects.filter(student__in=existing_students, study_class=instance).delete()
        existing_students.update(student_in_class=None)

        # Students that were added to the class
        self.add_students_to_class(instance, students, instance.academic_year, teachers_class_through, optional_subjects)

        return instance

    @staticmethod
    def get_optional_subjects(academic_program, instance):
        return academic_program.program_subjects_through.filter(class_grade=instance.class_grade).values_list('subject_id', flat=True)

    @staticmethod
    def create_teachers_class_through(instance, teachers_class_through, academic_year, optional_subjects):
        teacher_class_through_instances = []
        for teacher_class_through in teachers_class_through:
            subject = teacher_class_through['subject']
            teacher = teacher_class_through['teacher']
            teacher_class_through_instances.append(
                TeacherClassThrough(study_class=instance, teacher=teacher, subject=subject, academic_year=academic_year,
                                    is_class_master=teacher.id == instance.class_master_id,
                                    class_grade=instance.class_grade, class_letter=instance.class_letter,
                                    academic_program_name=instance.academic_program_name,
                                    subject_name=subject.name, is_optional_subject=subject.id in optional_subjects,
                                    is_coordination_subject=subject.is_coordination)
            )
        TeacherClassThrough.objects.bulk_create(teacher_class_through_instances)

    @staticmethod
    def add_students_to_class(instance, students, academic_year, teachers_class_through, optional_subjects):
        catalogs_per_year = []
        catalogs_per_subject = []
        student_ids = []

        for student in students:
            student_ids.append(student.id)
            student.student_in_class = instance
            catalogs_per_year.append(
                StudentCatalogPerYear(student=student, study_class=instance, academic_year=academic_year)
            )
            for teacher_class_through in teachers_class_through:
                subject = teacher_class_through['subject']
                catalogs_per_subject.append(
                    StudentCatalogPerSubject(student=student, teacher=teacher_class_through['teacher'],
                                             study_class=instance, academic_year=academic_year,
                                             subject=subject, subject_name=subject.name,
                                             is_coordination_subject=subject.is_coordination,
                                             is_enrolled=subject.id not in optional_subjects)
                )

        UserProfile.objects.bulk_update(students, ['student_in_class'])
        StudentCatalogPerYear.objects.bulk_create(catalogs_per_year)
        StudentCatalogPerSubject.objects.bulk_create(catalogs_per_subject)

        create_behavior_grades_task.delay(student_ids)

    def to_representation(self, instance):
        return StudyClassDetailSerializer(instance, context=self.context).data


class StudyClassPartiallyUpdateSerializer(StudyClassBaseSerializer):
    updated_teachers = TeacherClassThroughPartiallyUpdateSerializer(many=True, required=False)
    new_students = PrimaryKeyRelatedField(
        queryset=UserProfile.objects.filter(user_role=UserProfile.UserRoles.STUDENT, is_active=True),
        many=True
    )
    deleted_students = PrimaryKeyRelatedField(
        queryset=UserProfile.objects.filter(user_role=UserProfile.UserRoles.STUDENT, is_active=True),
        many=True
    )

    class Meta(StudyClassBaseSerializer.Meta):
        fields = ('class_master', 'updated_teachers', 'new_students', 'deleted_students')

    def validate(self, attrs):
        school_unit = self.context['principal_school']
        new_class_master = attrs.get('class_master')
        updated_teachers = attrs.get('updated_teachers', [])
        new_students = attrs.get('new_students', [])
        deleted_students = attrs.get('deleted_students', [])
        old_class_master = self.instance.class_master

        if new_class_master and new_class_master != old_class_master and \
                (new_class_master.user_role != UserProfile.UserRoles.TEACHER or
                 not new_class_master.is_active or
                 new_class_master.school_unit_id != school_unit.id or
                 new_class_master.mastering_study_classes.filter(academic_year=self.instance.academic_year).exists()):
            raise serializers.ValidationError({'class_master': _('Invalid user.')})

        for teacher_class_through in updated_teachers:
            teacher = teacher_class_through['teacher']
            instance_id = teacher_class_through['id']
            if teacher.user_role != UserProfile.UserRoles.TEACHER or not teacher.is_active or teacher.school_unit_id != school_unit.id:
                raise serializers.ValidationError({'updated_teachers': _('At least one teacher is invalid.')})

            try:
                teacher_class_through_instance = TeacherClassThrough.objects.get(id=instance_id, study_class_id=self.instance.id)
            except ObjectDoesNotExist:
                raise serializers.ValidationError({'updated_teachers': _(f'Invalid pk "{instance_id}" - object does not exist.')})

            subject = teacher_class_through_instance.subject
            if subject.is_coordination:
                raise serializers.ValidationError({'updated_teachers': _(f'Invalid pk "{instance_id}" - object does not exist.')})

            class_master = new_class_master or old_class_master
            if not teacher_class_through_instance.is_optional_subject and subject not in teacher.taught_subjects.all() \
                    and (self.instance.class_grade_arabic in range(5, 14) or (self.instance.class_grade_arabic in range(0, 5) and teacher != class_master)):
                raise serializers.ValidationError({'updated_teachers': _('Teacher {} does not teach {}.').format(teacher.full_name, subject.name)})

            teacher_class_through['instance'] = teacher_class_through_instance

        for student in new_students:
            if student.school_unit_id != school_unit.id or student.student_in_class:
                raise serializers.ValidationError({'new_students': _('At least one student is invalid.')})

        for student in deleted_students:
            if student.student_in_class != self.instance:
                raise serializers.ValidationError({'deleted_students': _('At least one student is invalid.')})

        return attrs

    def update(self, instance, validated_data):
        new_class_master = validated_data.get('class_master')
        updated_teachers = validated_data.get('updated_teachers', [])
        new_students = validated_data.get('new_students', [])
        deleted_students = validated_data.get('deleted_students', [])
        actual_class_master = instance.class_master

        # Update teachers
        instances_to_update = []
        for teacher_class_through in updated_teachers:
            teacher_class_through_instance = teacher_class_through['instance']
            teacher = teacher_class_through['teacher']

            teacher_class_through_instance.teacher = teacher
            teacher_class_through_instance.is_class_master = teacher == actual_class_master
            instances_to_update.append(teacher_class_through_instance)

            # Also update catalogs for all students in this class for this subject
            StudentCatalogPerSubject.objects.filter(study_class_id=instance.id,
                                                    subject_id=teacher_class_through_instance.subject_id) \
                .update(teacher=teacher)
        TeacherClassThrough.objects.bulk_update(instances_to_update, ['teacher', 'is_class_master'])

        # Update class master
        if new_class_master:
            TeacherClassThrough.objects.filter(study_class_id=instance.id, teacher=actual_class_master) \
                .update(is_class_master=False)

            instance.class_master = new_class_master
            instance.save()
            TeacherClassThrough.objects.filter(study_class_id=instance.id, is_coordination_subject=True) \
                .update(teacher=new_class_master)
            TeacherClassThrough.objects.filter(study_class_id=instance.id, teacher=new_class_master) \
                .update(is_class_master=True)
            StudentCatalogPerSubject.objects.filter(study_class_id=instance.id, is_coordination_subject=True) \
                .update(teacher=new_class_master)

        # Add students
        if new_students:
            self.add_students_to_class(instance, new_students)

        # Delete students
        if deleted_students:
            StudentCatalogPerYear.objects.filter(student__in=deleted_students, study_class=instance).delete()
            StudentCatalogPerSubject.objects.filter(student__in=deleted_students, study_class=instance).delete()
            deleted_students.update(student_in_class=None)

        return instance

    @staticmethod
    def add_students_to_class(instance, students):
        optional_subjects = StudyClassCreateUpdateSerializer.get_optional_subjects(instance.academic_program, instance)
        teachers_class_through = instance.teacher_class_through.all()

        catalogs_per_year = []
        catalogs_per_subject = []
        student_ids = []

        for student in students:
            student_ids.append(student.id)
            student.student_in_class = instance
            catalogs_per_year.append(
                StudentCatalogPerYear(student=student, study_class=instance, academic_year=instance.academic_year)
            )
            for teacher_class_through in teachers_class_through:
                subject = teacher_class_through.subject
                catalogs_per_subject.append(
                    StudentCatalogPerSubject(student=student, teacher=teacher_class_through.teacher,
                                             study_class=instance, academic_year=instance.academic_year,
                                             subject=subject, subject_name=subject.name,
                                             is_coordination_subject=subject.is_coordination,
                                             is_enrolled=subject.id not in optional_subjects)
                )

        UserProfile.objects.bulk_update(students, ['student_in_class'])
        StudentCatalogPerYear.objects.bulk_create(catalogs_per_year)
        StudentCatalogPerSubject.objects.bulk_create(catalogs_per_subject)

        create_behavior_grades_task.delay(student_ids)
        import_students_data.delay(student_ids, instance.class_grade_arabic)

    def to_representation(self, instance):
        return StudyClassDetailSerializer(instance, context=self.context).data


class StudyClassClonedToNextYearSerializer(serializers.ModelSerializer):
    class_grade = serializers.SerializerMethodField()
    academic_program = serializers.SerializerMethodField()
    class_master = serializers.SerializerMethodField()
    subjects = serializers.SerializerMethodField()
    students = serializers.SerializerMethodField()

    class Meta:
        model = StudyClass
        fields = ('class_grade', 'class_letter', 'academic_program', 'academic_program_name', 'class_master', 'subjects', 'students')

    @staticmethod
    def get_class_grade(obj):
        return CLASS_GRADE_REVERSE_MAPPING[obj.class_grade_arabic + 1]

    @lru_cache(maxsize=None)
    def retrieve_academic_program(self, obj):
        return AcademicProgram.objects.filter(name=obj.academic_program_name, academic_year=obj.academic_year + 1, school_unit_id=obj.school_unit_id).first()

    def get_academic_program(self, obj):
        academic_program = self.retrieve_academic_program(obj)
        return academic_program.id if academic_program else None

    @staticmethod
    def get_class_master(obj):
        from edualert.profiles.serializers import UserProfileBaseSerializer
        return UserProfileBaseSerializer(obj.class_master).data

    def get_subjects(self, obj):
        academic_program = self.retrieve_academic_program(obj)
        if not academic_program:
            return []

        subjects = ProgramSubjectThrough.objects.filter(
            Q(academic_program_id=academic_program.id) | Q(generic_academic_program_id=academic_program.generic_academic_program_id),
            class_grade=CLASS_GRADE_REVERSE_MAPPING[obj.class_grade_arabic + 1]
        ).order_by(Lower('subject_name'))
        return SimpleProgramSubjectThroughSerializer(instance=subjects, many=True).data

    @staticmethod
    def get_students(obj):
        from edualert.profiles.serializers import UserProfileBaseSerializer

        academic_profile = obj.school_unit.academic_profile
        behavior_grade_limit = 8 if academic_profile and academic_profile.name in BEHAVIOR_GRADE_EXCEPTIONS_PROFILES else 6
        subjects_ids = [obj.academic_program.core_subject_id] if obj.academic_program.core_subject else []

        students = []
        for catalog in obj.student_catalogs_per_year.all().order_by(Lower('student__full_name')):
            if catalog.behavior_grade_annual < behavior_grade_limit:
                continue
            student = catalog.student
            if student.student_catalogs_per_subject.filter(Q(avg_final__isnull=True) | Q(avg_final__lt=5) | Q(avg_final__lt=6, subject__id__in=subjects_ids),
                                                           study_class_id=obj.id).count() > 0:
                continue
            students.append(student)

        return UserProfileBaseSerializer(instance=students, many=True).data


class OwnStudyClassSerializer(serializers.ModelSerializer):
    class_master = serializers.SerializerMethodField()
    taught_subjects = serializers.SerializerMethodField()
    is_class_master = serializers.SerializerMethodField()

    class Meta:
        model = StudyClass
        fields = ('id', 'class_grade', 'class_letter', 'academic_year', 'academic_program_name',
                  'class_master', 'taught_subjects', 'is_class_master')

    @staticmethod
    def get_class_master(obj):
        from edualert.profiles.serializers import UserProfileBaseSerializer
        return UserProfileBaseSerializer(obj.class_master).data

    def get_taught_subjects(self, obj):
        current_teacher = self.context['request'].user.user_profile
        subject_ids = obj.teacher_class_through.filter(teacher=current_teacher).values_list('subject', flat=True)
        subjects = TaughtSubjectSerializer(
            instance=Subject.objects.filter(id__in=subject_ids).order_by('-is_coordination', Lower('name')),
            many=True
        ).data

        optional_subjects_ids = obj.teacher_class_through.filter(teacher=current_teacher, is_optional_subject=True) \
            .values_list('subject', flat=True)

        for subject in subjects:
            subject['is_optional'] = subject['id'] in optional_subjects_ids

        return subjects

    def get_is_class_master(self, obj):
        return obj.class_master_id == self.context['request'].user.user_profile.id
