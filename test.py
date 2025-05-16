import requests

# URL API для создания новой задачи
url = "http://127.0.0.1:5000/api/cb2b752c60db606be524b2a7977c1c9b/task/today"

# Замените <user_api> на действительный API ключ пользователя
user_api = "cb2b752c60db606be524b2a7977c1c9b"

# Параметры запроса (тело запроса)
task_data = {
    "name": "project1"
}

# Отправка POST-запроса
response = requests.get(url)

# Проверка ответа
if response.status_code == 201:
    print("Задача успешно создана!")
    print(response.json())
else:
    print("Ошибка при создании задачи:")
    print(f"Код статуса: {response.status_code}")
    print(response.json())