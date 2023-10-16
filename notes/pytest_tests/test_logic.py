import pytest

from http import HTTPStatus

# Дополнительно импортируем функцию slugify.
from pytils.translit import slugify

from pytest_django.asserts import assertRedirects, assertFormError
from django.urls import reverse

from notes.models import Note
from notes.forms import WARNING


# Указываем фикстуру form_data в параметрах теста.
def test_user_can_create_note(author_client, author, form_data):
    """Залогиненный пользователь может создать заметку"""

    url = reverse('notes:add')
    # В POST-запросе отправляем данные, полученные из фикстуры form_data:
    response = author_client.post(url, data=form_data)
    # Проверяем, что был выполнен редирект на страницу успешного добавления заметки:
    assertRedirects(response, reverse('notes:success'))
    # Считаем общее количество заметок в БД, ожидаем 1 заметку.
    assert Note.objects.count() == 1
    # Чтобы проверить значения полей заметки -
    # получаем её из базы при помощи метода get():
    new_note = Note.objects.get()
    # Сверяем атрибуты объекта с ожидаемыми.
    assert new_note.title == form_data['title']
    assert new_note.text == form_data['text']
    assert new_note.slug == form_data['slug']
    assert new_note.author == author



# Добавляем маркер, который обеспечит доступ к базе данных:
@pytest.mark.django_db
def test_anonymous_user_cant_create_note(client, form_data):
    """Анонимный пользователь не может создать заметку"""

    url = reverse('notes:add')
    # Через анонимный клиент пытаемся создать заметку:
    response = client.post(url, data=form_data)
    login_url = reverse('users:login')
    expected_url = f'{login_url}?next={url}'
    # Проверяем, что произошла переадресация на страницу логина:
    assertRedirects(response, expected_url)
    # Считаем количество заметок в БД, ожидаем 0 заметок.
    assert Note.objects.count() == 0


# Вызываем фикстуру отдельной заметки, чтобы в базе появилась запись.
def test_not_unique_slug(author_client, note, form_data):
    """Невозможно создать две заметки с одинаковым slug."""

    url = reverse('notes:add')
    # Подменяем slug новой заметки на slug уже существующей записи:
    form_data['slug'] = note.slug
    # Пытаемся создать новую заметку:
    response = author_client.post(url, data=form_data)
    # Проверяем, что в ответе содержится ошибка формы для поля slug:
    assertFormError(response, 'form', 'slug', errors=(note.slug + WARNING))
    # Убеждаемся, что количество заметок в базе осталось равным 1:
    assert Note.objects.count() == 1


def test_empty_slug(author_client, form_data):
    """Слаг формируется автоматически, если не указан"""

    url = reverse('notes:add')
    # Убираем поле slug из словаря:
    form_data.pop('slug')
    response = author_client.post(url, data=form_data)
    # Проверяем, что даже без slug заметка была создана:
    assertRedirects(response, reverse('notes:success'))
    assert Note.objects.count() == 1
    # Получаем созданную заметку из базы:
    new_note = Note.objects.get()
    # Формируем ожидаемый slug:
    expected_slug = slugify(form_data['title'])
    # Проверяем, что slug заметки соответствует ожидаемому:
    assert new_note.slug == expected_slug


# В параметрах вызвана фикстура note: значит, в БД создана заметка.
def test_author_can_edit_note(author_client, form_data, note):
    """Пользователь может редактировать свои заметки"""

    # Получаем адрес страницы редактирования заметки:
    url = reverse('notes:edit', args=(note.slug,))
    # В POST-запросе на адрес редактирования заметки
    # отправляем form_data - новые значения для полей заметки:
    response = author_client.post(url, form_data)
    # Проверяем редирект:
    assertRedirects(response, reverse('notes:success'))
    # Обновляем объект заметки note: получаем обновлённые данные из БД:
    note.refresh_from_db()
    # Проверяем, что атрибуты заметки соответствуют обновлённым:
    assert note.title == form_data['title']
    assert note.text == form_data['text']
    assert note.slug == form_data['slug']


def test_other_user_cant_edit_note(admin_client, form_data, note):
    """Пользователь не может редактировать чужие заметки"""

    url = reverse('notes:edit', args=(note.slug,))
    response = admin_client.post(url, form_data)
    # Проверяем, что страница не найдена:
    assert response.status_code == HTTPStatus.NOT_FOUND
    # Получаем новый объект запросом из БД.
    note_from_db = Note.objects.get(id=note.id)
    # Проверяем, что атрибуты объекта из БД равны атрибутам заметки до запроса.
    assert note.title == note_from_db.title
    assert note.text == note_from_db.text
    assert note.slug == note_from_db.slug


def test_author_can_delete_note(author_client, slug_for_args):
    """Пользователь может удалять свои заметки"""

    url = reverse('notes:delete', args=slug_for_args)
    response = author_client.post(url)
    assertRedirects(response, reverse('notes:success'))
    assert Note.objects.count() == 0


def test_other_user_cant_delete_note(admin_client, form_data, slug_for_args):
    """Пользователь не может удалять чужие заметки"""

    url = reverse('notes:delete', args=slug_for_args)
    response = admin_client.post(url)
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert Note.objects.count() == 1