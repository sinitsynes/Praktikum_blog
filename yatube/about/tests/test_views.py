from django.test import Client, TestCase
from django.urls import reverse


class StaticViewsTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_page_uses_correct_template(self):
        templates = {
            'about/author.html': reverse('about:author'),
            'about/tech.html': reverse('about:tech')
        }
        for template, pathname in templates.items():
            with self.subTest(pathname=pathname):
                response = self.guest_client.get(pathname)
                self.assertTemplateUsed(response, template)
