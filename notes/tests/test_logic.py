from pytils.translit import slugify
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()

NOTE_TITLE = 'Заголовок'
NOTE_TEXT = 'Текст заметки'
NOTE_SLUG = slugify(NOTE_TITLE)[:100]
NEW_NOTE_TEXT = 'Новый текст заметки'
NEW_NOTE_TITLE = 'Новый заголовок'
NEW_NOTE_SLUG = 'any_slug1'
DATA = {
    'title': NOTE_TITLE,
    'text': NOTE_TEXT,
    'slug': NOTE_SLUG
    }
CHANGED_DATA = {
    'title': NEW_NOTE_TITLE,
    'text': NEW_NOTE_TEXT,
    'slug': NEW_NOTE_SLUG
    }
ADD_URL = reverse('notes:add')
EDIT_URL = reverse('notes:edit', args=(NOTE_SLUG,))
DELETE_URL = reverse('notes:delete', args=(NOTE_SLUG,))
DONE_URL = reverse('notes:success')


class TestNoteCreation(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='Миша')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        # Данные для POST-запроса при создании заметки
        cls.form_data = DATA

    '''
    Анонимный пользователь не может создать заметку.
    '''
    def test_anonymous_user_cant_create_note(self):
        # Совершаем запрос от анонимного клиента, в POST-запросе отправляем
        # предварительно подготовленные данные формы с текстом заметки.
        self.client.post(ADD_URL, data=self.form_data)
        # Считаем количество заметок.
        notes_count = Note.objects.count()
        # Ожидаем, что заметок не прибавилось.
        self.assertEqual(notes_count, 0)

    '''
    Авторизованный пользователь может создать заметку.
    '''
    def test_user_can_create_note(self):
        # Совершаем запрос через авторизованный клиент.
        response = self.auth_client.post(ADD_URL, data=self.form_data)
        # Проверяем, что редиректнуло на страницу успеха.
        self.assertRedirects(response, DONE_URL)
        # Считаем количество комментариев.
        notes_count = Note.objects.count()
        # Убеждаемся, что добавилась заметка.
        self.assertEqual(notes_count, 1)
        # Получаем объект комментария из базы.
        note = Note.objects.get()
        # Проверяем, что все атрибуты заметки совпадают с ожидаемыми.
        self.assertEqual(note.text, NOTE_TEXT)
        self.assertEqual(note.title, NOTE_TITLE)
        self.assertEqual(note.author, self.user)
        self.assertEqual(note.slug, NOTE_SLUG)


class TestNoteSlugValidation(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='Миша Булгаков')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)

        # Создаем заметку:
        cls.note = Note.objects.create(
            title=NOTE_TITLE,
            text=NOTE_TEXT,
            slug=NOTE_SLUG,
            author=cls.user
            )

    '''
    Невозможно создать две заметки с одинаковым slug
    '''
    def test_user_cant_use_existing_slug(self):
        # Отправляем запрос через авторизованный клиент.
        response = self.auth_client.post(ADD_URL, data=DATA)
        # Проверяем, есть ли в ответе ошибка поля формы.
        self.assertFormError(
            response,
            form='form',
            field='slug',
            errors=NOTE_SLUG + WARNING
        )
        # Дополнительно убедимся, что заметка не создалась.
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)


class TestNoteEditDelete(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Создаём пользователя - автора заметки.
        cls.author = User.objects.create(username='Автор')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        # Создаем пользователя-читателя.
        cls.reader = User.objects.create(username='Читатель')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)

        # Создаём заметку в БД.
        cls.note = Note.objects.create(
            title=NOTE_TITLE,
            text=NOTE_TEXT,
            slug=NOTE_SLUG,
            author=cls.author)

    '''
    Авторизованный пользователь может удалять свои заметки.
    '''
    def test_author_can_delete_note(self):
        # От имени автора заметки отправляем DELETE-запрос на удаление.
        response = self.author_client.delete(DELETE_URL)
        self.assertRedirects(response, DONE_URL)
        # Считаем количество заметок в системе.
        notes_count = Note.objects.count()
        # Ожидаем ноль заметок в системе.
        self.assertEqual(notes_count, 0)

    '''
    Авторизованный пользователь может редактировать свои заметки.
    '''
    def test_author_can_edit_note(self):
        # От имени автора заметки отправляем POST-запрос на изменение.
        response = self.author_client.post(
            EDIT_URL,
            data=CHANGED_DATA)
        self.assertRedirects(response, DONE_URL)
        # Считаем количество заметок в системе.
        notes_count = Note.objects.count()
        # Ожидаем 1 заметку в системе.
        self.assertEqual(notes_count, 1)
        # Убедимся, что заметка изменилась.
        note = Note.objects.get()
        self.assertEqual(note.text, NEW_NOTE_TEXT)
        self.assertEqual(note.title, NEW_NOTE_TITLE)
        self.assertEqual(note.slug, NEW_NOTE_SLUG)
        self.assertEqual(note.author, self.author)

    '''
    Авторизованный пользователь не может удалять чужие заметки.
    '''
    def test_user_cant_delete_note_of_another_user(self):
        # Выполняем запрос на удаление от читателя.
        response = self.reader_client.delete(DELETE_URL)
        # Проверяем, что вернулась 404 ошибка.
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Убедимся, что заметка не удалилась.
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    '''
    Авторизованный пользователь не может редактировать чужие заметки.
    '''
    def test_user_cant_edit_note_of_another_author(self):
        # От имени не-автора заметки отправляем POST-запрос.
        response = self.reader_client.post(
            EDIT_URL,
            data=CHANGED_DATA)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Убедимся, что заметка не изменилась.
        note = Note.objects.get()
        self.assertEqual(note.text, NOTE_TEXT)
        self.assertEqual(note.title, NOTE_TITLE)
        self.assertEqual(note.slug, NOTE_SLUG)
        self.assertEqual(note.author, self.author)
