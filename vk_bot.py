import os
import random
from dotenv import load_dotenv
import redis
import vk_api
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkEventType, VkLongPoll

from questions import create_quiz


def make_short_answer(answer):
    short_answer = answer.split('.', 1)[0]
    short_answer = short_answer.split('(', 1)[0]
    return short_answer


def make_vk_id(user_id):
    return ''.join(['vk_', str(user_id)])


def main():
    load_dotenv()

    database = redis.Redis(
        host=os.environ['REDIS_HOST'],
        port=os.environ['REDIS_PORT'],
        password=os.environ['REDIS_PASSWORD']
    )
    quiz = create_quiz(os.environ['QUIZ_FOLDER'])

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
                user_id = event.user_id
                vk_user_id = make_vk_id(user_id)
                random_question = random.choice(list(quiz.keys()))
                database.set(vk_user_id, random_question)
                vk.messages.send(
                    user_id=user_id,
                    message=random_question,
                    random_id=random.randint(1,1000),
                    keyboard=keyboard.get_keyboard(),
                )
            elif event.text == 'Сдаться':
                user_id = event.user_id
                vk_user_id = make_vk_id(user_id)
                question = database.get(vk_user_id).decode('UTF-8')
                answer = quiz[question]
                vk.messages.send(
                    user_id=user_id,
                    message=answer,
                    random_id=random.randint(1,1000),
                    keyboard=keyboard.get_keyboard()
                )
                random_question = random.choice(list(quiz.keys()))
                database.set(vk_user_id, random_question)
                vk.messages.send(
                    user_id=user_id,
                    message=database.get(vk_user_id).decode('UTF-8'),
                    random_id=random.randint(1,1000),
                    keyboard=keyboard.get_keyboard()
                )
            else:
                message = event.text
                user_id = event.user_id
                vk_user_id = make_vk_id(user_id)
                question = database.get(vk_user_id).decode('UTF-8')
                correct_answer = make_short_answer(quiz[question])
                if message == correct_answer:
                    vk.messages.send(
                        user_id=user_id,
                        message="Правильно! Поздравляю! "
                        "Для следующего вопроса нажми «Новый вопрос»",
                        random_id=random.randint(1,1000),
                        keyboard=keyboard.get_keyboard()
                    )
                else:
                    vk.messages.send(
                        user_id=user_id,
                        message="Неправильно... Попробуешь ещё раз?",
                        random_id=random.randint(1,1000),
                        keyboard=keyboard.get_keyboard()
                    )


if __name__ == '__main__':
    main()
