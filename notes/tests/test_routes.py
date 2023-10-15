from http import HTTPStatus

# Импортируем функцию для определения модели пользователя.
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

# Импортируем класс модели новостей.
from notes.models import Note

# Получаем модель пользователя.
User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Создаём двух пользователей (автор/не автор):
        cls.author = User.objects.create(username='Миша Булгаков')
        cls.reader = User.objects.create(username='Варвара Л.')

        # Создаем заметку:
        cls.note = Note.objects.create(
            title='Заголовок заметки',
            text='Текст заметки',
            slug='any_slug',
            author=cls.author
            )

    '''
    Анонимному пользователю доступны страницы:
    главная, страницы регистрации, входа и выхода.
    '''
    def test_pages_availability(self):
        urls = ('notes:home',  # главная
                'users:signup',  # регистрация
                'users:login',  # вход
                'users:logout',  # выход
                )

        for page in urls:
            with self.subTest(page=page):
                url = reverse(page)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    '''
    Пользователь авторизован.
    Проверяем доступность заметок для автора
    и недоступность для не-автора (ошибка 404).
    '''
    def test_availability_for_author(self):
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.NOT_FOUND),
        )
        pages = (
            'notes:detail',  # просмотр заметки
            'notes:edit',  # редактирование заметки
            'notes:delete',  # удаление заметки
            )

        for user, status in users_statuses:
            self.client.force_login(user)

            for page in pages:
                with self.subTest(user=user, page=page):
                    url = reverse(page, args=(self.note.slug,))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    '''
    Проверяем редирект на страницу логина для анонимного пользователя
    при попытке открыть страницу создания/просмотра/удаления/редактирования
    заметки, списка заметок.
    '''
    def test_redirect_for_anonymous_client(self):
        login_url = reverse('users:login')
        slug = (self.note.slug,)
        # Адреса, с которых редиректим:
        pages = (
            ('notes:list', None),  # просмотр списка заметок
            ('notes:add', None),  # добавление заметки
            ('notes:success', None),  # страница успешного добавления записи
            ('notes:detail', slug),  # просмотр заметки
            ('notes:edit', slug),  # редактирование заметки
            ('notes:delete', slug)  # удаление заметки
            )

        for page, args in pages:
            with self.subTest(page=page):
                url = reverse(page, args=args)
                redirect_url = f'{login_url}?next={url}'  # ОР
                response = self.client.get(url)  # ФР
                self.assertRedirects(response, redirect_url)

    def test_pages_availability_for_auth_user(self):
        """Аутентифицированному пользователю доступна:

        страница со списком заметок notes/,
        страница добавления новой заметки add/,
        страница успешного добавления заметки done/."""

        urls = ('notes:list',
                'notes:add',
                'notes:success'
                )

        self.client.force_login(self.author)

        for page in urls:
            with self.subTest(page=page):
                url = reverse(page)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
