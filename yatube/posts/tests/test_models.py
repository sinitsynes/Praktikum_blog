from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Group, Post

User = get_user_model()


class PostGroupTest(TestCase):

    def test_string_method(self):
        author = User.objects.create_user(username='TestAuthor')
        post = Post.objects.create(
            text='Тестовый текст' * 15,
            author=author
        )
        group = Group.objects.create(
            title='Тестовое сообщество',
            description='Сообщество для тестов',
            slug='test_slug'
        )
        instance_expectations = (
            (post, post.text[:15]),
            (group, group.title)
        )
        for instance, expectation in instance_expectations:
            with self.subTest(instance):
                self.assertEqual(expectation, str(instance))
