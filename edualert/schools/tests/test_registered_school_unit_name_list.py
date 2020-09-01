from django.urls import reverse
from rest_framework import status

from edualert.common.api_tests import CommonAPITestCase
from edualert.schools.factories import RegisteredSchoolUnitFactory


class RegisteredSchoolUnitNameListTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('schools:school-unit-name-list')

    def test_school_unit_name_list_empty(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_school_unit_name_list_success(self):
        school_unit1 = RegisteredSchoolUnitFactory(name='school b')
        school_unit2 = RegisteredSchoolUnitFactory(name='school a')
        school_unit3 = RegisteredSchoolUnitFactory(name='school c', is_active=False)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data
        self.assertEqual(len(results), 3)
        self.assertEqual(school_unit2.id, results[0]['id'])
        self.assertEqual(school_unit1.id, results[1]['id'])
        self.assertEqual(school_unit3.id, results[2]['id'])

        expected_fields = ['id', 'name', 'city']
        for result in results:
            self.assertCountEqual(result.keys(), expected_fields)

        # Search by name
        response = self.client.get(self.url, {'search': 'a'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.data), 1)
        self.assertEqual(school_unit2.id, response.data[0]['id'])

        # Filter by is_active
        response = self.client.get(self.url, {'is_active': 'true'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.data), 2)
        self.assertEqual(school_unit2.id, response.data[0]['id'])
        self.assertEqual(school_unit1.id, response.data[1]['id'])
