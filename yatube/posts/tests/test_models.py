from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='TestAuthor')
        cls.post = Post.objects.create(
            text='Тестовый текст' * 15,
            author=cls.author
        )

    def test_string_method(self):
        post = self.post
        expected_content = post.text[:15]
        self.assertEqual(expected_content, str(post))


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовое сообщество',
            description='Сообщество для тестов',
            slug='test_slug'
        )

    def test_string_method(self):
        group = self.group
        expected_content = group.title
        self.assertEqual(expected_content, str(group))
