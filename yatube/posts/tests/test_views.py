import shutil
import tempfile

from django.test import Client, TestCase
from django.urls import reverse
from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from posts.models import Follow, Group, Post, User


class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
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
        cls.urls = (
            ('index', None, 'posts/index.html'),
            ('new_post', None, 'posts/new_post.html'),
            ('post_view', (cls.author, cls.post.id), 'posts/post.html'),
            ('group_posts', (cls.group.slug, ), 'posts/group.html'),
            ('profile', (cls.author.username, ), 'posts/profile.html'),
            ('post_edit', (cls.author, cls.post.id), 'posts/new_post.html')
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_templates_used(self):
        for url, args, template in self.urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(reverse(url, args=args))
                self.assertTemplateUsed(response, template)

    def test_index_and_post_valid_context(self):
        responses = {
            reverse('index'): 'page',
            reverse('post_view',
                    kwargs={
                        'username': self.author.username,
                        'post_id': self.post.id
                    }): 'post',
        }
        for path, context in responses.items():
            with self.subTest(context=context):
                response = self.authorized_client.get(path)
                self.assertIn(context, response.context)
                self.assertContains(response, '<img')

    def test_profile_valid_context(self):
        list_of_context = (
            'author',
            'page'
        )
        for context_value in list_of_context:
            with self.subTest(context_value=context_value):
                response = self.authorized_client.get(
                    reverse('profile',
                            kwargs={'username': self.author.username}
                            )
                )
                self.assertIn(context_value, response.context)
                self.assertContains(response, '<img')

    def test_new_post_edit_post_valid_context(self):
        responses = (
            reverse('new_post'),
            reverse('post_edit',
                    kwargs={
                        'username': self.author.username,
                        'post_id': self.post.id
                    }))
        for response in responses:
            response = self.authorized_client.get(response)
            form_fields = {
                'text': forms.fields.CharField,
                'group': forms.fields.ChoiceField,
                'image': forms.fields.ImageField
            }
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context['form'].fields[value]
                    self.assertIsInstance(form_field, expected)

    def test_group_posts_valid_context(self):
        list_of_context = (
            'group',
            'page'
        )
        for context_value in list_of_context:
            with self.subTest(context_value=context_value):
                response = self.authorized_client.get(
                    reverse(
                        'group_posts', kwargs={'slug': f'{self.group.slug}'})
                )
                self.assertIn(context_value, response.context)
                self.assertContains(response, '<img')

    def test_group_post_published_on_main(self):
        response = self.authorized_client.get(reverse('index'))
        first_object = response.context['page'][0]
        self.assertEqual(first_object.group.title, self.group.title)

    def test_group_post_published_on_group_page(self):
        response = self.authorized_client.get(
            reverse('group_posts', kwargs={'slug': self.group.slug}))
        first_object = response.context['page'][0]
        self.assertEqual(first_object.group.title, self.group.title)

    def test_wrong_group_post(self):
        wrong_group = Group.objects.create(
            title='Wrong Group',
            slug='wrong_group',
            description='сюда пост попасть не должен'
        )
        wrong_post = Post.objects.create(
            text='Здравствуйте, я из другой группы',
            author=self.author,
            group=wrong_group
        )
        response = self.authorized_client.get(
            reverse(
                'group_posts', kwargs={'slug': wrong_group.slug}))
        wrong_post = response.context['page'][0]
        self.assertNotEqual(wrong_post.group.title, self.group.title)


class PaginatorTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='test_author')
        cls.guest_client = Client()
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
            (5, 2, (reverse('index') + '?page=2' )),
            (10, 1, (reverse('profile',
                     kwargs={'username': self.author.username}))),
            (5, 2, (reverse('profile',
                    kwargs={'username': self.author.username}) + '?page=2')),
            (10, 1, (reverse('group_posts',
                     kwargs={'slug': self.group.slug}))),
            (5, 2, (reverse('group_posts',
                    kwargs={'slug': self.group.slug}) + '?page=2'))
        )
        for amount, page, url in posts_on_page:
            with self.subTest(page=page):
                response = self.guest_client.get(url)
                self.assertEqual(
                response.context.get(
                    'page').paginator.page(page).object_list.count(), amount)


class CacheTest(TestCase):
    def setUp(self):
        cache.clear()
        self.author = User.objects.create(username='test_author')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_cached_index(self):
        self.authorized_client.get(reverse('index'))
        test_post_for_cache = Post.objects.create(
            text='Новый пост, его нет в кэше',
            author=self.author
        )
        response_2 = self.authorized_client.get(reverse('index'))
        self.assertEqual(response_2.context, None)
        cache.clear()
        response_3 = self.authorized_client.get(reverse('index'))
        first_post_in_response_3 = response_3.context['page'][0]
        self.assertEqual(test_post_for_cache.text,
                         first_post_in_response_3.text)


class CommentTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='test_author')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.author)
        cls.post = Post.objects.create(
            text='Здравствуйте, я из теста' * 15,
            author=cls.author,
            ) 
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.author)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def test_comment_authorized_only(self):
        form_data = {
            'text': 'Тестовый комментарий'
        }
        
        response = self.authorized_client.get(reverse('post_view', kwargs={
                        'username': self.author.username,
                        'post_id': self.post.id
                    }))
        
        self.guest_client.post(reverse('add_comment', kwargs={
                        'username': self.author.username,
                        'post_id': self.post.id
                    }), data=form_data, follow=True)
        self.assertNotContains(response, form_data['text'])

        self.authorized_client.post(reverse('add_comment', kwargs={
                        'username': self.author.username,
                        'post_id': self.post.id
                    }), data=form_data, follow=True)

        response_2 = self.authorized_client.get(reverse('post_view', kwargs={
                        'username': self.author.username,
                        'post_id': self.post.id
                    }))
        self.assertContains(response_2, form_data['text'])


class FollowTestViews(TestCase):    
    def setUp(self):
        self.reader_user = User.objects.create(username='reader')
        self.reader_client = Client()
        self.reader_client.force_login(self.reader_user)

        self.author = User.objects.create(username='author')
        self.author_client = Client()
        self.author_client.force_login(self.author)

        self.follow = Follow.objects.create(
            user=self.reader_user,
            author=self.author
        )

        self.authors_post = Post.objects.create(
            text='Запись для теста подписок',
            author = self.author
        )

    def test_follow(self):
        self.reader_client.get(reverse('profile_follow',
                              kwargs={'username': self.author.username}))
        self.assertTrue(
            self.author.following.filter(
                user=self.reader_user).exists())
        
    def test_unfollow(self):
        self.reader_client.get(reverse('profile_unfollow',
                              kwargs={'username': self.author.username}))
        self.assertFalse(
            self.author.following.filter(
                user=self.reader_user).exists())
    
    def test_followers_follow(self):
        response = self.reader_client.get(reverse('follow_index'))
        self.assertTrue(
            self.authors_post in response.context['page'])

    def test_no_following(self):
        not_reader_user = User.objects.create(username='not_reader')
        not_reader_client = Client()
        not_reader_client.force_login(not_reader_user)

        response = not_reader_client.get(reverse('follow_index'))
        self.assertFalse(
            self.authors_post in response.context['page'])
