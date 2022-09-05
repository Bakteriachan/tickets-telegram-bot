import os
import re

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import CallbackContext

import config
from helpers import parse
import states

def start_command_handlers(update:Update,ctxt:CallbackContext):
    messages = {
        'owner' : {
            'welcome' : 'Support bot\\.'
        },
        'guest' : {
            'language' : 'Please select a language\\.',
            'ticket' : 'Open a new ticket\\.'
        }
    }
    if update.effective_user.id in (int(os.getenv('owner')),):
        update.effective_chat.send_message(
            text = messages.get('owner').get('welcome'),
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
            return None
        else: 
            inline_keyboard = [
                [
                    InlineKeyboardButton(
                        text = 'New ticket',
                        callback_data = 'open-ticket'
                    )
                ]
            ]

            update.effective_chat.send_message(
                text = messages.get('guest').get('ticket'),
                reply_markup = InlineKeyboardMarkup(inline_keyboard),
                parse_mode = config.PARSEMODE
            )
            return None

def select_language(update:Update,ctxt:CallbackContext):
    if update.callback_query is None:
        return None
    
    messages = {
        'ticket' : 'Open a new ticket\\.'
    }

    match = re.match(r'languageselect-([a-zA-Z]+)',update.callback_query.data)
    if match.group(1) in ('en',):
        ctxt.user_data['language'] = 'en'
        
    update.callback_query.answer()
    try:
        update.callback_query.delete_message()
    except Exception: # -> if could not delete message
        pass

    inline_keyboard = [
        [
            InlineKeyboardButton(
                text = 'New ticket',
                callback_data = 'open-ticket'
            )
        ]
    ]

    update.effective_chat.send_message(
        text = messages.get('ticket'),
        reply_markup = InlineKeyboardMarkup(inline_keyboard),
        parse_mode = config.PARSEMODE
    )

def new_ticket(update:Update,ctxt:CallbackContext):
    if update.callback_query is None:
        return None

    messages = {
        'ticket-request' : 'Send message\\.'
    }

    try:
        update.callback_query.delete_message()
    except Exception:
        pass

    update.effective_chat.send_message(
        text = messages.get('ticket-request'),
        parse_mode = config.PARSEMODE
    )


    return states.PROCESS_TICKET

def process_ticket(update:Update,ctxt:CallbackContext):
    if update.message.text is None:
        return None

    ctxt.user_data['ticket'] = update.message.text

    messages = {
        'confirm' : "Send to administration\\?"
    }

    inline_keyboard = [
        [
            InlineKeyboardButton(
                text = '✅ Confirm',
                callback_data = 'confirm-ticket'
            ),
            InlineKeyboardButton(
                text = '❌ Cancel',
                callback_data = 'cancel-ticket'
            )
        ]
    ]

    update.effective_chat.send_message(
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

    messages = {
        'error' : "Something went wrong\\. Please try again\\.",
        'owner-message' : 'New ticket\n\nUser ID: `{user_id}`\nUsername : {username}\n\nMessage:\n*{message}*',
        'succesfuly-sent' : 'Message sent to admins\\.',
        'succesfuly-canceled' : 'Message sent to admins\\.'
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

        if ctxt.bot.send_message(
            chat_id = os.getenv('owner'),
            text = messages.get('owner-message').format(user_id = parse(update.effective_user.id),username = parse(username),message = parse(ctxt.user_data.get('ticket'))),
            reply_markup = InlineKeyboardMarkup(inline_keyboard),
            parse_mode = config.PARSEMODE,
            
        ):
            update.effective_chat.send_message(
                text = messages.get('succesfuly-sent'),
                parse_mode = config.PARSEMODE
            )
        else:
            update.effective_chat.send_message(
                text = messages.get('error'),
                parse_mode = config.PARSEMODE
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
        'answer' : 'Send message you want to send to user'
    }

    update.effective_chat.send_message(
        text = messages.get('answer'),
        parse_mode=config.PARSEMODE
    )

    return states.PROCESS_ANSWER

def process_answer(update:Update,ctxt:CallbackContext):
    if update.effective_user.id not in (int(os.getenv('owner')),):
        return -1
    if ctxt.user_data.get('requester_id',None) is None:
        return -1

    messages = {
        'error' : 'Could not send message to user, probably he blocked the bot\\.',
        'succesfuly-sent' : 'Answer succesfuly sent to user with id {user_id}\\.'
    }
    
    try:
        update.effective_message.copy(
            chat_id = ctxt.user_data.get('requester_id')
        )
    except Exception:
        update.effective_chat.send_message(
            text = message.get('error'),
            parse_mode = config.PARSEMODE
        )
        return states.ADMIN
    else:
        update.effective_chat.send_message(
            text = messages.get('succesfuly-sent').format(user_id=parse(ctxt.user_data.get('requester_id'))),
            parse_mode = config.PARSEMODE
        )
        return states.ADMIN