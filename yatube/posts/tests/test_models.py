from django.contrib.auth import get_user_model
from django.test import TestCase
from django.db import IntegrityError

from posts.models import Group, Post, Follow

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Ф' * 100,
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Ф' * 100,
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        posts_data = [
            (PostModelTest.post.text[Post.SYMBOLS_IN_STR],
                str(PostModelTest.post)),
            (PostModelTest.group.title,
                str(PostModelTest.group)),
        ]
        for value, expected in posts_data:
            with self.subTest(value=value):
                self.assertEqual(value, expected)

    def test_verbose_name_post(self):
        """Проверяем, что поля моделей Post с verbose_name."""
        post = PostModelTest.post
        field_verboses = [
            ('group', 'Группа'),
            ('text', 'Текст Поста'),
            ('author', 'Автор'),
        ]
        for value, expected in field_verboses:
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name, expected
                )

    def test_verbose_name_group(self):
        """Проверяем, что поля моделей Group с verbose_name."""
        group = PostModelTest.group
        field_verboses = [
            ('title', 'Заголовок'),
            ('slug', 'Слаг в url-строке'),
            ('description', 'Описание'),
        ]
        for value, expected in field_verboses:
            with self.subTest(value=value):
                self.assertEqual(
                    group._meta.get_field(value).verbose_name, expected
                )

    def test_help_text_post(self):
        """Проверяем, что поля моделей Post с help_text."""
        post = PostModelTest.post
        field_help_texts = [
            ('group', 'Показывает название группы'),
            ('text', 'Введите текст Поста'),
            ('author', 'Показывает автора поста'),
        ]
        for value, expected in field_help_texts:
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).help_text, expected
                )

    def test_help_text_group(self):
        """Проверяем, что поля моделей Group с help_text."""
        group = PostModelTest.group
        field_help_texts = [
            ('title', 'Укажите заголовок группы'),
            ('slug', 'Укажите название группы'),
            ('description', 'Введите описание группы'),
        ]
        for value, expected in field_help_texts:
            with self.subTest(value=value):
                self.assertEqual(
                    group._meta.get_field(value).help_text, expected
                )

    def test_no_self_follow(self):
        constraint_name = "self_follow_prevention"
        with self.assertRaisesMessage(IntegrityError, constraint_name):
            Follow.objects.create(user=self.user, author=self.user)
