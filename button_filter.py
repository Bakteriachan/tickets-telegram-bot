from telegram.ext import MessageFilter
from telegram import Message

class BtnFilter(MessageFilter):
    def __init__(self,btnText):
        self.btnText = btnText
    def filter(self,message:Message):
        if message is None or \
            message.text is None:
            return False
        return message.text == self.btnText