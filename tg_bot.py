import os
import random

import redis
from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (CallbackContext, CommandHandler, ConversationHandler,
                          Filters, MessageHandler, Updater)

from questions import create_quiz


QUESTION, ANSWER = range(2)

REPLY_KEYBOARD = [['Новый вопрос', 'Сдаться'], ['Мой счет']]
MARKUP = ReplyKeyboardMarkup(REPLY_KEYBOARD, one_time_keyboard=True)


def start(update: Update, context: CallbackContext) -> int:
    
    context.bot_data['db'] = redis.Redis(
        host=os.environ['REDIS_HOST'],
        port=os.environ['REDIS_PORT'],
        password=os.environ['REDIS_PASSWORD']
    )

    context.bot_data['quiz'] = create_quiz(os.environ['QUIZ_FOLDER'])

    update.message.reply_text(
        'Привет! Я телеграм бот для викторины.',
        reply_markup=MARKUP,
    )

    return QUESTION


def handle_new_question_request(update: Update, context: CallbackContext) -> int:

    user = update.message.from_user['id']
    quiz = context.bot_data['quiz']
    question = random.choice(list(quiz.keys()))
    
    db = context.bot_data['db']
    db.set(user, question)

    update.message.reply_text(
        db.get(user).decode('UTF-8'),
        reply_markup=MARKUP,
    )

    return ANSWER


def handle_solution_attempt(update: Update, context: CallbackContext) -> int:

    user = update.message.from_user['id']
    answer = update.message.text

    db = context.bot_data['db']
    question = db.get(user).decode('UTF-8')
    correct_answer_full = context.bot_data['quiz'][question]
    correct_answer_short = correct_answer_full.split('.', 1)[0]
    correct_answer_short = correct_answer_short.split('(', 1)[0]

    if answer.lower() ==  correct_answer_short.lower():
        update.message.reply_text(
            'Правильно! Поздравляю! Для следующего вопроса нажми "Новый вопрос".',
            reply_markup=MARKUP,
        )
        return QUESTION
    else:
        update.message.reply_text(
            'Неправильно… Попробуешь ещё раз?',
            reply_markup=MARKUP,
        )
        return ANSWER


def handle_give_up(update: Update, context: CallbackContext) -> int:

    user = update.message.from_user['id']
    db = context.bot_data['db']
    question = db.get(user).decode('UTF-8')
    answer = context.bot_data['quiz'][question]
    update.message.reply_text(
        'Правильный ответ:\n{0}'.format(answer),
        reply_markup=MARKUP,
    )

    handle_new_question_request(update, context)


def done(update: Update, context: CallbackContext) -> int:

    user_data = context.user_data

    update.message.reply_text(
        'Возвращайтесь еще!',
        reply_markup=ReplyKeyboardRemove(),
    )

    user_data.clear()
    return ConversationHandler.END


def main() -> None:

    load_dotenv()
    bot_token = os.environ['BOT_TOKEN']

    updater = Updater(bot_token)

    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            QUESTION: [
                MessageHandler(Filters.regex('^Новый вопрос$'), handle_new_question_request),
            ],
            ANSWER: [
                MessageHandler(Filters.regex('^Сдаться$'), handle_give_up),
                MessageHandler(Filters.text, handle_solution_attempt),
            ],
        },
        fallbacks=[MessageHandler(Filters.regex('^Done$'), done)], 
    )

    dispatcher.add_handler(conv_handler)

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
