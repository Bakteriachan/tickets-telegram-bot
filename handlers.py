import os
import re

from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      ReplyKeyboardMarkup, ReplyKeyboardRemove, Update)
from telegram.ext import CallbackContext

import config
import states
from helpers import parse


def start(update:Update,ctxt:CallbackContext):
    messages = {
        'owner' : {
            'welcome' : 'ℹ️ *Main menu\\.*'
        },
        'guest' : {
            'language' : 'Please select a language\\.',
            'main-menu' : 'ℹ️ *Main menu\\.*'
        },
        'operation-canceled' : '✔️ *Operation canceled\\.*'
    }

    if ctxt.user_data.get('confirm-ticket',None) is not None:
        try:
            ctxt.bot.delete_message(
                chat_id = update.effective_chat.id,
                message_id = ctxt.user_data.get('confirm-ticket').message_id
            )
            ctxt.user_data.pop('confirm-ticket',None)
            update.effective_chat.send_message(
                text = messages.get('operation-canceled'),
                parse_mode = config.PARSEMODE
            )
        except Exception:
            pass

    if update.effective_user.id in (int(os.getenv('owner')),):
        keyboard = [['➕ Ticket']]
        update.effective_chat.send_message(
            text = messages.get('owner').get('welcome'),
            reply_markup = ReplyKeyboardMarkup(keyboard,resize_keyboard=True),
            parse_mode = config.PARSEMODE
        )
        return states.ADMIN
    else:
        if ctxt.user_data.get('language',None) is None:
            inline_keyboard = [
                [
                    InlineKeyboardButton(
                        text = '🇺🇸 English',
                        callback_data = 'languageselect-en'
                    )
                ]
            ]
            update.effective_chat.send_message(
                text = messages.get('guest').get('language'),
                reply_markup = InlineKeyboardMarkup(inline_keyboard),
                parse_mode = config.PARSEMODE
            )
            return -1
        else: 
            keyboard = [
                ['➕ Ticket']
            ]

            update.effective_chat.send_message(
                text = messages.get('guest').get('main-menu'),
                reply_markup = ReplyKeyboardMarkup(keyboard,resize_keyboard=True),
                parse_mode = config.PARSEMODE
            )
            return -1

def select_language(update:Update,ctxt:CallbackContext):
    if update.callback_query is None:
        return None
    
    messages = {
        'main-menu' : 'ℹ️ *Main menu\\.*'
    }

    match = re.match(r'languageselect-([a-zA-Z]+)',update.callback_query.data)
    if match.group(1) in ('en',):
        ctxt.user_data['language'] = 'en'
        
    update.callback_query.answer()
    try:
        update.callback_query.delete_message()
    except Exception: # -> if could not delete message
        pass

    keyboard = [
        ['➕ Ticket']
    ]

    update.effective_chat.send_message(
        text = messages.get('main-menu'),
        reply_markup = ReplyKeyboardMarkup(keyboard,resize_keyboard=True),
        parse_mode = config.PARSEMODE
    )

def new_ticket(update:Update,ctxt:CallbackContext):
    if update.message.text is None:
        return -1

    messages = {
        'ticket-request' : '❇️ *Enter the message you want to send to the administration\\.*'
    }

    try:
        update.callback_query.delete_message()
    except Exception:
        pass

    keyboard = [
        ['🚫 Cancel']
    ]
    update.effective_chat.send_message(
        text = messages.get('ticket-request'),
        reply_markup = ReplyKeyboardMarkup(keyboard,resize_keyboard=True),
        parse_mode = config.PARSEMODE
    )


    return states.PROCESS_TICKET

def process_ticket(update:Update,ctxt:CallbackContext):

    if update.message.text is not None:
        ctxt.user_data['ticket'] = update.message.text
    else:
        ctxt.user_data['ticket'] = update.effective_message.message_id

    messages = {
        'confirm' : "ℹ️ *New message\\.*\n\n*Press \"🚫 Cancel\" if you don't agree\\.*",
        'processing' : "Processing..."
    }

    inline_keyboard = [
        [
            InlineKeyboardButton(
                text = '✅ Confirm',
                callback_data = 'confirm-ticket'
            ),
            InlineKeyboardButton(
                text = '🚫 Cancel',
                callback_data = 'cancel-ticket'
            )
        ]
    ]

    ctxt.bot.delete_message(
        chat_id = update.effective_chat.id,
        message_id = update.effective_chat.send_message(
            text = messages.get('processing'),
            reply_markup = ReplyKeyboardRemove()
        ).message_id
    )

    ctxt.user_data['confirm-ticket'] = update.effective_chat.send_message(
        text = messages.get('confirm'),
        parse_mode = config.PARSEMODE,
        reply_markup = InlineKeyboardMarkup(inline_keyboard)
    )

    return states.TICKET_CONFIRMATION


def ticket_confirmation(update:Update,ctxt:CallbackContext):
    if update.callback_query is None:
        return -1
    if ctxt.user_data.get('ticket',None) is None:
        return -1

    match = re.match(r'(confirm|cancel)-ticket', update.callback_query.data)

    ctxt.user_data.pop('confirm-ticket',None)


    messages = {
        'error' : "Something went wrong\\. Please try again\\.",
        'owner-message' : 'ℹ️ *New ticket\\.*\n\nUser ID: `{user_id}`\nUsername: \\@{username}\n\n✉️ *Message:*\n{message}',
        'owner-message-multimedia' : 'ℹ️ *New ticket\\.*\n\nUser ID: `{user_id}`\nUsername: \\@{username}\n\n✉️ *Message:*',
        'succesfuly-sent' : '✔️ *Message sent\\.*',
        'succesfuly-canceled' : '✖️ *Message canceled\\.*'
    }

    if match.group(1) in ('confirm',):
        try:
            update.callback_query.delete_message()
        except Exception:
            pass

        username = update.effective_user.username
        if username is None:
            username = '-'
        

        inline_keyboard = [
            [
                InlineKeyboardButton(
                    text = 'Answer',
                    callback_data = f'answer-ticket-{update.effective_chat.id}'
                )
            ]
        ]

        message_text: str
        if isinstance(ctxt.user_data.get('ticket'),int):
            message_text = messages.get('owner-message-multimedia').format(
                user_id = update.effective_user.id,
                username = parse(update.effective_user.username)
            )
        else:
            message_text =  messages.get('owner-message').format(
                user_id = parse(update.effective_user.id),
                username = parse(username),
                message = parse(ctxt.user_data.get('ticket'))
            )

        if ctxt.bot.send_message(
            chat_id = os.getenv('owner'),
            text = message_text,
            reply_markup = InlineKeyboardMarkup(inline_keyboard),
            parse_mode = config.PARSEMODE,
            
        ):
            if isinstance(ctxt.user_data.get('ticket'),int):
                update.effective_chat.copy_message(
                    chat_id = os.getenv('owner'),
                    message_id = ctxt.user_data.get('ticket')
                )

            keyboard = [['➕ Ticket']]
            update.effective_chat.send_message(
                text = messages.get('succesfuly-sent'),
                parse_mode = config.PARSEMODE,
                reply_markup = ReplyKeyboardMarkup(keyboard,resize_keyboard=True)
            )
        else:
            keyboard = [['➕ Ticket']]
            update.effective_chat.send_message(
                text = messages.get('error'),
                parse_mode = config.PARSEMODE,
                reply_markup = ReplyKeyboardMarkup(keyboard,resize_keyboard=True)
            )
        ctxt.user_data.pop('ticket',None)
        return -1
    else:
        try:
            update.callback_query.delete_message()
        except Exception:
            pass
        update.effective_chat.send_message(
            text = messages.get('succesfuly-canceled'),
            parse_mode = config.PARSEMODE
        )
        return -1
    

def answer_ticket(update:Update,ctxt:CallbackContext):
    if update.callback_query is None:
        return None
    if update.effective_user.id not in (int(os.getenv('owner')),):
        return None
    
    match = re.match(r'answer-ticket-([0-9]+)', update.callback_query.data)

    requester_id = match.group(1)
    ctxt.user_data['requester_id'] = requester_id

    messages = {
        'answer' : f'❇️ *Enter the message you want to reply to the user: {requester_id}\\.*'
    }

    keyboard = [['🚫 Cancel']]
    update.effective_chat.send_message(
        text = messages.get('answer'),
        reply_markup = ReplyKeyboardMarkup(keyboard,resize_keyboard=True),
        parse_mode=config.PARSEMODE
    )

    update.callback_query.answer()

    return states.PROCESS_ANSWER

def process_answer(update:Update,ctxt:CallbackContext):
    if update.effective_user.id not in (int(os.getenv('owner')),):
        return -1
    if ctxt.user_data.get('requester_id',None) is None:
        return states.ADMIN

    messages = {
        'error' : '❌ *Could not send message to user, probably he blocked the bot\\.*',
        'succesfuly-sent' : '✔️ *Message sent to `{user_id}`\\.*',
        'user-notification-text' : 'ℹ️ *Answer from an administrator\\.*\n\n✉️ *Message:* {message}',
        'user-notification-multimedia' : 'ℹ️ *Answer from an administrator\\.*\n\n✉️ *Message:*'
    }
    
    keyboard = [['➕ Ticket']]

    try:
        message_text: str
        if update.message is None or \
                update.message.text is None:
            message_text = messages.get('user-notification-multimedia')
        else:
            message_text = messages.get('user-notification-text').format(message=parse(update.message.text))
        ctxt.bot.send_message(
            chat_id = ctxt.user_data.get('requester_id'),
            text =    message_text,
            parse_mode = config.PARSEMODE
        )
        if update.message.text is None:
            update.effective_message.copy(
                chat_id = ctxt.user_data.get('requester_id')
            )
    except Exception as e:
        update.effective_chat.send_message(
            text = messages.get('error'),
            parse_mode = config.PARSEMODE,
            reply_markup = ReplyKeyboardMarkup(keyboard,resize_keyboard=True)
        )
        return states.ADMIN
    else:
        update.effective_chat.send_message(
            text = messages.get('succesfuly-sent').format(user_id=parse(ctxt.user_data.get('requester_id'))),
            parse_mode = config.PARSEMODE,
            reply_markup = ReplyKeyboardMarkup(keyboard,resize_keyboard=True)
        )
        return states.ADMIN
