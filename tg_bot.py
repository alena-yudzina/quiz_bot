import os
import random
from functools import partial

import redis
from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (CommandHandler, ConversationHandler,
                          Filters, MessageHandler, Updater)

from questions import create_quiz


QUESTION, ANSWER = range(2)

REPLY_KEYBOARD = [['Новый вопрос', 'Сдаться'], ['Мой счет']]
MARKUP = ReplyKeyboardMarkup(REPLY_KEYBOARD, one_time_keyboard=True)


def start(update, context):

    update.message.reply_text(
        'Привет! Я телеграм бот для викторины.',
        reply_markup=MARKUP,
    )

    return QUESTION


def handle_new_question_request(update, context, db, quiz):

    user = update.message.from_user['id']
    question = random.choice(list(quiz.keys()))
    tg_user_id = 'tg_{}'.format(user)
    db.set(tg_user_id, question)

    update.message.reply_text(
        db.get(tg_user_id).decode('UTF-8'),
        reply_markup=MARKUP,
    )

    return ANSWER


def handle_solution_attempt(update, context, db, quiz):

    user = update.message.from_user['id']
    tg_user_id = 'tg_{}'.format(user)
    answer = update.message.text
    question = db.get(tg_user_id).decode('UTF-8')
    correct_answer_full = quiz[question]
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


def handle_give_up(update, context, db, quiz):

    user = update.message.from_user['id']
    tg_user_id = 'tg_{}'.format(user)
    question = db.get(tg_user_id).decode('UTF-8')
    answer = quiz[question]
    
    update.message.reply_text(
        'Правильный ответ:\n{0}'.format(answer),
        reply_markup=MARKUP,
    )

    handle_new_question_request(update, context, db, quiz)


def done(update, context):

    user_data = context.user_data

    update.message.reply_text(
        'Возвращайтесь еще!',
        reply_markup=ReplyKeyboardRemove(),
    )

    user_data.clear()
    return ConversationHandler.END


def main():

    load_dotenv()
    bot_token = os.environ['BOT_TOKEN']
    db = redis.Redis(
        host=os.environ['REDIS_HOST'],
        port=os.environ['REDIS_PORT'],
        password=os.environ['REDIS_PASSWORD']
    )
    quiz = create_quiz(os.environ['QUIZ_FOLDER'])

    updater = Updater(bot_token)

    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            QUESTION: [
                MessageHandler(Filters.regex('^Новый вопрос$'), partial(handle_new_question_request, db=db, quiz=quiz)),
            ],
            ANSWER: [
                MessageHandler(Filters.regex('^Сдаться$'), partial(handle_give_up, db=db, quiz=quiz)),
                MessageHandler(Filters.text, partial(handle_solution_attempt, db=db, quiz=quiz)),
            ],
        },
        fallbacks=[MessageHandler(Filters.regex('^Done$'), done)], 
    )

    dispatcher.add_handler(conv_handler)

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
