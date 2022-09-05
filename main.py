#!/usr/bin/env python3

import os
from sys import stderr
import logging

from telegram import Bot
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    PicklePersistence,
    MessageHandler,
    ConversationHandler,
    Filters
)
from env_loader import load_env

import handlers
import states

logging.basicConfig(
    level = logging.INFO,format = "[ %(asctime)s ] [ %(name)s ] [ %(levelname)s ]  { %(message)s },"
)

curr_path =  os.getcwd()

env = load_env(curr_path)

if os.getenv('TOKEN',None) is None:
    print('TOKEN environment varible not specified',file=stderr)
    exit(1)

if os.getenv('owner',None) is None:
    print('`owner` environment variable not specified',file=stderr)
    exit(1)

my_bot = Bot(token = os.getenv('TOKEN'))

try:
    my_bot.get_chat(chat_id = os.getenv('owner'))
except Exception:
    print(f'{os.getenv("owner")} has not started the bot',file=stderr)
    exit(1)

pick_persistance = PicklePersistence('support_persistance',store_bot_data=False,store_chat_data=False)

updater = Updater(token=my_bot.token,use_context=True,persistence=pick_persistance)
dp = updater.dispatcher

start_command_handler = CommandHandler('start', handlers.start_command_handlers)

main_conv = ConversationHandler(
    entry_points = [
        start_command_handler,
        CallbackQueryHandler(callback = handlers.new_ticket,pattern = 'open-ticket'),
        CallbackQueryHandler(callback = handlers.select_language,pattern = r'languageselect-[a-zA-Z]+')
    ],
    states = {
        states.ADMIN : [
            start_command_handler
        ],

        states.PROCESS_TICKET : [
            start_command_handler,
            MessageHandler(filters=Filters.text,callback = handlers.process_ticket)
        ],

        states.TICKET_CONFIRMATION : [
            start_command_handler,
            CallbackQueryHandler(callback = handlers.ticket_confirmation,pattern=r'(confirm|cancel)-ticket')
        ],

        states.PROCESS_ANSWER : [
            start_command_handler,
            MessageHandler(Filters.all, handlers.process_answer)
        ]

    }, fallbacks = [

        CallbackQueryHandler(callback=handlers.answer_ticket,pattern=r'answer-ticket-([0-9]+)'),

    ]
)


dp.add_handler(main_conv)


updater.start_polling()
updater.idle()
