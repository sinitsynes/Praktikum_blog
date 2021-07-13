from http import HTTPStatus

from django.core.cache import cache
from django.test import Client, TestCase

from posts.models import Group, Post, User


class PostsURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_author')
        cls.not_author = User.objects.create_user(username='not_author')
        cls.group = Group.objects.create(
            title='тестовое сообщество',
            slug='test_slug',
            description='сообщество для тестов'
        )
        cls.post = Post.objects.create(
            text='Здравствуйте, я из теста' * 15,
            author=cls.author,
            group=cls.group
        )

    def setUp(self):
        cache.clear()
        PostsURLTests.authorized_client = Client()
        PostsURLTests.authorized_client.force_login(PostsURLTests.author)

    def test_valid_url_200_response_unauthorized(self):
        responses = (
            '/',
            f'/group/{PostsURLTests.group.slug}/',
            f'/{PostsURLTests.author.username}/',
            f'/{PostsURLTests.author.username}/{PostsURLTests.post.id}/'
        )
        for value in responses:
            with self.subTest(response=value):
                response = self.client.get(value)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_restricted_access_for_unauthorized(self):
        responses = (
            '/new/',
            f'/{PostsURLTests.author.username}/{PostsURLTests.post.id}/edit/',
            f'/{PostsURLTests.author.username}'
            f'/{PostsURLTests.post.id}/comment/'
        )
        for response in responses:
            with self.subTest(response=response):
                response = self.client.get(response)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_redirect_unauthorized(self):
        not_author_client = Client()
        not_author_client.force_login(PostsURLTests.not_author)

        # неавторизованный пользователь не может создать пост,
        # переходит на страницу логина
        response = self.client.get('/new/', follow=True)
        self.assertRedirects(response, '/auth/login/?next=/new/')

        # неавторизованный пользователь не может комментировать пост,
        # переходит на страницу логина
        response = self.client.get(f'/{PostsURLTests.author.username}'
                                   f'/{PostsURLTests.post.id}/comment/')
        self.assertRedirects(
            response,
            '/auth/login/?next=' + f'/{PostsURLTests.author.username}'
                                   f'/{PostsURLTests.post.id}/comment/')

        # не-автор поста не может редактировать пост,
        # переходит на страницу его просмотра
        response = not_author_client.get(
            f'/{PostsURLTests.author.username}/{PostsURLTests.post.id}/edit/')
        self.assertRedirects(
            response,
            f'/{PostsURLTests.author.username}/{PostsURLTests.post.id}/')

    def test_valid_url_200_response_authorized(self):
        responses = (
            '/',
            f'/group/{PostsURLTests.group.slug}/',
            '/new/',
            f'/{PostsURLTests.author.username}/',
            f'/{PostsURLTests.author.username}/{PostsURLTests.post.id}/'
        )
        for response in responses:
            with self.subTest(response=response):
                response = self.authorized_client.get(response)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_post_for_author(self):
        response = PostsURLTests.authorized_client.get(
            f'/{PostsURLTests.author.username}/{PostsURLTests.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_post_for_not_author(self):
        authorized_client_2 = Client()
        authorized_client_2.force_login(PostsURLTests.not_author)
        response = authorized_client_2.get(
            f'/{PostsURLTests.author.username}/{PostsURLTests.post.id}/edit/'
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(
            response,
            f'/{PostsURLTests.author.username}/{PostsURLTests.post.id}/')

    def test_404(self):
        response = self.client.get('/not_existing_url/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
