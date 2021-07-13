import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import CommentForm, PostForm
from posts.models import Follow, Group, Post, User


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(dir=settings.BASE_DIR))
class PostsViewsTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif')
        cls.author = User.objects.create_user(username='test_author')
        cls.group = Group.objects.create(
            title='тестовое сообщество',
            slug='test_slug',
            description='сообщество для тестов'
        )
        cls.post = Post.objects.create(
            text='Здравствуйте, я из теста' * 15,
            author=cls.author,
            group=cls.group,
            image=cls.uploaded
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        cache.clear()
        PostsViewsTests.authorized_client = Client()
        PostsViewsTests.authorized_client.force_login(
            PostsViewsTests.author)

    def test_templates_used(self):
        urls = (
            ('index', None, 'posts/index.html'),
            ('new_post', None, 'posts/new_post.html'),
            ('post_view',
             (PostsViewsTests.author, PostsViewsTests.post.id),
             'posts/post.html'),
            ('group_posts',
             (PostsViewsTests.group.slug, ),
             'posts/group.html'),
            ('profile', (PostsViewsTests.author.username, ),
             'posts/profile.html'),
            ('post_edit',
             (PostsViewsTests.author, PostsViewsTests.post.id),
             'posts/new_post.html')
        )

        for url, args, template in urls:
            with self.subTest(url=url):
                response = PostsViewsTests.authorized_client.get(
                    reverse(url, args=args))
                self.assertTemplateUsed(response, template)

    def test_valid_page_context(self):
        # Проверка контекста для страниц с пажинатором
        responses_name_args = (
            ('index', None),
            ('profile', (PostsViewsTests.author.username,)),
            ('group_posts', (PostsViewsTests.group.slug,))
        )
        for url, args in responses_name_args:
            with self.subTest(url=url):
                response = PostsViewsTests.authorized_client.get(
                    reverse(url, args=args)
                )
                self.assertIn('page', response.context)
                post_on_page = response.context['page'][0]
                self.assertEqual(
                    PostsViewsTests.post.text, post_on_page.text)
                self.assertEqual(
                    PostsViewsTests.post.group, post_on_page.group)
                self.assertEqual(
                    PostsViewsTests.group.slug, post_on_page.group.slug
                )
                self.assertEqual(
                    PostsViewsTests.group.description,
                    post_on_page.group.description)
                self.assertEqual(
                    PostsViewsTests.post.image, post_on_page.image)
                self.assertEqual(
                    PostsViewsTests.post.author, post_on_page.author)

    def test_post_view_valid_context(self):
        response = PostsViewsTests.authorized_client.get(
            reverse('post_view',
                    kwargs={
                        'username': PostsViewsTests.author.username,
                        'post_id': PostsViewsTests.post.id
                    }))
        self.assertIn('post', response.context)

        post = response.context['post']
        self.assertEqual(PostsViewsTests.post.text, post.text)
        self.assertEqual(PostsViewsTests.post.group, post.group)
        self.assertEqual(PostsViewsTests.post.image, post.image)
        self.assertEqual(PostsViewsTests.post.author, post.author)
        self.assertEqual(PostsViewsTests.post.comments, post.comments)

        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], CommentForm)

    def test_new_post_edit_post_valid_context(self):
        responses = (
            reverse('new_post'),
            reverse('post_edit',
                    kwargs={
                        'username': PostsViewsTests.author.username,
                        'post_id': PostsViewsTests.post.id
                    }))
        for response in responses:
            response = PostsViewsTests.authorized_client.get(response)
            self.assertIn('form', response.context)
            self.assertIsInstance(response.context['form'], PostForm)

    def test_group_post_published_on_main(self):
        response = PostsViewsTests.authorized_client.get(reverse('index'))
        first_object = response.context['page'][0]
        self.assertEqual(first_object.group.title, PostsViewsTests.group.title)

    def test_group_post_published_on_group_page(self):
        response = PostsViewsTests.authorized_client.get(
            reverse('group_posts',
                    kwargs={'slug': PostsViewsTests.group.slug}))
        first_object = response.context['page'][0]
        self.assertEqual(first_object.group.title,
                         PostsViewsTests.group.title)

    def test_wrong_group_post(self):
        # Пост не попадает в неподходящую группу
        wrong_group = Group.objects.create(
            title='Wrong Group',
            slug='wrong_group',
            description='сюда пост попасть не должен'
        )
        wrong_post = Post.objects.create(
            text='Здравствуйте, я из другой группы',
            author=PostsViewsTests.author,
            group=wrong_group
        )
        response = PostsViewsTests.authorized_client.get(
            reverse(
                'group_posts', kwargs={'slug': wrong_group.slug}))
        wrong_post = response.context['page'][0]
        self.assertNotEqual(wrong_post.group.title,
                            PostsViewsTests.group.title)


class PaginatorTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='test_author')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.author)
        cls.group = Group.objects.create(
            title='тестовое сообщество',
            slug='test_slug',
            description='сообщество для тестов'
        )
        for i in range(15):
            cls.post = Post.objects.create(
                text='Здравствуйте, я из теста' * 15,
                author=cls.author,
                group=cls.group
            )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def setUp(self):
        cache.clear()

    def test_paginator(self):
        posts_on_page = (
            (10, 1, (reverse('index'))),
            (5, 2, (reverse('index') + '?page=2')),
        )
        for amount, page, url in posts_on_page:
            with self.subTest(page=page):
                response = PaginatorTest.authorized_client.get(url)
                self.assertEqual(
                    response.context.get(
                        'page').paginator.page(page).object_list.count(),
                    amount)


class CacheTest(TestCase):
    def setUp(self):
        cache.clear()
        CacheTest.author = User.objects.create(username='test_author')
        CacheTest.authorized_client = Client()
        CacheTest.authorized_client.force_login(CacheTest.author)
        CacheTest.other_user = User.objects.create(username='other_author')
        CacheTest.other_client = Client()
        CacheTest.other_client.force_login(CacheTest.other_user)

    def test_cached_index(self):
        # Обращаемся к странице впервые
        response = CacheTest.authorized_client.get(reverse('index'))

        # Создаем новый пост между обращениями
        test_post_for_cache = Post.objects.create(
            text='Новый пост, его нет в кэше',
            author=CacheTest.author
        )

        # Обращаемся повторно, страница идет из кеша без поста
        response_2 = CacheTest.authorized_client.get(reverse('index'))
        self.assertEqual(response_2.content, response.content)

        # Гостевой обращается к странице, для него кеш не создан
        other_user_response = CacheTest.other_client.get(reverse('index'))
        self.assertNotEqual(other_user_response.content, response.content)

        # Тестовый пост появляется на странице, его нет в кэше
        first_post_other_response = other_user_response.context['page'][0]
        self.assertEqual(test_post_for_cache.text,
                         first_post_other_response.text)

        # После чистки кэша пост виден и для первого пользователя
        cache.clear()
        response_3 = CacheTest.authorized_client.get(reverse('index'))
        first_post_response_3 = response_3.context['page'][0]
        self.assertEqual(test_post_for_cache.text,
                         first_post_response_3.text)


class FollowTestViews(TestCase):
    def setUp(self):
        FollowTestViews.reader_user = User.objects.create(username='reader')
        FollowTestViews.reader_client = Client()
        FollowTestViews.reader_client.force_login(FollowTestViews.reader_user)

        FollowTestViews.author = User.objects.create(username='author')
        FollowTestViews.author_client = Client()
        FollowTestViews.author_client.force_login(FollowTestViews.author)

        FollowTestViews.authors_post = Post.objects.create(
            text='Запись для теста подписок',
            author=FollowTestViews.author
        )

    def test_follow(self):
        followers_count = FollowTestViews.author.following.count()

        response = FollowTestViews.reader_client.get(
            reverse('profile_follow',
                    kwargs={'username': FollowTestViews.author.username}))
        recent_follower = Follow.objects.last()

        self.assertEqual(recent_follower.user, FollowTestViews.reader_user)
        self.assertEqual(recent_follower.author, FollowTestViews.author)
        self.assertEqual(
            FollowTestViews.author.following.count(), followers_count + 1)
        self.assertRedirects(
            response,
            reverse(
                'profile',
                kwargs={'username': FollowTestViews.author.username}))

    def test_unfollow(self):
        Follow.objects.create(
            user=FollowTestViews.reader_user,
            author=FollowTestViews.author
        )
        followers_count = FollowTestViews.author.following.count()

        response = FollowTestViews.reader_client.get(
            reverse('profile_unfollow',
                    kwargs={'username': FollowTestViews.author.username}))
        self.assertEqual(
            FollowTestViews.author.following.count(), followers_count - 1)
        self.assertFalse(
            FollowTestViews.author.following.filter(
                user=FollowTestViews.reader_user).exists())
        self.assertRedirects(
            response,
            reverse(
                'profile',
                kwargs={'username': FollowTestViews.author.username}))

    def test_followers_index(self):
        Follow.objects.create(
            user=FollowTestViews.reader_user,
            author=FollowTestViews.author
        )
        response = FollowTestViews.reader_client.get(reverse('follow_index'))
        self.assertTrue(
            FollowTestViews.authors_post in response.context['page'])

    def test_no_following(self):
        not_reader_user = User.objects.create(username='not_reader')
        not_reader_client = Client()
        not_reader_client.force_login(not_reader_user)

        response = not_reader_client.get(reverse('follow_index'))
        self.assertFalse(
            FollowTestViews.authors_post in response.context['page'])
