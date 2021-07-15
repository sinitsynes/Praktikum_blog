import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Group, Post, User

TEMP_MEDIA = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
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
        cls.group = Group.objects.create(
            title='тестовое сообщество',
            slug='test_slug',
            description='сообщество для тестов'
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(PostFormTests.author)

    def test_post_create_authorized(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Здравствуйте, я из теста',
            'group': PostFormTests.group.id,
            'image': PostFormTests.uploaded
        }

        response = self.author_client.post(
            reverse('new_post'), data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('index'))

        new_post = Post.objects.first()
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(new_post.text, form_data['text'])
        self.assertEqual(new_post.group.id, form_data['group'])
        self.assertEqual(new_post.image, 'posts/small.gif')

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
        self.assertRedirects(
            unauthorized_response,
            reverse('login') + '?next=' + reverse('new_post'))

        posts_count_after = Post.objects.count()
        self.assertEqual(posts_count_before, posts_count_after)

    def test_authorized_post_edit(self):
        new_group = Group.objects.create(
            title='New Group',
            slug='new_group',
            description='group to test editing'
        )
        post = Post.objects.create(
            text='Пост слоёного теста',
            author=PostFormTests.author,
            group=PostFormTests.group,
        )
        post_view_kwargs = {'username': post.author.username,
                            'post_id': post.id}

        post_count_before = Post.objects.count()

        form_data = {
            'text': 'Отредактировал текст',
            'group': new_group.id
        }
        to_edit_post = self.author_client.post(
            reverse('post_edit', kwargs=post_view_kwargs),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            to_edit_post,
            reverse('post_view', kwargs=post_view_kwargs))

        post_count_after = Post.objects.count()
        post.refresh_from_db()

        self.assertEqual(post_count_before, post_count_after)
        self.assertEqual(form_data['text'], post.text)
        self.assertEqual(form_data['group'], new_group.id)
        self.assertEqual(post.author.username, PostFormTests.author.username)

    def test_unauthorized_edit(self):
        new_group = Group.objects.create(
            title='New Group',
            slug='new_group',
            description='group to test editing'
        )
        post = Post.objects.create(
            text='Пост слоёного теста',
            author=PostFormTests.author,
            group=PostFormTests.group,
        )
        post_view_kwargs = {'username': post.author.username,
                            'post_id': post.id}

        not_author = User.objects.create(username='not_author')
        not_author_client = Client()
        not_author_client.force_login(not_author)

        post_count_before = Post.objects.count()
        form_data = {
            'text': 'Правки от не-автора',
            'group': new_group.id
        }

        unauthorized_edit = not_author_client.post(
            reverse('post_edit', kwargs=post_view_kwargs),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            unauthorized_edit,
            reverse('post_view', kwargs=post_view_kwargs))
        post_count_after = Post.objects.count()

        post.refresh_from_db()

        self.assertEqual(post_count_before, post_count_after)
        self.assertNotEqual(form_data['text'], post.text)
        self.assertNotEqual(form_data['group'], post.group)
        self.assertEqual(
            PostFormTests.author.username, post.author.username)

    def test_comment_authorized(self):
        post = Post.objects.create(
            text='Пост слоёного теста',
            author=PostFormTests.author,
            group=PostFormTests.group,
        )
        post_view_kwargs = {'username': post.author.username,
                            'post_id': post.id}

        comment_count = post.comments.count()
        form_data = {
            'text': 'oh-la-la'
        }

        response = self.author_client.post(
            reverse('add_comment', kwargs=post_view_kwargs),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('post_view', kwargs=post_view_kwargs))

        comment = post.comments.first()
        self.assertEqual(post.comments.count(), comment_count + 1)
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(comment.post.id, post.id)
        self.assertEqual(comment.author.username, post.author.username)

    def test_comment_unauthorized(self):
        post = Post.objects.create(
            text='Пост слоёного теста',
            author=PostFormTests.author,
            group=PostFormTests.group,
        )
        post_view_kwargs = {'username': post.author.username,
                            'post_id': post.id}

        comment_count = post.comments.count()
        form_data = {
            'text': 'oh-la-la'
        }
        unauthorized_response = self.client.post(
            reverse('add_comment',
                    kwargs=post_view_kwargs),
            data=form_data,
            follow=True
        )

        add_comment_url = reverse('add_comment', kwargs=post_view_kwargs)
        self.assertRedirects(unauthorized_response,
                             reverse('login') + '?next=' + add_comment_url)

        self.assertEqual(post.comments.count(), comment_count)
