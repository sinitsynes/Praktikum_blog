from http import HTTPStatus

from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User


class PostsURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_author')
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
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsURLTests.author)

    def test_valid_url_200_response_unauthorized(self):
        author = PostsURLTests.author
        post = PostsURLTests.post
        group = PostsURLTests.group

        responses = (
            '/',
            f'/group/{group.slug}/',
            f'/{author.username}/',
            f'/{author.username}/{post.id}/'
        )
        for value in responses:
            with self.subTest(response=value):
                response = self.client.get(value)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_unauthorized(self):
        not_author = User.objects.create_user(username='not_author')
        not_author_client = Client()
        not_author_client.force_login(not_author)

        author = PostsURLTests.author
        post = PostsURLTests.post

        post_kwargs = {
            'username': author.username,
            'post_id': post.id
        }

        clients_redirect = (
            (self.client,
             '/new/',
             reverse('login') + '?next=' + reverse('new_post')
             ),

            (self.client,
             f'/{author.username}/{post.id}/comment/',
             reverse(
                 'login'
             ) + '?next=' + reverse(
                 'add_comment', kwargs=post_kwargs)),

            (not_author_client,
             f'/{PostsURLTests.author.username}/'
             f'{PostsURLTests.post.id}/edit/',
             reverse('post_view', kwargs=post_kwargs))
        )

        for client, request_url, redirect in clients_redirect:
            with self.subTest(client=client):
                response = client.get(request_url)
                self.assertRedirects(response, redirect)

    def test_valid_url_200_response_authorized(self):
        responses = (
            '/',
            f'/group/{PostsURLTests.group.slug}/',
            '/new/',
            f'/{PostsURLTests.author.username}/',
            f'/{PostsURLTests.author.username}/{PostsURLTests.post.id}/',
            f'/{PostsURLTests.author.username}/{PostsURLTests.post.id}/edit/'
        )
        for response in responses:
            with self.subTest(response=response):
                response = self.authorized_client.get(response)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_404(self):
        response = self.client.get('/not_existing_url/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
