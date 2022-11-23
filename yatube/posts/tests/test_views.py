from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Group, Post, Follow
from posts.forms import PostForm

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
        cls.user = User.objects.create_user(username='auth')
        cls.user_follower = User.objects.create_user(username='follower')
        cls.group_with_post = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='тестовое описание группы'
        )
        cls.group_without_post = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug-2',
            description='тестовое описание группы 2'
        )
        cls.post = Post.objects.create(
            text='тестовый текст',
            author=cls.user,
            group=cls.group_with_post,
            image=uploaded,
        )
        cls.follow = Follow.objects.create(
            user=cls.user_follower,
            author=cls.user,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    # Проверка, что страницы передают правильный контекст
    def test_pages_shows_correct_context(self):
        url_list = (
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group_with_post.slug},
            ),
            reverse(
                'posts:index'
            ),
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username},
            ),
        )

        def check_context(url):
            response = self.authorized_client.get(url)
            first_object = response.context['page_obj'][0]
            self.assertEqual(first_object.text, self.post.text)
            self.assertEqual(first_object.author, self.post.author)
            self.assertEqual(first_object.group, self.post.group)
            self.assertEqual(
                first_object.image, self.post.image
            )

        for url in url_list:
            with self.subTest(url=url):
                if url == reverse('posts:follow_index'):
                    self.authorized_client.force_login(self.user_follower)
                    check_context(url)
                else:
                    check_context(url)

    # Проверка, что страница post_detail передает правильный контекст
    def test_post_detail_page_show_correct_context(self):
        url = reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.id},
        )
        response = self.authorized_client.get(url)
        post_object = response.context['post']
        self.assertEqual(post_object.text, self.post.text)
        self.assertEqual(post_object.author, self.post.author)
        self.assertEqual(post_object.group, self.post.group)
        self.assertEqual(response.context['post'].image, self.post.image)

    # Проверка, что страницы передают правильный контекст
    def test_post_create_page_show_correct_context(self):
        url_list = (
            reverse('posts:post_create'),
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
        )
        for url in url_list:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertIsInstance(response.context['form'], PostForm)

    def test_edit_post(self):
        url = reverse(
            'posts:post_edit',
            kwargs={'post_id': self.post.id},
        )
        response = self.authorized_client.get(url)
        self.assertEqual(response.context['form'].instance, self.post)
        self.assertIsInstance(response.context['form'], PostForm)

    def test_author_page_show_correct_context(self):
        url = reverse(
            'posts:profile',
            kwargs={'username': self.user.username},
        )
        response = self.authorized_client.get(url)
        self.assertEqual(response.context['author'], self.user)

    def test_group_page_show_correct_context(self):
        url = reverse(
            'posts:group_list',
            kwargs={'slug': self.group_with_post.slug},
        )
        response = self.authorized_client.get(url)
        self.assertEqual(response.context['group'], self.group_with_post)

    # Проверка, что пост с группой не выводится на страницу другой группы
    def test_post_not_show_on_other_group_page(self):
        url = reverse(
            'posts:group_list',
            kwargs={'slug': self.group_without_post.slug},
        )
        response = self.authorized_client.get(url)
        self.assertNotIn(self.post, response.context['page_obj'])

    def test_cache_index(self):
        """Проверка хранения и очищения кэша для index."""
        response = self.authorized_client.get(reverse('posts:index'))
        content_before_post_create = response.content
        Post.objects.create(
            text='test_new_post',
            author=self.user,
        )
        second_response = self.authorized_client.get(reverse('posts:index'))
        content_after_post_create = second_response.content
        self.assertEqual(content_before_post_create, content_after_post_create)
        cache.clear()
        third_response = self.authorized_client.get(reverse('posts:index'))
        content_cache_cleared = third_response.content
        self.assertNotEqual(content_after_post_create, content_cache_cleared)

    def test_follow(self):
        """Проверка подписки на пользователя."""
        self.authorized_client.post(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user_follower.username}
                    ),
        )
        self.assertTrue(
            Follow.objects.filter(
                user=self.user,
                author=self.user_follower
            ).exists()
        )

    def test_unfollow(self):
        """Проверка отписки от пользователя."""
        self.authorized_client.force_login(self.user_follower)
        self.authorized_client.post(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.user.username}
                    ),
        )
        self.assertFalse(
            Follow.objects.filter(
                user=self.user_follower,
                author=self.user
            ).exists()
        )


# Проверяем работоспособность Паджинатора
class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user_follower = User.objects.create_user(username='follower')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='тестовое описание группы'
        )

        cls.POSTS_NUMBER = 13

        cls.posts = Post.objects.bulk_create(
            [
                Post(
                    text=f'Тестовые посты номер {post}',
                    author=cls.user,
                    group=cls.group
                )
                for post in range(cls.POSTS_NUMBER)
            ]
        )

        cls.follow = Follow.objects.create(
            user=cls.user_follower,
            author=cls.user,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_follower)

    # Проверяем, что страница отображает по 10 постов
    def test_pages_contain_ten_records(self):
        url_list = (
            reverse('posts:index'),
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug},
            ),
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username},
            ),
        )

        for url in url_list:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(
                    len(response.context['page_obj']),
                    settings.POSTS_ON_PAGE
                )

        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(
            len(response.context['page_obj']), settings.POSTS_ON_PAGE
        )

    # Проверяем, что "n" страница отображает нужное количество постов
    def test_n_page_contains_three_records(self):
        posts_on_n_page = f'''?page={
            (self.POSTS_NUMBER - 1)
            // settings.POSTS_ON_PAGE + 1}'''
        url_list = (
            reverse('posts:index')
            + posts_on_n_page,
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug},
            )
            + posts_on_n_page,
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username},
            )
            + posts_on_n_page,
        )

        def get_n_page_posts_number(post_number):
            return (post_number
                    - ((post_number // settings.POSTS_ON_PAGE + 1) - 1)
                    * settings.POSTS_ON_PAGE)

        for url in url_list:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(
                    len(response.context['page_obj']),
                    get_n_page_posts_number(self.POSTS_NUMBER)
                )

        self.assertEqual(
            len(
                self.authorized_client
                .get(reverse('posts:follow_index')
                     + posts_on_n_page).context['page_obj']
            ),
            get_n_page_posts_number(self.POSTS_NUMBER)
        )
