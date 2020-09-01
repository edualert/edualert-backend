from ddt import data, ddt, unpack
from django.urls import reverse
from rest_framework import status

from edualert.academic_calendars.factories import AcademicYearCalendarFactory
from edualert.catalogs.factories import StudentCatalogPerSubjectFactory
from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.study_classes.factories import StudyClassFactory, TeacherClassThroughFactory
from edualert.subjects.factories import SubjectFactory


@ddt
class UserProfileDeactivateTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        AcademicYearCalendarFactory()
        cls.admin = UserProfileFactory(user_role=UserProfile.UserRoles.ADMINISTRATOR)
        cls.principal = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL)
        cls.school_unit = RegisteredSchoolUnitFactory(school_principal=cls.principal)

    @staticmethod
    def build_url(profile_id):
        return reverse('users:user-profile-deactivate', kwargs={'id': profile_id})

    def test_deactivate_user_unauthenticated(self):
        response = self.client.post(self.build_url(self.admin.id), data={})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.TEACHER,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_deactivate_user_wrong_user_type(self, user_role):
        profile = UserProfileFactory(user_role=user_role, school_unit=self.school_unit)
        self.client.login(username=profile.username, password='passwd')

        response = self.client.post(self.build_url(self.principal.id), data={})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @data(
        'admin', 'principal'
    )
    def test_deactivate_user_not_found(self, profile):
        self.client.login(username=getattr(self, profile).username, password='passwd')

        response = self.client.post(self.build_url(0), data={})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @unpack
    @data(
        ('admin', UserProfile.UserRoles.TEACHER),
        ('admin', UserProfile.UserRoles.STUDENT),
        ('admin', UserProfile.UserRoles.PARENT),
        ('principal', UserProfile.UserRoles.ADMINISTRATOR),
        ('principal', UserProfile.UserRoles.PRINCIPAL),
    )
    def test_deactivate_user_wrong_requested_user_type(self, login_user, user_role):
        self.client.login(username=getattr(self, login_user).username, password='passwd')
        profile = UserProfileFactory(user_role=user_role)

        response = self.client.post(self.build_url(profile.id), data={})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_deactivate_user_already_inactive(self):
        self.client.login(username=self.admin.username, password='passwd')
        self.principal.is_active = False
        self.principal.save()
        self.principal.user.is_active = False
        self.principal.user.save()

        response = self.client.post(self.build_url(self.principal.id), data={})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], 'This user is already inactive.')

    def test_deactivate_principal_missing_required_data(self):
        self.client.login(username=self.admin.username, password='passwd')

        principal = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL)
        RegisteredSchoolUnitFactory(school_principal=principal)

        response = self.client.post(self.build_url(principal.id), data={})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['new_school_principal'], ['This field is required.'])

    def test_deactivate_principal_invalid_id(self):
        self.client.login(username=self.admin.username, password='passwd')

        principal = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL)
        RegisteredSchoolUnitFactory(school_principal=principal)

        profile1 = UserProfileFactory(user_role=UserProfile.UserRoles.ADMINISTRATOR)
        profile2 = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL, is_active=False)

        for profile_id in [profile1.id, profile2.id, 0, self.principal.id]:
            response = self.client.post(self.build_url(principal.id), data={
                'new_school_principal': profile_id
            })
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data['new_school_principal'], [f'Invalid pk "{profile_id}" - object does not exist.'])

    def test_deactivate_teacher_missing_required_data(self):
        self.client.login(username=self.principal.username, password='passwd')

        teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=self.school_unit)
        study_class = StudyClassFactory(school_unit=self.school_unit, class_letter='B')
        TeacherClassThroughFactory(study_class=study_class, teacher=teacher, is_class_master=False)

        for req_data in [{}, {'new_teachers': []}]:
            response = self.client.post(self.build_url(teacher.id), data=req_data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data['new_teachers'], ['This field is required.'])

    def test_deactivate_teacher_invalid_teachers_array(self):
        self.client.login(username=self.principal.username, password='passwd')

        teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=self.school_unit)
        study_class = StudyClassFactory(school_unit=self.school_unit, class_letter='B')
        teacher_class_through1 = TeacherClassThroughFactory(study_class=study_class, teacher=teacher, is_class_master=False)
        teacher_class_through2 = TeacherClassThroughFactory(study_class=study_class, teacher=teacher, is_class_master=False)

        new_teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=self.school_unit)

        request_data = {
            'new_teachers': [
                {
                    'id': teacher_class_through1.id,
                    'teacher': new_teacher.id
                },
                {
                    'id': teacher_class_through2.id,
                    'teacher': new_teacher.id
                },
                {
                    'id': teacher_class_through1.id,
                    'teacher': new_teacher.id
                }
            ]
        }

        response = self.client.post(self.build_url(teacher.id), data=request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['new_teachers'], ['No duplicates allowed.'])

        request_data = {
            'new_teachers': [
                {
                    'id': teacher_class_through1.id,
                    'teacher': new_teacher.id
                }
            ]
        }

        response = self.client.post(self.build_url(teacher.id), data=request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['new_teachers'], ['There must be provided teachers for all classes and subjects.'])

    def test_deactivate_teacher_invalid_teacher(self):
        self.client.login(username=self.principal.username, password='passwd')

        teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=self.school_unit)

        subject1 = SubjectFactory(name='Dirigentie', is_coordination=True)
        subject2 = SubjectFactory(name='Subject')
        subject3 = SubjectFactory(name='Another Subject')

        study_class1 = StudyClassFactory(school_unit=self.school_unit, class_master=teacher)
        teacher_class_through1 = TeacherClassThroughFactory(study_class=study_class1, teacher=teacher,
                                                            subject=subject1, is_class_master=True)
        teacher_class_through2 = TeacherClassThroughFactory(study_class=study_class1, teacher=teacher,
                                                            subject=subject2, is_class_master=True)

        study_class2 = StudyClassFactory(school_unit=self.school_unit, class_grade='IV', class_grade_arabic=4)
        teacher_class_through3 = TeacherClassThroughFactory(study_class=study_class2, teacher=teacher,
                                                            subject=subject3, is_class_master=False)

        new_teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=self.school_unit)

        request_data = {
            'new_teachers': [
                {
                    'id': teacher_class_through1.id,
                    'teacher': 0
                },
                {
                    'id': teacher_class_through2.id,
                    'teacher': new_teacher.id
                },
                {
                    'id': teacher_class_through3.id,
                    'teacher': new_teacher.id
                }
            ]
        }

        response = self.client.post(self.build_url(teacher.id), data=request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['new_teachers'][0]['teacher'], [f'Invalid pk "{0}" - object does not exist.'])

        profile1 = UserProfileFactory(user_role=UserProfile.UserRoles.PARENT, school_unit=self.school_unit)
        profile2 = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=self.school_unit, is_active=False)
        profile3 = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=RegisteredSchoolUnitFactory())

        for profile in [profile1, profile2, profile3]:
            request_data['new_teachers'][0]['teacher'] = profile.id
            response = self.client.post(self.build_url(teacher.id), data=request_data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data['new_teachers'], ['At least one teacher is invalid.'])

        request_data['new_teachers'][0]['teacher'] = new_teacher.id
        response = self.client.post(self.build_url(teacher.id), data=request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['new_teachers'], ['Teacher {} does not teach {}.'.format(new_teacher.full_name, subject2.name)])

        new_teacher.taught_subjects.add(subject2)
        response = self.client.post(self.build_url(teacher.id), data=request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['new_teachers'], ['Teacher {} does not teach {}.'.format(new_teacher.full_name, subject3.name)])

        study_class2.class_master = new_teacher
        study_class2.save()

        response = self.client.post(self.build_url(teacher.id), data=request_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['new_teachers'], ['Invalid class master.'])

    def test_deactivate_principal_success(self):
        self.client.login(username=self.admin.username, password='passwd')

        principal = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL)
        school_unit = RegisteredSchoolUnitFactory(school_principal=principal)
        new_principal = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL)

        response = self.client.post(self.build_url(principal.id), data={
            "new_school_principal": new_principal.id
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(response.data.keys(), ['id', 'full_name', 'user_role', 'email', 'phone_number', 'use_phone_as_username',
                                                     'is_active', 'last_online', 'labels', 'school_unit'])
        self.assertFalse(response.data['is_active'])

        self.refresh_objects_from_db([principal, school_unit, new_principal])
        self.assertIsNone(principal.school_unit)
        self.assertEqual(school_unit.school_principal, new_principal)
        self.assertEqual(new_principal.school_unit, school_unit)

    def test_deactivate_teacher_success(self):
        self.client.login(username=self.principal.username, password='passwd')

        teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=self.school_unit)

        coordination_subject = SubjectFactory(name='Dirigentie', is_coordination=True)
        mandatory_subject1 = SubjectFactory(name='Subject')

        study_class1 = StudyClassFactory(school_unit=self.school_unit, class_master=teacher)
        teacher_class_through1 = TeacherClassThroughFactory(study_class=study_class1, teacher=teacher,
                                                            subject=coordination_subject, is_class_master=True)
        teacher_class_through2 = TeacherClassThroughFactory(study_class=study_class1, teacher=teacher,
                                                            subject=mandatory_subject1, is_class_master=True)

        study_class2 = StudyClassFactory(school_unit=self.school_unit, class_grade='III', class_grade_arabic=3)
        optional_subject = SubjectFactory(name='An optional subject')
        teacher_class_through3 = TeacherClassThroughFactory(study_class=study_class2, teacher=teacher, is_optional_subject=True,
                                                            subject=optional_subject, is_class_master=False)
        student = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=self.school_unit, student_in_class=study_class2)
        catalog1 = StudentCatalogPerSubjectFactory(student=student, teacher=teacher, study_class=study_class2, subject=optional_subject)
        mandatory_subject2 = SubjectFactory(name='Another subject')
        teacher_class_through4 = TeacherClassThroughFactory(study_class=study_class2, teacher=teacher, subject=mandatory_subject2, is_class_master=False)
        catalog2 = StudentCatalogPerSubjectFactory(student=student, teacher=teacher, study_class=study_class2, subject=mandatory_subject2)

        new_teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=self.school_unit)
        new_teacher.taught_subjects.add(mandatory_subject1)

        request_data = {
            'new_teachers': [
                {
                    'id': teacher_class_through1.id,
                    'teacher': new_teacher.id
                },
                {
                    'id': teacher_class_through2.id,
                    'teacher': new_teacher.id
                },
                {
                    'id': teacher_class_through3.id,
                    'teacher': new_teacher.id
                },
                {
                    'id': teacher_class_through4.id,
                    'teacher': study_class2.class_master.id
                }
            ]
        }

        response = self.client.post(self.build_url(teacher.id), data=request_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(response.data.keys(), ['id', 'full_name', 'user_role', 'email', 'phone_number', 'use_phone_as_username',
                                                     'is_active', 'last_online', 'labels', 'taught_subjects', 'assigned_study_classes'])
        self.assertFalse(response.data['is_active'])
        self.assertEqual(len(response.data['assigned_study_classes']), 0)

        self.refresh_objects_from_db([teacher_class_through1, teacher_class_through2, teacher_class_through3, teacher_class_through4,
                                      study_class1, study_class2, catalog1, catalog2])

        self.assertEqual(study_class1.class_master, new_teacher)
        self.assertEqual(teacher_class_through1.teacher, new_teacher)
        self.assertTrue(teacher_class_through1.is_class_master)

        self.assertEqual(teacher_class_through2.teacher, new_teacher)
        self.assertTrue(teacher_class_through2.is_class_master)

        self.assertEqual(teacher_class_through3.teacher, new_teacher)
        self.assertFalse(teacher_class_through3.is_class_master)
        self.assertEqual(catalog1.teacher, new_teacher)

        self.assertEqual(teacher_class_through4.teacher, study_class2.class_master)
        self.assertTrue(teacher_class_through4.is_class_master)
        self.assertEqual(catalog2.teacher, study_class2.class_master)

    @unpack
    @data(
        ('admin', UserProfile.UserRoles.ADMINISTRATOR),
        ('admin', UserProfile.UserRoles.PRINCIPAL),
        ('principal', UserProfile.UserRoles.TEACHER),
        ('principal', UserProfile.UserRoles.STUDENT),
        ('principal', UserProfile.UserRoles.PARENT),
    )
    def test_deactivate_user_no_request_data_success(self, login_user, user_role):
        self.client.login(username=getattr(self, login_user).username, password='passwd')
        profile = UserProfileFactory(
            user_role=user_role, is_active=True,
            school_unit=self.school_unit if user_role not in [UserProfile.UserRoles.ADMINISTRATOR, UserProfile.UserRoles.PRINCIPAL] else None
        )

        response = self.client.post(self.build_url(profile.id), data={})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        profile.refresh_from_db()
        self.assertFalse(profile.is_active)
        self.assertFalse(profile.user.is_active)
