import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Group, Post, Comment


User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='тестовое описание группы'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='test_comment',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    # Проверка создания поста
    def test_create_post(self):
        '''Проверка создания нового поста'''
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Текст нового поста',
            'group': self.group.id,
            'image': uploaded,
        }
        posts_before = set(Post.objects.values_list('id', flat=True))
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        posts_set = set(
            Post.objects.values_list('id', flat=True)
        ) - posts_before
        post_tuple = posts_set.pop()
        post = Post.objects.get(id=post_tuple)
        self.assertEqual(self.user, self.post.author)
        self.assertEqual(
            form_data['group'],
            post.group.id
        )
        self.assertEqual(
            form_data['text'],
            post.text
        )
        self.assertEqual(
            'posts/small.gif',
            post.image
        )
        self.assertRedirects(
            response,
            reverse('posts:profile',
                    kwargs={'username': self.user.username}
                    )
        )
        self.assertEqual(len(str(post_tuple)), 1)

    # Проверка редактирования поста
    def test_edit_post(self):
        form_data = {
            'text': 'Отредактированный текст',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        post = Post.objects.get(pk=self.post.id)
        self.assertEqual(self.user, self.post.author)
        self.assertEqual(
            form_data['group'],
            post.group.id
        )
        self.assertEqual(
            form_data['text'],
            post.text
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))

    # Проверка создания комментария
    def test_comment_create(self):
        comments_before = set(
            Comment.objects.values_list('id', flat=True)
        )
        form_data = {
            'text': 'Текст нового комментария',
        }
        self.authorized_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        comments_set = set(
            Comment.objects.values_list('id', flat=True)
        ) - comments_before
        comment_tuple = comments_set.pop()
        comment = Comment.objects.get(id=comment_tuple)
        self.assertEqual(self.post, comment.post)
        self.assertEqual(self.user, comment.author)
        self.assertEqual(
            form_data['text'],
            comment.text
        )
