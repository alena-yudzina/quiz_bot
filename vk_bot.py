import os
import random
from dotenv import load_dotenv
import redis
import vk_api
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkEventType, VkLongPoll

from questions import create_quiz


def create_question(db, quiz):

    question_with_answer = random.choice(quiz)
    question = question_with_answer['question']
    full_answer = question_with_answer['answer']
    short_answer = full_answer.split('.', 1)[0]
    short_answer = short_answer.split('(', 1)[0]

    db.mset(
        {
            'question': question,
            'short_answer': short_answer,
            'full_answer': full_answer
        }
    )


def main():
    load_dotenv()

    database = redis.Redis(
        host=os.environ['REDIS_HOST'],
        port=os.environ['REDIS_PORT'],
        password=os.environ['REDIS_PASSWORD']
    )
    quiz = create_quiz()

    vk_session = vk_api.VkApi(token=os.environ['VK_TOKEN'])
    vk = vk_session.get_api()

    keyboard = VkKeyboard(one_time=True)

    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.PRIMARY)

    keyboard.add_line()
    keyboard.add_button('Мой счет', color=VkKeyboardColor.PRIMARY)

    longpoll = VkLongPoll(vk_session)
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            if event.text == 'Новый вопрос':
                create_question(database, quiz)
                vk.messages.send(
                    user_id=event.user_id,
                    message=database.get('question').decode('UTF-8'),
                    random_id=random.randint(1,1000),
                    keyboard=keyboard.get_keyboard()
                )
            if event.text == 'Сдаться':
                vk.messages.send(
                    user_id=event.user_id,
                    message=database.get('full_answer').decode('UTF-8'),
                    random_id=random.randint(1,1000),
                    keyboard=keyboard.get_keyboard()
                )
                create_question(database, quiz)
                vk.messages.send(
                    user_id=event.user_id,
                    message=database.get('question').decode('UTF-8'),
                    random_id=random.randint(1,1000),
                    keyboard=keyboard.get_keyboard()
                )
            if event.text == database.get('short_answer').decode('UTF-8'):
                vk.messages.send(
                    user_id=event.user_id,
                    message='Правильно! Поздравляю! Для следующего вопроса нажми "Новый вопрос".',
                    random_id=random.randint(1,1000),
                    keyboard=keyboard.get_keyboard()
                )
            if event.text != 'Новый вопрос' and event.text != 'Сдаться' and event.text != database.get('short_answer').decode('UTF-8'):
    
                vk.messages.send(
                    user_id=event.user_id,
                    message='Неправильно… Попробуешь ещё раз?.',
                    random_id=random.randint(1,1000),
                    keyboard=keyboard.get_keyboard()
                )


if __name__ == '__main__':
    main()
