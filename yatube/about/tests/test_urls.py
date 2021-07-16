from http import HTTPStatus

from django.test import TestCase
from django.urls import reverse


class StaticURLTests(TestCase):

    def test_valid_url_response(self):
        pathnames = (
            'about:author',
            'about:tech',
        )
        for pathname in pathnames:
            with self.subTest(pathname=pathname):
                response = self.client.get(reverse(pathname))
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_names_valid_path(self):
        pathname_url = (
            ('about:author', '/about/author/'),
            ('about:tech', '/about/tech/')
        )
        for pathname, url in pathname_url:
            with self.subTest(pathname=pathname):
                self.assertEqual(reverse(pathname), url)
