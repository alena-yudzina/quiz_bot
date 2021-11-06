import os
from itertools import zip_longest


def chunk(lst):
    i_ = iter(lst)
    return list(zip_longest(i_, i_))


def create_quiz(quiz_folder):

    text = ''
    for filename in os.listdir(quiz_folder):
        with open(os.path.join(quiz_folder, filename), 'r', encoding='KOI8-R') as f:
            text += f.read()

    sep_text = [part for part in text.split('\n\n')]

    answers_and_questions = list(filter(lambda elem: 'Вопрос' in elem or 'Ответ:' in elem, sep_text))

    quiz_desc = [
        {
            'question': pair[0].split('\n', 1)[1],
            'answer': pair[1].split('\n', 1)[1]
        }
        for pair in chunk(answers_and_questions)
    ]

    return quiz_desc
