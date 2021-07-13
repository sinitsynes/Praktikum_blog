import os
import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, override_settings, TestCase
from django.urls import reverse

from posts.models import Group, Post, User
from yatube.settings import BASE_DIR

if not os.path.exists(os.path.join(BASE_DIR, 'media')):
    os.mkdir('media')
else:
    pass


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(dir=settings.BASE_DIR))
class PostFormTests(TestCase):

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
        cls.not_author = User.objects.create(username='not_author')
        cls.group = Group.objects.create(
            title='тестовое сообщество',
            slug='test_slug',
            description='сообщество для тестов'
        )
        cls.post = Post.objects.create(
            text='Пост слоёного теста',
            author=cls.author,
            group=cls.group,
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        PostFormTests.author_client = Client()
        PostFormTests.author_client.force_login(PostFormTests.author)

    def test_post_create_authorized(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Здравствуйте, я из теста',
            'group': PostFormTests.group.id,
            'image': PostFormTests.uploaded
        }

        response = PostFormTests.author_client.post(
            reverse('new_post'), data=form_data,
            follow=True
        )
        new_post = Post.objects.first()
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(new_post.text, form_data['text'])
        self.assertEqual(new_post.group, PostFormTests.group)
        self.assertEqual(new_post.image, 'posts/small.gif')
        self.assertRedirects(response, reverse('index'))

    def test_post_create_unauthorized(self):
        posts_count_before = Post.objects.count()
        form_data = {
            'text': 'Здравствуйте, я из теста',
            'group': PostFormTests.group.id,
            'image': PostFormTests.uploaded
        }
        unauthorized_response = self.client.post(
            reverse('new_post'), data=form_data,
            follow=True
        )
        posts_count_after = Post.objects.count()
        self.assertEqual(posts_count_before, posts_count_after)
        self.assertRedirects(unauthorized_response, '/auth/login/?next=/new/')

    def test_authorized_post_edit(self):
        post_count_before = Post.objects.count()
        form_data = {
            'text': 'Отредактировал текст',
            'group': PostFormTests.group.id
        }
        to_edit_post = PostFormTests.author_client.post(
            reverse(
                'post_edit',
                kwargs={'username': PostFormTests.author,
                        'post_id': PostFormTests.post.id}
            ),
            data=form_data,
            follow=True
        )
        post_count_after = Post.objects.count()
        edited_post = PostFormTests.author_client.get(
            reverse('post_view',
                    kwargs={
                        'username': f'{PostFormTests.author.username}',
                        'post_id': f'{PostFormTests.post.id}'
                    }))
        post = edited_post.context['post']
        self.assertEqual(post_count_before, post_count_after)
        self.assertNotEqual(post.text, PostFormTests.post.text)
        self.assertEqual(post.group, PostFormTests.post.group)
        self.assertRedirects(
            to_edit_post,
            reverse('post_view', kwargs={
                    'username': f'{PostFormTests.author.username}',
                    'post_id': f'{PostFormTests.post.id}'
                    }))

    def test_unauthorized_edit(self):
        PostFormTests.not_author_client = Client()
        PostFormTests.not_author_client.force_login(PostFormTests.not_author)
        post_count_before = Post.objects.count()
        unauthorized_form_data = {
            'text': 'Правки от не-автора'
        }

        unauthorized_edit = PostFormTests.not_author_client.post(
            reverse(
                'post_edit',
                kwargs={'username': PostFormTests.author,
                        'post_id': PostFormTests.post.id}
            ),
            data=unauthorized_form_data,
            follow=True
        )

        post_count_after = Post.objects.count()

        unauthorized_edited_post = PostFormTests.not_author_client.get(
            reverse('post_view',
                    kwargs={
                        'username': f'{PostFormTests.author.username}',
                        'post_id': f'{PostFormTests.post.id}'
                    }))

        not_edited_post = unauthorized_edited_post.context['post']
        self.assertEqual(post_count_before, post_count_after)
        self.assertEqual(not_edited_post.text, PostFormTests.post.text)
        self.assertEqual(not_edited_post.group, PostFormTests.post.group)
        self.assertRedirects(
            unauthorized_edit,
            reverse('post_view',
                    kwargs={'username': f'{PostFormTests.author.username}',
                            'post_id': f'{PostFormTests.post.id}'
                            }))

    def test_comment_authorized(self):
        post = Post.objects.first()
        comment_count = post.comments.count()
        form_data = {
            'text': 'oh-la-la'
        }
        response = PostFormTests.author_client.post(
            reverse('add_comment',
                    kwargs={
                        'username': f'{PostFormTests.author.username}',
                        'post_id': f'{PostFormTests.post.id}'
                    }), data=form_data, follow=True)
        self.assertEqual(post.comments.count(), comment_count + 1)
        self.assertEqual(post.comments.first().text, form_data['text'])
        self.assertRedirects(
            response,
            reverse('post_view',
                    kwargs={'username': f'{PostFormTests.author.username}',
                            'post_id': f'{PostFormTests.post.id}'
                            }))

    def test_comment_unauthorized(self):
        post = Post.objects.first()
        comment_count = post.comments.count()
        form_data = {
            'text': 'oh-la-la'
        }
        unauthorized_response = self.client.post(
            reverse('add_comment',
                    kwargs={
                        'username': f'{PostFormTests.author.username}',
                        'post_id': f'{PostFormTests.post.id}'
                    }), data=form_data, follow=True)
        add_comment_url = reverse(
            'add_comment',
            kwargs={'username': f'{PostFormTests.author.username}',
                    'post_id': f'{PostFormTests.post.id}'
                    })
        self.assertEqual(post.comments.count(), comment_count)
        self.assertRedirects(unauthorized_response,
                             '/auth/login/?next=' + add_comment_url)
