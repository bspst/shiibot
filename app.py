import telepot
import traceback
import time
from datetime import datetime
import urllib3
import os
import firebase_admin
from firebase_admin import credentials, db
from github import Github
import tweepy
import json

bot = telepot.Bot(os.environ['BOT_TOKEN'])
bot.setWebhook("")

cred = credentials.Certificate(json.loads(os.environ['FIREBASE_KEY']))
app = firebase_admin.initialize_app(cred, {
    'databaseURL': os.environ['FIREBASE_DB_URL']
})

gh = Github(os.environ['GITHUB_TOKEN'])

tw_auth = json.loads(os.environ['TWITTER_AUTH'])
oah = tweepy.OAuthHandler(tw_auth['consumer_key'], tw_auth['consumer_secret'])
oah.set_access_token(tw_auth['access_token'], tw_auth['access_token_secret'])
twitter = tweepy.API(oah)

def handle(msg):
    global app, gh, twitter

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
                parts = msg['text'].strip().split()
                cmd = parts[0][1:]
                body = msg['text'][len(parts[0]):]

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

                if cmd == "todo":
                    # Make issue in bspst/todo
                    repo = gh.get_repo("bspst/todo")

                    if len(body.strip()) == 0:
                        reply = "You can't do nothing"
                    else:
                        issue_title = body.split("\n")[0]
                        issue_body = body[len(issue_title)+1:].strip()

                        # File issue
                        issue = repo.create_issue("[{}] {}".format(sender['username'], issue_title, body=issue_body))

                        issue_url = "https://github.com/bspst/todo/issues/{}".format(issue.number)
                        reply = "Issue created! [#{}]({})".format(issue.number, issue_url)

                if cmd == "tweet":
                    # Sends a tweet to @realbspst
                    if len(body.strip()) == 0:
                        reply = "You can't tweet nothing"
                    else:
                        status = twitter.update_status(status=body)
                        reply = "[Tweet posted!](https://twitter.com/realbspst/status/{})".format(status.id)

                if cmd == "fapped":
                    # Fap counter for https://github.com/bspst/todo/issues/21
                    ref = db.reference("/faps", app)
                    user_data = ref.child(str(sender_id))
                    current = user_data.get()
                    user_data.child(str(len(current))).set(time.time())

                    reply = "DB updated! Total: {} faps.".format(len(current))
                    pass

                if cmd == "fap_status":
                    # Fap statistics
                    ref = db.reference("/faps", app)
                    user_data = ref.child(str(sender_id)).get()
                    if user_data == None:
                        reply = "Oh my sweet summer child..."
                    else:
                        last_timestamp = list(user_data)[-1]
                        last_fap = datetime.fromtimestamp(last_timestamp).strftime('%Y-%m-%d %H:%M:%S')
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
