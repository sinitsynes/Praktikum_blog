import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User


class PostCreateFormTests(TestCase):
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
            text='Пост слоёного теста',
            author=cls.author,
            group=cls.group,
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_post_create(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Здравствуйте, я из теста',
            'group': self.group.id,
            'image': self.uploaded
        }
        self.authorized_client.post(
            reverse('new_post'), data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(Post.objects.filter(
            text=form_data['text'],
            group=form_data['group'],
            image='posts/small.gif'
        ).exists()
        )

    def test_post_edited(self):
        form_data = {
            'text': 'Отредактировал текст',
            'group': self.group.id
        }
        self.authorized_client.post(
            reverse(
                'post_edit',
                kwargs={'username': self.author, 'post_id': self.post.id}
            ),
            data=form_data,
            follow=True
        )
        response = self.authorized_client.get(
            reverse('post_view',
                    kwargs={
                        'username': f'{self.author.username}',
                        'post_id': f'{self.post.id}'
                    }))
        post = response.context['post']
        self.assertNotEqual(post.text, self.post.text)
        self.assertEqual(post.group, self.post.group)
