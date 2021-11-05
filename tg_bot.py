import os
import random

import redis
from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (CallbackContext, CommandHandler, ConversationHandler,
                          Filters, MessageHandler, Updater)

from questions import create_quiz


QUESTION, ANSWER = range(2)

reply_keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счет']]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)


def start(update: Update, context: CallbackContext) -> int:
    
    context.bot_data['db'] = redis.Redis(
        host=os.environ['REDIS_HOST'],
        port=os.environ['REDIS_PORT'],
        password=os.environ['REDIS_PASSWORD']
    )

    context.bot_data['quiz'] = create_quiz()

    update.message.reply_text(
        'Привет! Я телеграм бот для викторины.',
        reply_markup=markup,
    )

    return QUESTION


def handle_new_question_request(update: Update, context: CallbackContext) -> int:

    quiz = context.bot_data['quiz']
    question_with_answer = random.choice(quiz)
    question = question_with_answer['question']
    full_answer = question_with_answer['answer']
    short_answer = full_answer.split('.', 1)[0]
    short_answer = short_answer.split('(', 1)[0]
    db = context.bot_data['db']
    db.mset(
        {
            'question': question,
            'short_answer': short_answer,
            'full_answer': full_answer
        }
    )

    update.message.reply_text(
        db.get('question').decode('UTF-8'),
        reply_markup=markup,
    )
    print(db.get('full_answer').decode('UTF-8'))

    return ANSWER


def handle_solution_attempt(update: Update, context: CallbackContext) -> int:

    answer = update.message.text
    db = context.bot_data['db']
    if answer.lower() == db.get('short_answer').decode('UTF-8').lower():
        update.message.reply_text(
            'Правильно! Поздравляю! Для следующего вопроса нажми "Новый вопрос".',
            reply_markup=markup,
        )
        return QUESTION
    else:
        update.message.reply_text(
            'Неправильно… Попробуешь ещё раз?.',
            reply_markup=markup,
        )
        return ANSWER


def handle_give_up(update: Update, context: CallbackContext) -> int:

    db = context.bot_data['db']
    answer = db.get('full_answer').decode('UTF-8')
    update.message.reply_text(
        'Правильный ответ:\n{0}'.format(answer),
        reply_markup=markup,
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
