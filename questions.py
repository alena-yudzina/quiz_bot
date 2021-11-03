import re
from itertools import zip_longest


def chunk(lst):
    i_ = iter(lst)
    return list(zip_longest(i_, i_))


def create_quiz():

    with open('quiz-questions/1vs1200.txt', 'r', encoding='KOI8-R') as f:
        text = f.read()
    
    sep_text = [part for part in text.split('\n\n')]

    answers_and_questions = list(filter(lambda elem: 'Вопрос' in elem or 'Ответ' in elem, sep_text))
    quiz_desc = []
    quiz_desc = [
        {
            'question': pair[0].split('\n', 1)[1],
            'answer': pair[1].split('\n', 1)[1]
        }
        for pair in chunk(answers_and_questions)
    ]

    return quiz_desc
# print(create_quiz())