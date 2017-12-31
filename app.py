import telepot
import time
import urllib3
import os
import firebase_admin
import json

bot = telepot.Bot(os.environ['BOT_TOKEN'])
bot.setWebhook("")

cred = firebase_admin.credentials.Certificate(json.loads(os.environ['FIREBASE_KEY']))
firebase_admin.initialize_app(cred)

def handle(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    sender = msg['from']
    sender_id, sender_name = sender['id'], sender['first_name']
    print(content_type, chat_type, chat_id, sender_name)

    if chat_id != int(os.environ['GROUP_ID']):
        bot.sendMessage(chat_id, "Sorry, this is a private bot.")
        bot.sendMessage(chat_id, "https://github.com/bspst/shiibot")
        return

    if content_type == 'text':
        if msg['text'][0] == '/':
            cmd = msg['text'].split()[0][1:]

            # Check if command is tagged
            if '@' in cmd:
                tagged_cmd = cmd.split('@')
                cmd = tagged_cmd[0]
                tag = tagged_cmd[1]
                if tag != 'shiina_mashibot':
                    # Do nothing if not for bot
                    return

            if cmd == "start":
                bot.sendMessage(chat_id, "I'm alive!")

            if cmd == "ping":
                bot.sendMessage(chat_id, "Pong!")

            if cmd == "fapped":
                # TODO: Fap counter for https://github.com/bspst/todo/issues/21
                pass

bot.message_loop(handle)

print('Listening ...')

# Keep the program running.
while 1:
    time.sleep(10)
