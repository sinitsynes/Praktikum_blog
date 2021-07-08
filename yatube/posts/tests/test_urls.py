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
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_valid_url_200_response_unauthorized(self):
        responses = (
            '/',
            f'/group/{self.group.slug}/',
            f'/{self.author.username}/',
            f'/{self.author.username}/{self.post.id}/'
        )
        for value in responses:
            with self.subTest(response=value):
                response = self.guest_client.get(value)
                self.assertEqual(response.status_code, 200)

    def test_restricted_access_for_unauthorized(self):
        responses = (
            '/new/',
            f'/{self.author.username}/{self.post.id}/edit/'
        )
        for response in responses:
            with self.subTest(response=response):
                response = self.guest_client.get(response)
                self.assertEqual(response.status_code, 302)

    def test_new_post_redirect_unauthorized(self):
        response = self.guest_client.get('/new/', follow=True)
        self.assertRedirects(response, '/auth/login/?next=/new/')

    def test_valid_url_200_response_authorized(self):
        responses = (
            '/',
            f'/group/{self.group.slug}/',
            '/new/',
            f'/{self.author.username}/',
            f'/{self.author.username}/{self.post.id}/'
        )
        for response in responses:
            with self.subTest(response=response):
                response = self.authorized_client.get(response)
                self.assertEqual(response.status_code, 200)

    def test_templates_used(self):
        template_url = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group.html',
            '/new/': 'posts/new_post.html',
            f'/{self.author.username}/{self.post.id}/edit/':
            'posts/new_post.html',
            f'/{self.author.username}/': 'posts/profile.html',
            f'/{self.author.username}/{self.post.id}/': 'posts/post.html',
            '404': 'misc/404.html'
        }
        for address, template in template_url.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_edit_post_for_author(self):
        response = self.authorized_client.get(
            f'/{self.author.username}/{self.post.id}/edit/')
        self.assertEqual(response.status_code, 200)

    def test_edit_post_for_not_author(self):
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(self.not_author)
        response = self.authorized_client_2.get(
            f'/{self.author.username}/{self.post.id}/edit/'
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response, f'/{self.author.username}/{self.post.id}/')

    def test_404(self):
        response = self.guest_client.get(
            f'/{self.author.username}/{self.post.id} + {1}')
        self.assertEqual(response.status_code, 404)
