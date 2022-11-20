from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='auth')
        cls.user_not_author = User.objects.create_user(username='auth_1')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='тестовое описание группы'
        )

        cls.post = Post.objects.create(
            text='тестовый текст',
            author=cls.user_author,
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client_post_author = Client()
        self.authorized_client_post_author.force_login(self.user_author)

    def test_reverse_name(self):
        template_names = {
            reverse('posts:index'):
                '/',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
                f'/group/{self.group.slug}/',
            reverse('posts:profile',
                    kwargs={'username': self.user_author.username}):
                f'/profile/{self.user_author.username}/',
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}):
                f'/posts/{self.post.id}/',
            reverse('posts:post_create'):
                '/create/',
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}):
                f'/posts/{self.post.id}/edit/',
        }
        for reverse_name, address in template_names.items():
            with self.subTest(reverse_name=reverse_name):
                self.assertEqual(reverse_name, address)

    # Проверка доступности страниц
    def test_pages_exist_at_desired_location(self):
        template_names = [
            (reverse('posts:index'),
                200, False),
            (reverse('posts:group_list', kwargs={'slug': self.group.slug}),
                200, False),
            (reverse('posts:profile',
                     kwargs={'username': self.user_author.username}),
                200, False),
            (reverse('posts:post_detail', kwargs={'post_id': self.post.id}),
                200, False),
            (reverse('posts:post_create'),
                200, True),
            (reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
                200, True),
            ('/unexisting_page/',
                404, False),
        ]
        for address, status, auth in template_names:
            with self.subTest(address=address):
                if auth:
                    response = self.authorized_client_post_author.get(address)
                else:
                    response = self.guest_client.get(address)
                self.assertEqual(response.status_code, status)

    # Проверка вызываемых шаблонов для каждого адреса
    def test_pages_use_correct_template(self):
        templates_pages_names = {
            reverse('posts:index'):
                'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
                'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': self.user_author.username}):
                'posts/profile.html',
            reverse('posts:post_create'):
                'posts/create_post.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}):
                'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}):
                'posts/create_post.html',
        }
        for address, template in templates_pages_names.items():
            with self.subTest(address=address):
                response = self.authorized_client_post_author.get(address)
                self.assertTemplateUsed(response, template)

    def test_unauthorized_redirect(self):
        urls = [
            reverse('posts:post_create'),
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(response, f'/auth/login/?next={url}')

    def test_edit_page_redirect(self):
        self.authorized_client_post_author.force_login(self.user_not_author)
        response = self.authorized_client_post_author.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
