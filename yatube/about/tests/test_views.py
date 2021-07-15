from django.test import TestCase
from django.urls import reverse


class StaticViewsTests(TestCase):

    def test_about_page_uses_correct_template(self):
        templates = (
            ('about/author.html', 'about:author'),
            ('about/tech.html', 'about:tech')
        )
        for template, pathname in templates:
            with self.subTest(pathname=pathname):
                response = self.client.get(reverse(pathname))
                self.assertTemplateUsed(response, template)
