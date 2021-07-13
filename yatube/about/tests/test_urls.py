from http import HTTPStatus

from django.urls import reverse
from django.test import Client, TestCase


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_valid_url_response(self):
        pathnames = (
            'about:author',
            'about:tech',
        )
        for pathname in pathnames:
            with self.subTest(pathname=pathname):
                response = self.guest_client.get(reverse(pathname))
                self.assertEqual(response.status_code, HTTPStatus.OK)
