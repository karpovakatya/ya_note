import pytest

from django.urls import reverse

'''
отдельная заметка передаётся на страницу 
со списком заметок в списке object_list, в словаре context;
'''
# В тесте используем фикстуру заметки
# и фикстуру клиента с автором заметки.
def test_note_in_list_for_author(note, author_client):
    url = reverse('notes:list')
    # Запрашиваем страницу со списком заметок:
    response = author_client.get(url)
    # Получаем список объектов из контекста:
    object_list = response.context['object_list']
    # Проверяем, что заметка находится в этом списке:
    assert note in object_list


'''
в список заметок одного пользователя не попадают заметки другого пользователя;
'''
# В этом тесте тоже используем фикстуру заметки,
# но в качестве клиента используем admin_client;
# он не автор заметки, так что заметка не должна быть ему видна.
def test_note_not_in_list_for_another_user(note, admin_client):
    url = reverse('notes:list')
    response = admin_client.get(url)
    object_list = response.context['object_list']
    # Проверяем, что заметки нет в контексте страницы:
    assert note not in object_list


# дублирует первые два теста
@pytest.mark.parametrize(
    # Задаём названия для параметров:
    'parametrized_client, note_in_list',
    (
        # Передаём фикстуры в параметры при помощи "ленивых фикстур":
        (pytest.lazy_fixture('author_client'), True),
        (pytest.lazy_fixture('admin_client'), False),
    )
)
def test_notes_list_for_different_users(
        # Используем фикстуру заметки и параметры из декоратора:
        note, parametrized_client, note_in_list
):
    url = reverse('notes:list')
    # Выполняем запрос от имени параметризованного клиента:
    response = parametrized_client.get(url)
    object_list = response.context['object_list']
    # Проверяем истинность утверждения "заметка есть в списке":
    assert (note in object_list) is note_in_list


'''
Тест «есть ли форма в контексте?»
'''
# при создании заметки есть форма в контексте
def test_create_note_page_contains_form(author_client):
    url = reverse('notes:add')
    # Запрашиваем страницу создания заметки:
    response = author_client.get(url)
    # Проверяем, есть ли объект form в словаре контекста:
    assert 'form' in response.context


# В параметры теста передаём фикстуру slug_for_args и клиент с автором заметки:
# при релактировании заметки есть форма в контексте
def test_edit_note_page_contains_form(slug_for_args, author_client):
    url = reverse('notes:edit', args=slug_for_args)
    # Запрашиваем страницу редактирования заметки:
    response = author_client.get(url)
    # Проверяем, есть ли объект form в словаре контекста:
    assert 'form' in response.context

# второй вариант решения предыдущего кейса
@pytest.mark.parametrize(
    # В качестве параметров передаем name и args для reverse.
    'name, args',
    (
        # Для тестирования страницы создания заметки 
        # никакие дополнительные аргументы для reverse() не нужны.
        ('notes:add', None),
        # Для тестирования страницы редактирования заметки нужен slug заметки.
        ('notes:edit', pytest.lazy_fixture('slug_for_args'))
    )
)
def test_pages_contains_form(author_client, name, args):
    # Формируем URL.
    url = reverse(name, args=args)
    # Запрашиваем нужную страницу:
    response = author_client.get(url)
    # Проверяем, есть ли объект формы в словаре контекста:
    assert 'form' in response.context
