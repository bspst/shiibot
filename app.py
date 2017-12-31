import telepot
import traceback
import time
from datetime import datetime
import urllib3
import os
import firebase_admin
from firebase_admin import credentials, db
import json

bot = telepot.Bot(os.environ['BOT_TOKEN'])
bot.setWebhook("")

cred = credentials.Certificate(json.loads(os.environ['FIREBASE_KEY']))
app = firebase_admin.initialize_app(cred, {
    'databaseURL': os.environ['FIREBASE_DB_URL']
})

def handle(msg):
    global app

    content_type, chat_type, chat_id = telepot.glance(msg)
    sender = msg['from']
    sender_id, sender_name = sender['id'], sender['first_name']
    print(content_type, chat_type, chat_id, sender_name)
    print('< ', msg['text'])

    if chat_id != int(os.environ['GROUP_ID']) and chat_type == "group":
        bot.sendMessage(chat_id, "Sorry, this is a private bot.")
        bot.sendMessage(chat_id, "https://github.com/bspst/shiibot")
        return

    reply = None
    try:
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
                    reply = "I'm alive!"

                if cmd == "ping":
                    reply = "Pong!"

                if cmd == "fapped":
                    # Fap counter for https://github.com/bspst/todo/issues/21
                    ref = db.reference("/faps", app)
                    user_data = ref.child(str(sender_id))
                    user_data.child(str(msg['message_id'])).set(time.time())
                    current = user_data.get()

                    reply = "DB updated! Total: {} faps.".format(len(current)+1)
                    pass

                if cmd == "fap_status":
                    # Fap statistics
                    ref = db.reference("/faps", app)
                    user_data = ref.child(str(sender_id)).get()
                    last_index = list(user_data.keys())[0]
                    last_fap = datetime.fromtimestamp(user_data[last_index]).strftime('%Y-%m-%d %H:%M:%S')
                    reply = "Total: {} faps, last: {} UTC".format(len(user_data), last_fap)

    except Exception as e:
        reply = "```python\n{}```".format(traceback.format_exc())

    if reply != None:
        bot.sendMessage(chat_id, reply, parse_mode="Markdown", reply_to_message_id=msg['message_id'])
        print('> ', reply)

bot.message_loop(handle)

print('Listening ...')

# Keep the program running.
while 1:
    time.sleep(10)
