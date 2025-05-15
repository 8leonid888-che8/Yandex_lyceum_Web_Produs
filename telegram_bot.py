import logging
import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ConversationHandler, CallbackContext
)

from data import db_session
from data.users import User
from Config import api_bot
import asyncio
from datetime import datetime
from data.tasks import Task

EMAIL, PASSWORD, PROJECT_NAME, TASK_ID_FOR_DELETE, PROJECT_ID_FOR_DELETE = range(5)

logging.basicConfig(
    filename='bot.log',
    filemode='a',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

API_URL = "http://localhost:5000/api"


async def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    await context.bot.send_message(chat_id=user_id, text="Введите ваш email:")
    return EMAIL


async def receive_email(update: Update, context: CallbackContext):
    email = update.message.text
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.email == email).first()

    if user:
        context.user_data['email'] = email
        await update.message.reply_text("Введите пароль:")
        return PASSWORD
    else:
        await update.message.reply_text("Email не найден. Попробуйте снова:")
        return EMAIL


async def receive_password(update: Update, context: CallbackContext):
    password = update.message.text
    email = context.user_data['email']
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.email == email).first()

    if user and user.check_password(password):
        user.tg_name = update.effective_user.id
        db_sess.merge(user)
        db_sess.commit()
        context.user_data['api_key'] = user.api
        await update.message.reply_text("Вы успешно авторизованы!")
        return ConversationHandler.END
    else:
        await update.message.reply_text("Неверный пароль. Повторите попытку:")
        return PASSWORD


async def cancel(update: Update, context: CallbackContext):
    await update.message.reply_text("Авторизация отменена.")
    return ConversationHandler.END


# --- API команды --- #

async def get_all_tasks(update: Update, context: CallbackContext):
    api_key = context.user_data.get("api_key")
    if not api_key:
        await update.message.reply_text("Сначала авторизуйтесь командой /start.")
        return
    response = requests.get(f"{API_URL}/{api_key}/task/all/")
    if response.ok:
        data = response.json()
        message = "\n\n".join(
            [f"{t['id']}. {t['name']} - {'✅' if t['completed'] else '❌'}" for t in data.get("all task", [])]
        ) or "Задачи не найдены."
        await update.message.reply_text(message)
    else:
        await update.message.reply_text("Ошибка получения задач.")


async def get_today_tasks(update: Update, context: CallbackContext):
    api_key = context.user_data.get("api_key")
    if not api_key:
        await update.message.reply_text("Сначала авторизуйтесь командой /start.")
        return
    response = requests.get(f"{API_URL}/{api_key}/task/today/")
    print(response.json())
    if response.ok:
        data = response.json()
        message = "\n\n".join(
            [f"{t['id']}. {t['name']} - {'✅' if t['completed'] else '❌'}" for t in data.get("today task", [])]
        ) or "Задачи не найдены."
        await update.message.reply_text(message)
    else:
        await update.message.reply_text("Ошибка получения задач.")


async def get_projects(update: Update, context: CallbackContext):
    api_key = context.user_data.get("api_key")
    if not api_key:
        await update.message.reply_text("Сначала авторизуйтесь командой /start.")
        return

    response = requests.get(f"{API_URL}/{api_key}/project/all/")
    if response.ok:
        data = response.json()
        message = "\n".join(
            [f"{p['id']}. {p['name']}" for p in data.get("all project", [])]
        ) or "Проекты не найдены."
        await update.message.reply_text(message)
    else:
        await update.message.reply_text("Ошибка получения проектов.")


async def request_project_name(update: Update, context: CallbackContext):
    api_key = context.user_data.get("api_key")
    if not api_key:
        await update.message.reply_text("Сначала авторизуйтесь командой /start.")
        return ConversationHandler.END

    response = requests.get(f"{API_URL}/{api_key}/project/all/")
    if response.ok:
        data = response.json()
        projects = data.get("all project", [])
        message = "Введите название проекта из списка:\n" + "\n".join([p['name'] for p in projects])
        context.user_data['projects'] = projects  # сохраняем список проектов
        await update.message.reply_text(message)
        return PROJECT_NAME
    else:
        await update.message.reply_text("Ошибка получения проектов.")
        return ConversationHandler.END


async def handle_project_name(update: Update, context: CallbackContext):
    project_name = update.message.text
    api_key = context.user_data.get("api_key")
    projects = context.user_data.get("projects", [])

    matched_project = next((p for p in projects if p["name"].lower() == project_name.lower()), None)

    if not matched_project:
        await update.message.reply_text("Проект не найден. Попробуйте снова.")
        return PROJECT_NAME

    project_id = matched_project["id"]
    print("project_id", project_id)

    response = requests.get(f"{API_URL}/{api_key}/task/tasks_from_project/{project_id}/")
    if response.ok:
        data = response.json()
        tasks = data.get("project task", [])
        message = "\n".join(
            [f"{t['id']}. {t['name']} - {'✅' if t['completed'] else '❌'}" for t in tasks]) or "Задачи не найдены."
        await update.message.reply_text(f"Задачи проекта {project_name}:\n" + message)
    else:
        await update.message.reply_text("Ошибка получения задач проекта.")

    return ConversationHandler.END


async def reminder_loop(application):
    while True:
        db_sess = db_session.create_session()
        now_str = datetime.now().strftime("%Y-%m-%dT%H:%M")
        tasks = db_sess.query(Task).filter(Task.reminders != None).all()

        for task in tasks:
            if now_str in task.reminders:
                user = task.user
                if user.tg_name:
                    try:
                        await application.bot.send_message(
                            chat_id=user.tg_name,
                            text=f"🔔 Напоминание: задача '{task.name}'"
                        )
                    except Exception as e:
                        logging.error(f"Не удалось отправить напоминание пользователю {user.id}: {e}")

        await asyncio.sleep(60)


async def request_task_id(update: Update, context: CallbackContext):
    api_key = context.user_data.get("api_key")
    if not api_key:
        await update.message.reply_text("Сначала авторизуйтесь командой /start.")
        return ConversationHandler.END

    await update.message.reply_text("Введите ID задачи, которую хотите удалить:")
    return TASK_ID_FOR_DELETE


async def delete_task_by_id(update: Update, context: CallbackContext):
    task_id = update.message.text
    api_key = context.user_data.get("api_key")

    if not task_id.isdigit():
        await update.message.reply_text("ID задачи должен быть числом. Попробуйте снова.")
        return TASK_ID_FOR_DELETE

    response = requests.delete(f"{API_URL}/{api_key}/task/{task_id}/")
    if response.ok:
        await update.message.reply_text(f"Задача с ID {task_id} успешно удалена.")
    else:
        await update.message.reply_text(f"Ошибка удаления задачи. Возможно, она не существует.")

    return ConversationHandler.END


async def request_project_id(update: Update, context: CallbackContext):
    api_key = context.user_data.get("api_key")
    if not api_key:
        await update.message.reply_text("Сначала авторизуйтесь командой /start.")
        return ConversationHandler.END

    await update.message.reply_text("Введите ID проекта, который хотите удалить:")
    return PROJECT_ID_FOR_DELETE


async def delete_project_by_id(update: Update, context: CallbackContext):
    project_id = update.message.text
    api_key = context.user_data.get("api_key")

    if not project_id.isdigit():
        await update.message.reply_text("ID проекта должен быть числом. Попробуйте снова.")
        return PROJECT_ID_FOR_DELETE

    response = requests.delete(f"{API_URL}/{api_key}/project/{project_id}/")
    if response.ok:
        await update.message.reply_text(f"Проект с ID {project_id} успешно удалён.")
    else:
        await update.message.reply_text("Ошибка удаления проекта. Возможно, он не существует.")

    return ConversationHandler.END


def main():
    db_session.global_init("db/produs.db")

    application = ApplicationBuilder().token(api_bot).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={

            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_email)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_password)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],

    )
    project_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('tasks_from_project', request_project_name)],
        states={

            PROJECT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_project_name)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    delete_task_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('delete_task', request_task_id)],
        states={

            TASK_ID_FOR_DELETE: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_task_by_id)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    delete_project_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('delete_project', request_project_id)],
        states={

            PROJECT_ID_FOR_DELETE: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_project_by_id)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('all_tasks', get_all_tasks))
    application.add_handler(CommandHandler('today_tasks', get_today_tasks))
    application.add_handler(CommandHandler('projects', get_projects))

    application.add_handler(project_conv_handler)

    application.add_handler(delete_task_conv_handler)

    application.add_handler(delete_project_conv_handler)

    application.job_queue.run_repeating(lambda ctx: asyncio.create_task(reminder_loop(application)), interval=60,
                                        first=0)
    application.run_polling()


if __name__ == "__main__":
    main()
