from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestNotesList(TestCase):
    LIST_URL = reverse('notes:list')
    NOTES_COUNT = 12

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Миша Булгаков')

        Note.objects.bulk_create(
            Note(title=f'Заголовок {index}',
                 text='Текст заметки',
                 slug=f'slug-{index}',
                 author=cls.author
                 )
            for index in range(cls.NOTES_COUNT)
        )

    '''
    Тестируем количество заметок на странице списка авторизованного автора:
    отображаются все созданные заметки
    '''
    def test_notes_count(self):
        self.client.force_login(self.author)
        # Загружаем страницу со списком заметок.
        response = self.client.get(self.LIST_URL)
        object_list = response.context['object_list']
        notes_count = len(object_list)
        self.assertEqual(response.status_code, 200)
        # Проверяем, что на странице есть все созданные заметки.
        self.assertEqual(notes_count, self.NOTES_COUNT)

    '''
    Тестируем сортировку заметок на странице списка заметок:
    порядок отображения от первой к последней заметке по id.
    '''
    def test_notes_order(self):
        self.client.force_login(self.author)
        response = self.client.get(self.LIST_URL)
        object_list = response.context['object_list']
        # Получаем id заметок в том порядке, как они выведены на странице.
        note_idx = [note.id for note in object_list]
        sorted_idx = sorted(note_idx)
        # Проверяем, что исходный список был отсортирован правильно.
        self.assertEqual(note_idx, sorted_idx)


class TestCreateNote(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Сохраняем в переменную адрес страницы с формой создания заметки:
        cls.add_url = reverse('notes:add')
        cls.author = User.objects.create(username='Миша Булгаков')

        # Создаем заметку:
        cls.note = Note.objects.create(
            title='Заголовок заметки',
            text='Текст заметки',
            slug='any_slug',
            author=cls.author
            )

    '''
    Тестируем наличие формы создания заметки в словаре контекста.
    '''
    def test_authorized_client_has_form(self):
        self.client.force_login(self.author)
        response = self.client.get(self.add_url)
        self.assertIn('form', response.context)


'''
отдельная заметка передаётся на страницу со списком заметок 
в списке object_list, в словаре context;
'''

'''
в список заметок одного пользователя не попадают заметки другого пользователя
'''