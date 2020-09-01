from rest_framework.test import APITestCase


class CommonAPITestCase(APITestCase):
    @staticmethod
    def refresh_objects_from_db(list_of_objects):
        for obj in list_of_objects:
            obj.refresh_from_db()

    def tearDown(self):
        super().tearDown()

        if not self._outcome.errors[1][1]:
            print('{} PASSED'.format(self._testMethodName))
