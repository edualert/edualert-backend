from ddt import data, ddt, unpack
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from edualert.academic_calendars.factories import AcademicYearCalendarFactory
from edualert.catalogs.factories import SubjectGradeFactory, SubjectAbsenceFactory, ExaminationGradeFactory
from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.study_classes.factories import TeacherClassThroughFactory


@ddt
class UserProfileDeleteTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        AcademicYearCalendarFactory()
        cls.admin = UserProfileFactory(user_role=UserProfile.UserRoles.ADMINISTRATOR)
        cls.principal = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL)
        cls.school_unit = RegisteredSchoolUnitFactory(school_principal=cls.principal)

    @staticmethod
    def build_url(profile_id):
        return reverse('users:user-profile-detail', kwargs={'id': profile_id})

    def test_delete_user_unauthenticated(self):
        response = self.client.delete(self.build_url(self.admin.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.TEACHER,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_delete_user_wrong_user_type(self, user_role):
        profile = UserProfileFactory(user_role=user_role, school_unit=self.school_unit)
        self.client.login(username=profile.username, password='passwd')

        response = self.client.delete(self.build_url(self.principal.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @data(
        'admin', 'principal'
    )
    def test_delete_user_not_found(self, profile):
        self.client.login(username=getattr(self, profile).username, password='passwd')

        response = self.client.delete(self.build_url(0))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @unpack
    @data(
        ('admin', UserProfile.UserRoles.TEACHER),
        ('admin', UserProfile.UserRoles.STUDENT),
        ('admin', UserProfile.UserRoles.PARENT),
        ('principal', UserProfile.UserRoles.ADMINISTRATOR),
        ('principal', UserProfile.UserRoles.PRINCIPAL),
    )
    def test_delete_user_wrong_requested_user_type(self, login_user, user_role):
        self.client.login(username=getattr(self, login_user).username, password='passwd')
        profile = UserProfileFactory(
            user_role=user_role,
            school_unit=self.school_unit if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )

        response = self.client.delete(self.build_url(profile.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_user_was_online(self):
        student = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, last_online=timezone.now(),
                                     school_unit=self.school_unit)
        self.client.login(username=self.principal.username, password='passwd')

        response = self.client.delete(self.build_url(student.id))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], "This user cannot be deleted because it's either active or has data.")

    def test_delete_user_teacher_has_classes(self):
        teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=self.school_unit)
        TeacherClassThroughFactory(teacher=teacher)
        self.client.login(username=self.principal.username, password='passwd')

        response = self.client.delete(self.build_url(teacher.id))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], "This user cannot be deleted because it's either active or has data.")

    def test_delete_user_student_has_data(self):
        self.client.login(username=self.principal.username, password='passwd')
        student1 = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=self.school_unit)
        SubjectGradeFactory(student=student1)
        student2 = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=self.school_unit)
        SubjectAbsenceFactory(student=student2)
        student3 = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=self.school_unit)
        ExaminationGradeFactory(student=student3)

        for student in [student1, student2, student3]:
            response = self.client.delete(self.build_url(student.id))
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data['message'], "This user cannot be deleted because it's either active or has data.")

    @unpack
    @data(
        ('admin', UserProfile.UserRoles.ADMINISTRATOR),
        ('admin', UserProfile.UserRoles.PRINCIPAL),
        ('principal', UserProfile.UserRoles.TEACHER),
        ('principal', UserProfile.UserRoles.STUDENT),
        ('principal', UserProfile.UserRoles.PARENT),
    )
    def test_delete_user_success(self, login_user, user_role):
        self.client.login(username=getattr(self, login_user).username, password='passwd')
        profile = UserProfileFactory(
            user_role=user_role,
            school_unit=self.school_unit if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )

        response = self.client.delete(self.build_url(profile.id))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
