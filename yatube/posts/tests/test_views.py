import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import CommentForm, PostForm
from posts.models import Follow, Group, Post, User
from yatube.settings import POST_COUNT

TEMP_MEDIA = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
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

    def post_check(self, context, is_post=False):
        example = PostsViewsTests.post
        if is_post:
            self.assertIn('post', context)
            post = context['post']
        else:
            self.assertIn('page', context)
            self.assertTrue(len(context) > 0, 'Страница пуста')
            post = context['page'][0]

        example_attrs = (
            (example.author.username, post.author.username),
            (example.text, post.text),
            (example.group, post.group),
            (example.image, post.image),
            (example.pub_date, post.pub_date)
        )
        for expected_attr, post_attr in example_attrs:
            with self.subTest(post_attr=post_attr):
                self.assertEqual(expected_attr, post_attr)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(
            PostsViewsTests.author)

    def test_templates_used(self):
        example_author = PostsViewsTests.author
        example_post = PostsViewsTests.post
        example_group = PostsViewsTests.group

        urls = (
            ('index', None, 'posts/index.html'),
            ('new_post', None, 'posts/new_post.html'),
            ('post_view',
             (example_author.username, example_post.id),
             'posts/post.html'),
            ('group_posts',
             (example_group.slug,),
             'posts/group.html'),
            ('profile', (example_author.username,),
             'posts/profile.html'),
            ('post_edit',
             (example_author.username, example_post.id),
             'posts/new_post.html')
        )

        for url, args, template in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(
                    reverse(url, args=args))
                self.assertTemplateUsed(response, template)

    def test_index_valid_context(self):
        response = self.authorized_client.get(
            reverse('index')
        )
        self.assertIn('page', response.context)
        self.post_check(response.context)

    def test_profile_valid_context(self):
        response = self.authorized_client.get(
            reverse(
                'profile',
                kwargs={'username': PostsViewsTests.author.username})
        )
        list_of_context = (
            'author',
            'page',
            'following'
        )
        for item in list_of_context:
            with self.subTest(item=item):
                self.assertIn(item, response.context)

        author = response.context['author']
        self.assertEqual(author.username, PostsViewsTests.author.username)

        self.post_check(response.context)

    def test_group_posts_valid_context(self):
        example_group = PostsViewsTests.group
        response = self.authorized_client.get(
            reverse('group_posts', kwargs={'slug': example_group.slug})
        )
        list_of_context = (
            'group',
            'page'
        )
        for item in list_of_context:
            with self.subTest(item=item):
                self.assertIn(item, response.context)

        group = response.context['group']
        group_attrs_expected = (
            (example_group.title, group.title),
            (example_group.slug, group.slug),
            (example_group.description, group.description)
        )
        for expected_group_attr, group_attr in group_attrs_expected:
            with self.subTest(expected_group_attr=group_attr):
                self.assertEqual(expected_group_attr, group_attr)

        self.post_check(response.context)

    def test_post_view_valid_context(self):
        example_author = PostsViewsTests.author
        example_post = PostsViewsTests.post
        response = self.authorized_client.get(
            reverse('post_view',
                    kwargs={
                        'username': example_author.username,
                        'post_id': example_post.id
                    }))
        self.assertIn('post', response.context)
        self.post_check(response.context, is_post=True)

        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], CommentForm)

    def test_new_post_edit_post_valid_context(self):
        example_author = PostsViewsTests.author
        example_post = PostsViewsTests.post
        urls = (
            reverse('new_post'),
            reverse('post_edit',
                    kwargs={
                        'username': example_author.username,
                        'post_id': example_post.id
                    }))
        for url in urls:
            response = self.authorized_client.get(url)
            self.assertIn('form', response.context)
            self.assertIsInstance(response.context['form'], PostForm)

    def test_group_post_published_on_main(self):
        response = self.authorized_client.get(reverse('index'))
        self.assertIn(PostsViewsTests.post, response.context['page'])

    def test_group_post_published_on_group_page(self):
        response = self.authorized_client.get(
            reverse('group_posts',
                    kwargs={'slug': PostsViewsTests.group.slug}))
        self.assertIn(PostsViewsTests.post, response.context['page'])

    def test_wrong_group_post(self):
        # Пост не попадает в неподходящую группу
        wrong_group = Group.objects.create(
            title='Wrong Group',
            slug='wrong_group',
            description='сюда пост попасть не должен'
        )
        response = self.authorized_client.get(
            reverse(
                'group_posts', kwargs={'slug': wrong_group.slug}))
        self.assertNotIn(PostsViewsTests.post, response.context['page'])


class PaginatorTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='test_author')
        cls.group = Group.objects.create(
            title='тестовое сообщество',
            slug='test_slug',
            description='сообщество для тестов'
        )
        cls.POST_ORPHANS = 7
        cls.posts = (
            Post(
                text='Здравствуйте, я из теста %s' % i,
                author=cls.author,
                group=cls.group
            )
            for i in range(POST_COUNT + cls.POST_ORPHANS)
        )
        Post.objects.bulk_create(cls.posts)

    def setUp(self):
        cache.clear()

    def test_paginator(self):
        posts_on_page = (
            (POST_COUNT, 1, (reverse('index'))),
            (PaginatorTest.POST_ORPHANS, 2, (reverse('index') + '?page=2')),
        )
        for amount, page, url in posts_on_page:
            with self.subTest(page=page):
                response = self.client.get(url)
                self.assertEqual(
                    response.context.get(
                        'page').paginator.page(page).object_list.count(),
                    amount)


class CacheTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='test_author')

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(CacheTest.author)

    def test_cached_index(self):
        # Обращаемся к странице впервые
        response = self.authorized_client.get(reverse('index'))

        # Создаем новый пост между обращениями
        test_post_for_cache = Post.objects.create(
            text='Новый пост, его нет в кэше',
            author=CacheTest.author
        )

        # Обращаемся повторно, страница идет из кеша без поста
        response_2 = self.authorized_client.get(reverse('index'))
        self.assertEqual(response_2.content, response.content)

        # Гостевой обращается к странице, для него кеш не создан
        other_user_response = self.client.get(reverse('index'))
        self.assertNotEqual(other_user_response.content, response.content)

        # Тестовый пост появляется на странице, его нет в кэше
        first_post_other_response = other_user_response.context['page'][0]
        self.assertEqual(test_post_for_cache.text,
                         first_post_other_response.text)

        # После чистки кэша пост виден и для первого пользователя
        cache.clear()
        response_3 = self.authorized_client.get(reverse('index'))
        first_post_response_3 = response_3.context['page'][0]
        self.assertEqual(test_post_for_cache.text,
                         first_post_response_3.text)


class FollowTestViews(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.reader_user = User.objects.create(username='reader')
        cls.author = User.objects.create(username='author')

    def setUp(self):
        self.reader_client = Client()
        self.reader_client.force_login(FollowTestViews.reader_user)

    def test_follow(self):
        followers_count = Follow.objects.count()

        response = self.reader_client.get(
            reverse('profile_follow',
                    kwargs={'username': FollowTestViews.author.username}))
        self.assertRedirects(
            response,
            reverse(
                'profile',
                kwargs={'username': FollowTestViews.author.username}))

        self.assertEqual(Follow.objects.count(), followers_count + 1)

        recent_follower = Follow.objects.last()
        self.assertEqual(recent_follower.user, FollowTestViews.reader_user)
        self.assertEqual(recent_follower.author, FollowTestViews.author)

    def test_unfollow(self):
        Follow.objects.create(
            user=FollowTestViews.reader_user,
            author=FollowTestViews.author
        )

        followers_count = Follow.objects.count()

        response = self.reader_client.get(
            reverse('profile_unfollow',
                    kwargs={'username': FollowTestViews.author.username}))
        self.assertRedirects(
            response,
            reverse(
                'profile',
                kwargs={'username': FollowTestViews.author.username}))

        self.assertEqual(Follow.objects.count(), followers_count - 1)

    def test_followers_index(self):
        authors_post = Post.objects.create(
            text='Запись для теста подписок',
            author=FollowTestViews.author
        )

        Follow.objects.create(
            user=FollowTestViews.reader_user,
            author=FollowTestViews.author
        )
        response = self.reader_client.get(reverse('follow_index'))
        self.assertTrue(
            authors_post in response.context['page'])

    def test_no_following(self):
        authors_post = Post.objects.create(
            text='Запись для теста подписок',
            author=FollowTestViews.author
        )

        not_reader_user = User.objects.create(username='not_reader')
        not_reader_client = Client()
        not_reader_client.force_login(not_reader_user)

        response = not_reader_client.get(reverse('follow_index'))
        self.assertFalse(
            authors_post in response.context['page'])
