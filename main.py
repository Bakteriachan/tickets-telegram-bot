#!/usr/bin/env python3

import os
from sys import stderr,platform
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
from button_filter import BtnFilter

logging.basicConfig(
    level = logging.INFO,format = "[ %(asctime)s ] [ %(name)s ] [ %(levelname)s ]  { %(message)s },"
)

separator = '\\' # -> windows directories separator
if platform.startswith('linux'):
    separator = '/'


curr_path = separator.join(__file__.split(separator)[:-1])
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

start_command_handler = CommandHandler('start', handlers.start)

main_conv = ConversationHandler(
    entry_points = [
        start_command_handler,
        MessageHandler(filters = BtnFilter(r'➕ Ticket'), callback = handlers.new_ticket),
        CallbackQueryHandler(callback = handlers.select_language,pattern = r'languageselect-[a-zA-Z]+'),
        CallbackQueryHandler(callback=handlers.answer_ticket,pattern=r'answer-ticket-([0-9]+)')
    ],
    states = {
        states.ADMIN : [
            start_command_handler,
            MessageHandler(filters = BtnFilter(r'➕ Ticket'), callback = handlers.new_ticket)
        ],

        states.PROCESS_TICKET : [
            start_command_handler,
            MessageHandler(BtnFilter(r'🚫 Cancel'), callback = handlers.start),
            MessageHandler(filters=Filters.all,callback = handlers.process_ticket)
        ],

        states.TICKET_CONFIRMATION : [
            start_command_handler,
            MessageHandler(BtnFilter(r'🚫 Cancel'), callback = handlers.start),
            CallbackQueryHandler(callback = handlers.ticket_confirmation,pattern=r'(confirm|cancel)-ticket')
        ],

        states.PROCESS_ANSWER : [
            start_command_handler,
            MessageHandler(BtnFilter(r'🚫 Cancel'), callback = handlers.start),
            MessageHandler(Filters.all, handlers.process_answer)
        ]

    }, fallbacks = [

        CallbackQueryHandler(callback=handlers.answer_ticket,pattern=r'answer-ticket-([0-9]+)'),

        MessageHandler(BtnFilter(r'🚫 Cancel'), callback = handlers.start)
    ]
)


dp.add_handler(main_conv)


updater.start_polling()
updater.idle()
