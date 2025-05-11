import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackContext
from data import db_session
from data.users import User

# Настройка логирования
logging.basicConfig(
    filename='bot.log',
    filemode='a',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Определяем состояния
EMAIL, PASSWORD = range(2)

async def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    await context.bot.send_message(chat_id=user_id, text="Приветствую, вам нужно авторизоваться. Пожалуйста, введите ваш email.")
    return EMAIL

async def receive_email(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    email = update.message.text

    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.email == email).first()

    if user:
        await context.bot.send_message(chat_id=user_id, text="Введите ваш пароль.")
        context.user_data['email'] = email
        return PASSWORD
    else:
        await context.bot.send_message(chat_id=user_id, text="Email не найден. Пожалуйста, попробуйте еще раз.")
        return EMAIL

async def receive_password(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    password = update.message.text
    email = context.user_data['email']

    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.email == email).first()

    if user and user.check_password(password):
        await context.bot.send_message(chat_id=user_id, text="Вы успешно авторизованы!")
        db_sess = db_session.create_session()
        user.tg_name = user_id
        db_sess.merge(user)
        db_sess.commit()
        logging.info(f"Пользователь {user_id} успешно авторизован.")
        return ConversationHandler.END
    else:
        await context.bot.send_message(chat_id=user_id, text="Неправильный пароль. Пожалуйста, попробуйте снова.")
        return PASSWORD

async def cancel(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    await context.bot.send_message(chat_id=user_id, text="Авторизация отменена.")
    return ConversationHandler.END

def run_bot(token):
    application = ApplicationBuilder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_email)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_password)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)

    # Запускаем бота
    application.run_polling()
