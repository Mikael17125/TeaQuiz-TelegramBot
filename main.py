"""
Simple Quiz Bot for Telegram
"""
import re
from datetime import datetime
import logging
from logging import debug, info
from pathlib import Path
import random
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, PicklePersistence
import yaml  # pyyaml
import numpy as np
import multiprocessing
import requests
import pandas as pd

logging.basicConfig(
    filename='conversations.log',
    format='%(asctime)s %(levelname)-7s %(name)s %(message)s')
logging.getLogger().setLevel('DEBUG')

TOKEN_FILE = 'token.txt'
TOKEN = Path(TOKEN_FILE).read_text().strip()
AUTHORIZED_USERS = ['mikaelnias', 'aizizhasyein', 'Chacam102']

DURATION = 5
class Data:
    data_ = np.empty((0,7))

class Question:

    def __init__(self, qid, question, answers, type):
        self.qid = qid
        self.text = question
        self.answers = {}
        self.type = type
        self.correct = None
        for a in answers:
            aid = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[len(self.answers)]
            if isinstance(a, str):
                self.answers[aid] = a
            elif isinstance(a, dict) and len(a) == 1 and \
                    'correct' in a and self.correct is None:
                self.answers[aid] = a['correct']
                self.correct = aid
            else:
                raise ValueError(
                    f'Incorrect answers in question {qid}: {answers}')

QUESTIONS = {q['id']: Question(q['id'], q['q'], q['a'], q['type'])
             for q in yaml.safe_load(Path('questions.yaml').read_text())}

def start(update, context):
    """Command handler for command /start"""

    msg = update.message
    user = msg.from_user
    debug(f'Quiz bot entered by user: {user.id} @{user.username} "{user.first_name} {user.last_name}"')

    if AUTHORIZED_USERS and user.username not in AUTHORIZED_USERS:
        return

    if 'username' not in context.user_data:
        context.user_data['username'] = user.username

    msg.bot.send_message(msg.chat_id,
        text=f'Mari kita mulai tes. Anda akan memiliki {DURATION} menit untuk {len (QUESTIONS)} pertanyaan. Siap?',
        reply_markup=telegram.ReplyKeyboardMarkup([['Mulai Tes']]))


def common_message(update, context):
    """General response handler"""

    msg = update.message
    user = msg.from_user
    debug(f'Message received from {user.id} @{user.username}: {msg.text}')

    if AUTHORIZED_USERS and user.username not in AUTHORIZED_USERS:
         return

    if 'quiz' not in context.user_data:

        info(f'Kuis dimulai oleh {user.id} @{user.username}')

        context.user_data['quiz'] = {}
        context.user_data['quiz']['answers'] = {}
        starttime = datetime.now()
        context.user_data['quiz']['starttime'] = starttime

        msg.bot.send_message(msg.chat_id,
            text = f'Tes dimulai pada {starttime}',
            reply_markup=telegram.ReplyKeyboardRemove())

    else:
        # save response
        context.user_data['quiz']['answers'][context.user_data['quiz']['current_qid']] = msg.text

    # ask the question

    questions_left = set(QUESTIONS) - set(context.user_data['quiz']['answers'])

    if len(questions_left) > 0:

        question = QUESTIONS[random.sample(questions_left, 1)[0]]

        if question.type == '1': #photo
            file = {'photo': open(f'file/{question.qid}.jpg', 'rb')}
            respon = requests.post(f'https://api.telegram.org/bot{TOKEN}/sendPhoto?chat_id={msg.chat_id}', files=file)
        elif question.type == '2':
            file = {'video': open(f'file/{question.qid}.mp4', 'rb')}
            respon = requests.post(f'https://api.telegram.org/bot{TOKEN}/sendVideo?chat_id={msg.chat_id}', files=file)
        elif question.type == '3':
            file = {'audio': open(f'file/{question.qid}.mp3', 'rb')}
            respon = requests.post(f'https://api.telegram.org/bot{TOKEN}/sendAudio?chat_id={msg.chat_id}', files=file)

        msg.bot.send_message(msg.chat_id,
            text=f'{question.text}\n' + \
                '\n'.join(f'{aid}. {text}' for aid, text in sorted(question.answers.items())),
            reply_markup=telegram.ReplyKeyboardMarkup([[aid for aid in sorted(question.answers)]]))
        context.user_data['quiz']['current_qid'] = question.qid

    else:

        answer = parser(context.user_data['quiz']['answers'].items())
        data_tmp = np.array([10, user.username])
        data_tmp = np.append(answer, data_tmp)
        data = np.array([data_tmp])

        Data.data_ =np.append(Data.data_, data,axis=0)
        df = pd.DataFrame(Data.data_)
        df_text = df.to_string(index=False, header=False)

        data_text_2 = re.sub('\s+', ' ', df_text).strip()
        print(data_text_2)
        archive = open('data.txt', 'w')
        archive.write(df_text)
        msg.bot.send_message(msg.chat_id,
            text=f'Ujian Selesai',
            reply_markup=telegram.ReplyKeyboardRemove())
        context.user_data['quiz']['current_qid'] = None
        print(Question.answer)

def parser(answer):
    order = dict(sorted(answer))
    data = list(order.items())
    arr = np.array(data)

    return(arr[:, 1])

def main():
    # storage = PicklePersistence(filename='data.pickle')
    updater = Updater(token=TOKEN, workers=multiprocessing.cpu_count(), use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(MessageHandler(None, common_message))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
