import os


def parse_block(block):
    result = {}
    key = ''
    block_lines = block.split('\n\n')
    for line in block_lines:
        if line.startswith('Вопрос'):
            key = line.split(':', 1)[1].strip()
        elif line.startswith('Ответ'):
            result[key] = line.split(':', 1)[1].strip()
    return result


def create_quiz(quiz_folder):

    text = ''
    for filename in os.listdir(quiz_folder):
        with open(os.path.join(quiz_folder, filename), 'r', encoding='KOI8-R') as f:
            text += f.read()

    sep_text = text.split('\n\n\n')

    quiz_desc = {}

    for block in sep_text:
        parsed_block = parse_block(block)
        quiz_desc.update(parsed_block)

    return quiz_desc
