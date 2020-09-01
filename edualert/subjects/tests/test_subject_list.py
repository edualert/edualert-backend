from ddt import ddt, data
from django.urls import reverse
from rest_framework import status

from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.subjects.factories import SubjectFactory


@ddt
class SubjectListTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.principal = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL)
        cls.school_unit = RegisteredSchoolUnitFactory(school_principal=cls.principal)
        cls.url = reverse('subjects:subject-list')

    def test_subject_list_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.TEACHER,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_subject_list_wrong_user_type(self, user_role):
        profile = UserProfileFactory(
            user_role=user_role,
            school_unit=self.school_unit if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )
        self.client.login(username=profile.username, password='passwd')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_subject_list(self):
        self.client.login(username=self.principal.username, password='passwd')

        subject1 = SubjectFactory(name='Matematica')
        subject2 = SubjectFactory(name='Limba romana')
        subject3 = SubjectFactory(name='Fizica')
        SubjectFactory(name='Dirigentie', is_coordination=True)
        SubjectFactory(name='Some other subject', should_be_in_taught_subjects=False)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

        self.assertEqual(subject3.id, response.data[0]['id'])
        self.assertEqual(subject2.id, response.data[1]['id'])
        self.assertEqual(subject1.id, response.data[2]['id'])

        for result in response.data:
            self.assertCountEqual(result.keys(), ['id', 'name'])

        # Search
        response = self.client.get(self.url, {'search': 'ma'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        self.assertEqual(subject2.id, response.data[0]['id'])
        self.assertEqual(subject1.id, response.data[1]['id'])
