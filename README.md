# Telegram bot for interacting with users.
+ This bot is usefull if you want to accept feedback/comments of a service (or whatever you want actually) from telegram users.

# Configuration
+ Create a file named `.env` in the same directories as the bot main script and place bot token and owner id in telegram. Like this:

    ```
    TOKEN=<your_bot_token>
    owner=<owner_id>    
    ```
    - You must replace `<your_bot_token>` with the actual bot token and `<owner_id>` with the owner telegram id (There are many bots that can help you to find this id ) - the telegram id that will be recieving feedbacks/comments


# Making the bot run
+ The bot depends on `python-telegram-bot` third-party library version `13.11`
+ You can make the bot run with `python3 main.py`
