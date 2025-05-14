import requests

# URL API для создания новой задачи
url = "http://127.0.0.1:5000/api/b5ebf3ed998a494a812f04a6d32ea6ae/project/3"

# Замените <user_api> на действительный API ключ пользователя
user_api = "b5ebf3ed998a494a812f04a6d32ea6ae"

# Параметры запроса (тело запроса)
task_data = {
    "name": "project1"
}

# Отправка POST-запроса
response = requests.delete(url, json=task_data)

# Проверка ответа
if response.status_code == 201:
    print("Задача успешно создана!")
    print(response.json())
else:
    print("Ошибка при создании задачи:")
    print(f"Код статуса: {response.status_code}")
    print(response.json())