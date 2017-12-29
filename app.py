import telepot
import time
import urllib3
import os

bot = telepot.Bot(os.environ['BOT_TOKEN'])
bot.setWebhook("")

def handle(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    print(content_type, chat_type, chat_id)

    if chat_id != int(os.environ['GROUP_ID']):
        bot.sendMessage(chat_id, "Sorry, this is a private bot.")
        bot.sendMessage(chat_id, "ChatID: {}".format(chat_id))
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

bot.message_loop(handle)

print('Listening ...')

# Keep the program running.
while 1:
    time.sleep(10)
