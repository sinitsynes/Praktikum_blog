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

    def test_verbose_name(self):
        post = PostModelTest.post
        field_verboses = {
            'text': 'Текст поста',
            'author': 'Автор',
            'group': 'Сообщество'
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value
                )

    def test_help_text(self):
        post = PostModelTest.post
        field_help_texts = {
            'text': 'Напишите текст записи',
            'group': 'Укажите сообщество'
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value
                )

    def test_string_method(self):
        post = PostModelTest.post
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

    def test_verbose_name(self):
        group = GroupModelTest.group
        field_verboses = {
            'title': 'Название сообщества',
            'description': 'Описание сообщества'
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    group._meta.get_field(field).verbose_name, expected_value)

    def test_string_method(self):
        group = GroupModelTest.group
        expected_content = group.title
        self.assertEqual(expected_content, str(group))
