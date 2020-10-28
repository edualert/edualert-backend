from unittest.mock import call, patch

from ddt import data, unpack, ddt
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from edualert.academic_calendars.factories import AcademicYearCalendarFactory
from edualert.catalogs.factories import SubjectGradeFactory, SubjectAbsenceFactory, ExaminationGradeFactory, \
    StudentCatalogPerSubjectFactory, StudentCatalogPerYearFactory
from edualert.common.api_tests import CommonAPITestCase
from edualert.common.utils import date
from edualert.profiles.constants import EXPELLED_LABEL, HELD_BACK_LABEL, EXPELLED_TITLE, EXPELLED_BODY, HELD_BACK_TITLE, HELD_BACK_BODY
from edualert.profiles.factories import UserProfileFactory, LabelFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.study_classes.factories import TeacherClassThroughFactory, StudyClassFactory
from edualert.subjects.factories import SubjectFactory


@ddt
class UserProfileUpdateTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        AcademicYearCalendarFactory()

        cls.admin = UserProfileFactory(user_role=UserProfile.UserRoles.ADMINISTRATOR)
        cls.principal = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL)
        cls.school_unit = RegisteredSchoolUnitFactory(school_principal=cls.principal)

        cls.admin_profile = UserProfileFactory(user_role=UserProfile.UserRoles.ADMINISTRATOR)
        cls.principal_profile = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL, school_unit=cls.school_unit)
        cls.teacher_profile = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=cls.school_unit,
                                                 email='teacher@email.com', username='{}_{}'.format(cls.school_unit.id, 'teacher@email.com'))
        cls.student_profile = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=cls.school_unit,
                                                 email='student@email.com', username='{}_{}'.format(cls.school_unit.id, 'student@email.com'))
        cls.parent_profile = UserProfileFactory(user_role=UserProfile.UserRoles.PARENT, school_unit=cls.school_unit,
                                                email='parent@email.com', username='{}_{}'.format(cls.school_unit.id, 'parent@email.com'))

    def setUp(self):
        self.data = {
            'full_name': 'John Doe',
            'email': 'john@gmail.com',
            'use_phone_as_username': False,
            'user_role': UserProfile.UserRoles.ADMINISTRATOR
        }

        self.principal_data = {
            **self.data,
            'labels': [],
            'user_role': UserProfile.UserRoles.PRINCIPAL
        }
        self.teacher_data = {
            **self.data,
            'labels': [],
            'taught_subjects': [],
            'user_role': UserProfile.UserRoles.TEACHER
        }
        self.parent_data = {
            **self.data,
            'labels': [],
            'user_role': UserProfile.UserRoles.PARENT
        }
        self.student_data = {
            **self.data,
            'labels': [],
            'parents': [],
            'user_role': UserProfile.UserRoles.STUDENT
        }

    @staticmethod
    def build_url(profile_id):
        return reverse('users:user-profile-detail', kwargs={'id': profile_id})

    def test_user_profile_update_unauthenticated(self):
        response = self.client.put(self.build_url(self.admin_profile.id), self.data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.TEACHER,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_user_profile_update_wrong_user_type(self, user_role):
        profile = UserProfileFactory(user_role=user_role, school_unit=self.school_unit)
        self.client.login(username=profile.username, password='passwd')

        response = self.client.put(self.build_url(self.admin_profile.id), self.data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @data(
        [UserProfile.UserRoles.ADMINISTRATOR, [UserProfile.UserRoles.STUDENT, UserProfile.UserRoles.TEACHER, UserProfile.UserRoles.PARENT]],
        [UserProfile.UserRoles.PRINCIPAL, [UserProfile.UserRoles.ADMINISTRATOR, UserProfile.UserRoles.PRINCIPAL]]
    )
    @unpack
    def test_user_profile_update_forbidden_user_role(self, user_role, forbidden_roles):
        self.client.login(username=UserProfile.objects.filter(user_role=user_role).first().username, password='passwd')
        for forbidden_role in forbidden_roles:
            profile = UserProfileFactory(user_role=forbidden_role)
            if forbidden_role != UserProfile.UserRoles.ADMINISTRATOR:
                profile.school_unit = self.school_unit
                profile.save()
            self.data['user_role'] = forbidden_role
            response = self.client.put(self.build_url(profile.id), self.data)
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @data(
        ('data', UserProfile.UserRoles.ADMINISTRATOR, []),
        ('principal_data', UserProfile.UserRoles.PRINCIPAL, ['labels', 'school_unit']),
        ('teacher_data', UserProfile.UserRoles.TEACHER, ['labels', 'taught_subjects', 'assigned_study_classes']),
        ('parent_data', UserProfile.UserRoles.PARENT, ['labels', 'address']),
        ('student_data', UserProfile.UserRoles.STUDENT, [
            'student_in_class', 'labels', 'risk_description', 'address', 'personal_id_number', 'birth_date',
            'parents', 'educator_full_name', 'educator_email', 'educator_phone_number'
        ])
    )
    @unpack
    def test_user_profile_update_expected_response_fields(self, data_dict, user_role, expected_fields):
        if user_role in [UserProfile.UserRoles.ADMINISTRATOR, UserProfile.UserRoles.PRINCIPAL]:
            self.client.login(username=self.admin.username, password='passwd')
        else:
            self.client.login(username=self.principal.username, password='passwd')

        profile = UserProfileFactory(
            user_role=user_role,
            school_unit=self.school_unit if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )
        data_dict = getattr(self, data_dict)
        data_dict['user_role'] = user_role

        response = self.client.put(self.build_url(profile.id), data_dict)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        common_fields = ['id', 'full_name', 'user_role', 'email', 'phone_number', 'use_phone_as_username', 'is_active', 'last_online']
        self.assertCountEqual(response.data.keys(), expected_fields + common_fields)

    @data(
        (UserProfile.UserRoles.ADMINISTRATOR, 'data', ['full_name', 'email', 'user_role', 'use_phone_as_username']),
        (UserProfile.UserRoles.PRINCIPAL, 'principal_data', ['full_name', 'labels', 'email', 'user_role', 'use_phone_as_username']),
        (UserProfile.UserRoles.TEACHER, 'teacher_data', ['full_name', 'labels', 'taught_subjects', 'email', 'user_role', 'use_phone_as_username']),
        (UserProfile.UserRoles.PARENT, 'parent_data', ['full_name', 'email', 'user_role', 'labels', 'use_phone_as_username']),
        (UserProfile.UserRoles.STUDENT, 'student_data', ['full_name', 'email', 'labels', 'parents', 'user_role', 'use_phone_as_username']),
    )
    @unpack
    def test_user_profile_update_missing_fields(self, user_role, data_dict, required_fields):
        if user_role in [UserProfile.UserRoles.ADMINISTRATOR, UserProfile.UserRoles.PRINCIPAL]:
            self.client.login(username=self.admin.username, password='passwd')
        else:
            self.client.login(username=self.principal.username, password='passwd')

        profile = UserProfileFactory(
            user_role=user_role,
            school_unit=self.school_unit if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )

        data_dict = getattr(self, data_dict)
        data_dict['user_role'] = user_role
        url = self.build_url(profile.id)

        for field in required_fields:
            data_to_send = {
                required_field: data_dict[required_field]
                for required_field in required_fields if required_field != field
            }
            response = self.client.put(url, data_to_send)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data, {field: ['This field is required.']})

        data_dict['password'] = None
        response = self.client.put(url, data_dict)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'password': ['This field may not be null.']})
        del data_dict['password']

        data_dict['use_phone_as_username'] = True
        response = self.client.put(url, data_dict)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'phone_number': ['This field is required.']})

        data_dict['use_phone_as_username'] = False
        del data_dict['email']
        response = self.client.put(url, data_dict)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'email': ['This field is required.']})

    def test_user_profile_update_invalid_role_transitions(self):
        # valid transitions
        valid_transitions = {
            UserProfile.UserRoles.ADMINISTRATOR: [UserProfile.UserRoles.PRINCIPAL, ],
            UserProfile.UserRoles.PRINCIPAL: [UserProfile.UserRoles.ADMINISTRATOR, ],
            UserProfile.UserRoles.TEACHER: [UserProfile.UserRoles.PARENT, UserProfile.UserRoles.STUDENT],
            UserProfile.UserRoles.PARENT: [UserProfile.UserRoles.TEACHER, UserProfile.UserRoles.STUDENT],
            UserProfile.UserRoles.STUDENT: [UserProfile.UserRoles.TEACHER, UserProfile.UserRoles.PARENT],
        }

        for role in UserProfile.UserRoles:
            if role in [UserProfile.UserRoles.PRINCIPAL, UserProfile.UserRoles.ADMINISTRATOR]:
                self.client.login(username=self.admin.username, password='passwd')
            else:
                self.client.login(username=self.principal.username, password='passwd')
            profile = UserProfile.objects.filter(user_role=role).first()

            for other_role in UserProfile.UserRoles:
                if role != other_role and other_role not in valid_transitions.get(role, []):
                    self.principal_data['user_role'] = other_role
                    response = self.client.put(self.build_url(profile.id), self.principal_data)
                    self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                    self.assertEqual(response.data, {'user_role': ['Invalid role transition.']})

    def test_user_profile_update_role_not_allowed(self):
        student1 = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, last_online=timezone.now(), school_unit=self.school_unit)
        student2 = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=self.school_unit)
        SubjectGradeFactory(student=student2)
        student3 = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=self.school_unit)
        SubjectAbsenceFactory(student=student3)
        student4 = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=self.school_unit)
        ExaminationGradeFactory(student=student4)

        self.client.login(username=self.principal.username, password='passwd')
        self.student_data['user_role'] = UserProfile.UserRoles.PARENT

        for student in [student1, student2, student3, student4]:
            response = self.client.put(self.build_url(student.id), self.student_data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data['user_role'], ['Cannot change user role.'])

    @data(
        (UserProfile.UserRoles.ADMINISTRATOR, 'data'),
        (UserProfile.UserRoles.PRINCIPAL, 'principal_data')
    )
    @unpack
    def test_user_profile_update_own_profile(self, user_role, data_dict):
        profile = UserProfile.objects.filter(user_role=user_role).first()
        self.client.login(username=profile.username, password='passwd')

        data_dict = getattr(self, data_dict)
        response = self.client.put(self.build_url(profile.id), data_dict)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @data(
        (UserProfile.UserRoles.PRINCIPAL, 'principal_data'),
        (UserProfile.UserRoles.TEACHER, 'teacher_data'),
        (UserProfile.UserRoles.PARENT, 'parent_data'),
        (UserProfile.UserRoles.STUDENT, 'student_data'),
    )
    @unpack
    def test_user_profile_update_label_validations(self, user_role, data_dict):
        if user_role == UserProfile.UserRoles.PRINCIPAL:
            self.client.login(username=self.admin.username, password='passwd')
        else:
            self.client.login(username=self.principal.username, password='passwd')

        url = self.build_url(UserProfile.objects.filter(user_role=user_role).first().id)

        # Label doesn't exist
        data_dict = getattr(self, data_dict)
        data_dict['user_role'] = user_role
        data_dict['labels'] = [0]
        response = self.client.put(url, data_dict)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'labels': ['Invalid pk "0" - object does not exist.']})

        # Label with the wrong user_role
        label = LabelFactory(user_role=UserProfile.UserRoles.PARENT if user_role != UserProfile.UserRoles.PARENT else UserProfile.UserRoles.STUDENT)
        data_dict['labels'] = [label.id, ]

        response = self.client.put(url, data_dict)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'labels': ['Labels do not correspond to the created user role.']})

    def test_user_profile_update_student_validations(self):
        self.client.login(username=self.principal.username, password='passwd')
        student = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=self.school_unit)
        url = self.build_url(student.id)

        self.student_data['educator_full_name'] = 'Educator'
        response = self.client.put(url, self.student_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, ({'educator_full_name': [
            'Either email or phone number is required for the educator.'
        ]}))

        self.student_data['educator_email'] = 'edu@edu.com'
        response = self.client.put(url, self.student_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Invalid personal_id_number
        del self.student_data['educator_full_name']
        del self.student_data['educator_email']
        for bad_data in ['32840', '249124395385039850', '123456789123a']:
            self.student_data['personal_id_number'] = bad_data
            response = self.client.put(url, self.student_data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data, {'personal_id_number': ['Invalid format. Must be 13 digits, no spaces allowed.']})

        # Birth date must be in the past
        next_year = timezone.now().year + 1
        del self.student_data['personal_id_number']
        self.student_data['birth_date'] = date(next_year, 1, 1)

        response = self.client.put(url, self.student_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'birth_date': ['Birth date must be in the past.']})

    def test_user_profile_update_student_parent_validations(self):
        self.client.login(username=self.principal.username, password='passwd')
        url = self.build_url(self.student_profile.id)

        # Parents don't exist
        self.student_data['parents'] = [0]
        response = self.client.put(url, self.student_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'parents': ['Invalid pk "0" - object does not exist.']})

        # Parents don't belong to the same school
        other_school = RegisteredSchoolUnitFactory()
        parent = UserProfileFactory(user_role=UserProfile.UserRoles.PARENT, school_unit=other_school)
        self.student_data['parents'] = [parent.id]

        response = self.client.put(url, self.student_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'parents': ["Parents must belong to the user's school unit."]})

        # Parents don't have a school
        parent.school_unit = None
        parent.save()
        response = self.client.put(url, self.student_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'parents': ["Parents must belong to the user's school unit."]})

    @data(
        'a' * 5,
        'a' * 129,
        'abcdefg h'
    )
    def test_user_profile_update_validate_password(self, password):
        self.client.login(username=self.admin.username, password='passwd')

        self.principal_data['password'] = password
        response = self.client.put(self.build_url(self.principal.id), self.principal_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['password'], ['Invalid format. Must be minimum 6, maximum 128 characters, no spaces allowed.'])

    def test_user_profile_update_username_not_unique(self):
        self.client.login(username=self.admin.username, password='passwd')

        self.data['email'] = self.admin.email
        response = self.client.put(self.build_url(self.admin_profile.id), self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['username'], ['This username is already associated with another account.'])

        self.client.logout()
        self.client.login(username=self.principal.username, password='passwd')

        self.teacher_profile.refresh_from_db()
        self.student_data['email'] = self.teacher_profile.email
        response = self.client.put(self.build_url(self.student_profile.id), self.student_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['username'], ['This username is already associated with another account.'])

    @data(
        '+9049', '2328492489f898', '2224', '123456789'
    )
    def test_user_profile_update_phone_number_validations(self, phone_number):
        self.client.login(username=self.principal.username, password='passwd')
        self.principal_data['phone_number'] = phone_number
        response = self.client.put(self.build_url(self.teacher_profile.id), self.principal_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'phone_number': ['Invalid format. Must be minimum 10, maximum 20 digits or +.']})

        self.student_data['educator_phone_number'] = phone_number
        response = self.client.put(self.build_url(self.student_profile.id), self.student_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'educator_phone_number': ['Invalid format. Must be minimum 10, maximum 20 digits or +.']})

    def test_user_profile_update_new_teachers_validations(self):
        self.client.login(username=self.principal.username, password='passwd')
        url = self.build_url(self.teacher_profile.id)

        subject1 = SubjectFactory()
        subject2 = SubjectFactory()
        self.teacher_profile.taught_subjects.add(subject1, subject2)

        study_class = StudyClassFactory(school_unit=self.school_unit)
        teacher_class_through1 = TeacherClassThroughFactory(study_class=study_class, teacher=self.teacher_profile, subject=subject1)

        # Incompatible field
        for taught_subjects in [[subject1.id, subject2.id], [subject1.id]]:
            self.teacher_data['taught_subjects'] = taught_subjects
            self.teacher_data['new_teachers'] = [
                {
                    "id": teacher_class_through1.id,
                    "teacher": self.teacher_profile.id,
                }
            ]
            response = self.client.put(url, self.teacher_data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data['new_teachers'], ['This field is incompatible with the request data.'])

        teacher_class_through2 = TeacherClassThroughFactory(study_class=study_class, teacher=self.teacher_profile, subject=subject2)
        new_teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=self.school_unit)

        # Missing the required teacher
        response = self.client.put(url, self.teacher_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['new_teachers'], ['There must be provided teachers for all classes for this subject.'])

        # Duplicated teachers
        self.teacher_data['new_teachers'] = [
            {
                "id": teacher_class_through2.id,
                "teacher": new_teacher.id,
            },
            {
                "id": teacher_class_through2.id,
                "teacher": new_teacher.id,
            }
        ]
        response = self.client.put(url, self.teacher_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['new_teachers'], ['No duplicates allowed.'])

        # Invalid teachers
        inactive_teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=self.school_unit, is_active=False)
        no_school_teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER)

        for profile in [self.principal, inactive_teacher, no_school_teacher]:
            self.teacher_data['new_teachers'] = [
                {
                    "id": teacher_class_through2.id,
                    "teacher": profile.id,
                }
            ]
            response = self.client.put(url, self.teacher_data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data['new_teachers'], ['At least one teacher is invalid.'])

        # Teacher does not teach the subject
        self.teacher_data['new_teachers'] = [
            {
                "id": teacher_class_through2.id,
                "teacher": new_teacher.id,
            }
        ]
        response = self.client.put(url, self.teacher_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['new_teachers'], ['Teacher {} does not teach {}.'.format(new_teacher.full_name, subject2.name)])

        study_class.class_grade = 'IV'
        study_class.class_grade_arabic = 4
        study_class.save()

        response = self.client.put(url, self.teacher_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['new_teachers'], ['Teacher {} does not teach {}.'.format(new_teacher.full_name, subject2.name)])

    @patch('edualert.profiles.tasks.format_and_send_notification_task')
    def test_user_profile_update_labels_success(self, send_notification_mock):
        self.client.login(username=self.principal.username, password='passwd')

        profile = UserProfile.objects.filter(user_role=UserProfile.UserRoles.STUDENT).last()
        url = self.build_url(profile.id)

        # Create a few labels
        label1 = LabelFactory(user_role=UserProfile.UserRoles.STUDENT, text=EXPELLED_LABEL)
        label2 = LabelFactory(user_role=UserProfile.UserRoles.STUDENT, text=HELD_BACK_LABEL)

        self.student_data['labels'] = [label1.id, label2.id]
        response = self.client.put(url, self.student_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        profile.refresh_from_db()
        self.assertCountEqual(profile.labels.values_list('id', flat=True), [label1.id, label2.id])

        # Remove one of them
        self.student_data['labels'] = [label1.id]
        response = self.client.put(url, self.student_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        profile.refresh_from_db()
        self.assertCountEqual(profile.labels.values_list('id', flat=True), [label1.id])

        self.assertEqual(send_notification_mock.call_count, 2)
        calls = [call(EXPELLED_TITLE.format(profile.full_name),
                      EXPELLED_BODY.format(profile.full_name),
                      [self.principal.id], False),
                 call(HELD_BACK_TITLE.format(profile.full_name),
                      HELD_BACK_BODY.format(profile.full_name),
                      [self.principal.id], False)]
        send_notification_mock.assert_has_calls(calls, any_order=True)

    def test_user_profile_update_taught_subjects(self):
        self.client.login(username=self.principal.username, password='passwd')
        url = self.build_url(self.teacher_profile.id)

        # Create a few taught subjects
        subject1 = SubjectFactory(name='Sport')
        subject2 = SubjectFactory(name='Religie')

        self.teacher_data['user_role'] = UserProfile.UserRoles.TEACHER
        self.teacher_data['taught_subjects'] = [subject1.id, subject2.id]

        response = self.client.put(url, self.teacher_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.teacher_profile.refresh_from_db()
        for attr_name, value in self.teacher_data.items():
            if attr_name not in ['labels', 'taught_subjects']:
                self.assertEqual(getattr(self.teacher_profile, attr_name), value)

        self.assertCountEqual(self.teacher_profile.taught_subjects.values_list('id', flat=True), [subject1.id, subject2.id])

        study_class1 = StudyClassFactory(school_unit=self.school_unit, class_grade='I', class_grade_arabic=1)
        teacher_class_through1 = TeacherClassThroughFactory(study_class=study_class1, teacher=self.teacher_profile,
                                                            subject=subject1, is_class_master=False)

        study_class2 = StudyClassFactory(school_unit=self.school_unit, class_master=self.teacher_profile)
        teacher_class_through2 = TeacherClassThroughFactory(study_class=study_class2, teacher=self.teacher_profile,
                                                            subject=subject2, is_class_master=True)
        self.student_profile.student_in_class = study_class2
        self.student_profile.save()
        StudentCatalogPerYearFactory(student=self.student_profile, study_class=study_class2)
        catalog = StudentCatalogPerSubjectFactory(student=self.student_profile, teacher=self.teacher_profile,
                                                  study_class=study_class2, subject=subject2)

        new_teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=self.school_unit)
        new_teacher.taught_subjects.add(subject2)

        self.teacher_data['taught_subjects'] = [subject1.id]
        self.teacher_data['new_teachers'] = [
            {
                'id': teacher_class_through2.id,
                'teacher': new_teacher.id
            }
        ]

        response = self.client.put(url, self.teacher_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.refresh_objects_from_db([teacher_class_through2, catalog])

        self.assertEqual(teacher_class_through2.teacher, new_teacher)
        self.assertFalse(teacher_class_through2.is_class_master)
        self.assertEqual(catalog.teacher, new_teacher)

        self.teacher_data['taught_subjects'] = []
        self.teacher_data['new_teachers'] = [
            {
                'id': teacher_class_through1.id,
                'teacher': study_class1.class_master.id
            }
        ]

        response = self.client.put(url, self.teacher_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        teacher_class_through1.refresh_from_db()

        self.assertEqual(teacher_class_through1.teacher, study_class1.class_master)
        self.assertTrue(teacher_class_through1.is_class_master)

    def test_user_profile_update_password_success(self):
        self.client.login(username=self.admin.username, password='passwd')

        profile = UserProfileFactory(user_role=UserProfile.UserRoles.ADMINISTRATOR)
        self.data['password'] = 'password'
        response = self.client.put(self.build_url(profile.id), self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        profile.user.refresh_from_db()
        self.assertTrue(profile.user.check_password('password'))

    def test_user_profile_update_username_success(self):
        self.client.login(username=self.admin.username, password='passwd')

        # use_phone_as_username is true
        self.data['use_phone_as_username'] = True
        self.data['phone_number'] = '+40700100200'
        response = self.client.put(self.build_url(self.admin_profile.id), self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.admin_profile.refresh_from_db()
        self.assertEqual(self.admin_profile.username, self.data['phone_number'])
        self.assertEqual(self.admin_profile.user.username, self.data['phone_number'])
        self.assertEqual(self.admin_profile.phone_number, self.data['phone_number'])

        # use_phone_as_username is false
        self.data['use_phone_as_username'] = False
        response = self.client.put(self.build_url(self.admin_profile.id), self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.admin_profile.refresh_from_db()
        self.assertEqual(self.admin_profile.username, self.data['email'])
        self.assertEqual(self.admin_profile.user.username, self.data['email'])
        self.assertEqual(self.admin_profile.email, self.data['email'])

        self.client.logout()
        self.client.login(username=self.principal.username, password='passwd')
        response = self.client.put(self.build_url(self.student_profile.id), self.student_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.student_profile.refresh_from_db()
        self.assertEqual(self.student_profile.username, '{}_{}'.format(self.school_unit.id, self.data['email']))
        self.assertEqual(self.student_profile.user.username, '{}_{}'.format(self.school_unit.id, self.data['email']))
