import telepot
import traceback
import time
from datetime import datetime
from urllib.request import urlopen
import urllib3
import os
import firebase_admin
from firebase_admin import credentials, db
from github import Github
import tweepy
import json
import re

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

def file_issue(repo_name, title, body):
    global gh

    repo = gh.get_repo("bspst/{}".format(repo_name))

    if len(title.strip()) == 0:
        return False

    issue_title = title.strip()
    issue_body = body.strip()

    # File issue
    issue = repo.create_issue(issue_title, body=issue_body)

    return issue.number, "https://github.com/bspst/{}/issues/{}".format(repo_name, issue.number)

def parse_message(msg, access):
    global app, gh, twitter, bot

    sender = msg['from']
    sender_id, sender_name = sender['id'], sender['first_name']

    parts = msg['text'].strip().split()
    cmd = parts[0][1:]
    body = msg['text'][len(parts[0]):]

    print("Cmd: '{}'".format(cmd))

    # Check if command is tagged
    if '@' in cmd:
        tagged_cmd = cmd.split('@')
        cmd = tagged_cmd[0]
        tag = tagged_cmd[1]
        if tag != 'shiina_mashibot':
            # Do nothing if not for bot
            return

    print("=>", cmd)

    if cmd == "start":
        return "I'm alive!"

    if cmd == "ping":
        return "Pong!"

    if cmd == "fapped":
        # Fap counter for https://github.com/bspst/todo/issues/21
        ref = db.reference("/faps", app)
        user_data = ref.child(str(sender_id))
        current = user_data.get()
        if current == None:
            current = []
        user_data.child(str(len(current))).set(int(round(time.time())))

        return "DB updated! Total: {} faps.".format(len(current)+1)

    if cmd == "fap":
        arg = body.strip()

        ref = db.reference("/faps", app)
        user_data = ref.child(str(sender_id)).get()
        if user_data == None:
            user_data = []

        if arg == "dump":
            # Dump fap data
            return "`{}`".format(json.dumps(user_data))

        elif arg == "status":
            # Fap statistics
            if len(user_data) == 0:
                return "Oh my sweet summer child..."

            last_timestamp = list(user_data)[-1]
            last_fap = datetime.fromtimestamp(last_timestamp).strftime('%Y-%m-%d %H:%M:%S')
            fap_ago = datetime.fromtimestamp(time.time() - last_timestamp).strftime('%dd %Hh %Mm %Ss')
            return "Total: {} faps, last: {} UTC ({} ago)".format(len(user_data), last_fap, fap_ago)

        else:
            return "usage: /fap dump|status"

    print("Access: {}".format(access))

    # The commands below require a higher access level
    if not access:
        return "Sorry, you can't do that here."

    if cmd == "todo":
        # Make issue in bspst/todo
        repo = gh.get_repo("bspst/todo")

        if len(body.strip()) == 0:
            return "You can't do nothing"

        issue_title = body.split("\n")[0].strip()
        issue_body = body[len(issue_title)+1:].strip()

        issue_num, issue_url = file_issue("todo", "[{}] {}".format(sender['username'], issue_title), issue_body)
        if issue_url:
            return "Issue filed! [#{}]({})".format(issue.number, issue_url)

        return "Unable to file issue"

    if cmd == "issue":
        # /issue file title\nbody
        # /issue close repo number

        args = body.split()
        action = args[0]

        if action == "file":
            issue_repo = args[1]
            issue_title = body.split("\n")[0][len(action)+len(issue_repo)+2:].strip()
            issue_body = body[len(action)+len(issue_repo)+len(issue_title)+3:].strip()

            issue_num, issue_url = file_issue(issue_repo, issue_title, "Opened by {}\n\n{}".format(sender['username'], issue_body))

            if issue_url:
                return "Issue [#{}]({}) filed on [bspst/{}]({})".format(issue_num, issue_url, issue_repo, "https://github.com/bspst/{}".format(issue_repo))

            return "Unable to file issue"
        elif action == "close":
            repo_name = args[1]
            issue_number = args[2]
            # TODO
    if cmd == "retweet":
        # Retweet a tweet by its ID to @realbspst
        if len(body.strip()) == 0:
            if not 'reply_to_message' in msg:
                return "You can't retweet nothing"
            
            msg2tweet = msg['reply_to_message']
            print("Reply msg:", list(msg2tweet.keys()))
            if 'text' in msg2tweet:
                body = re.search(r'^(?:https:\/\/)twitter\.com\/([^?\/#]+)\/status\/([0-9]+).*$', msg2tweet)
                reusername = body.group(1)
                twid = body.group(2)
                retweet = twitter.retweet(twid)
        else:
            message = re.search(r'^(?:https:\/\/)twitter\.com\/([^?\/#]+)\/status\/([0-9]+).*$', body)
            reusername = message.group(1)
            twid = message.group(2)
            retweet = twitter.retweet(twid)
        return "[Retweeted "+ reusername + "'s post!](https://twitter.com/realbspst/status/{})".format(retweet.id)
    
    if cmd == "tweet":
        # Sends a tweet to @realbspst
        if len(body.strip()) == 0:
            if not 'reply_to_message' in msg:
                return "You can't tweet nothing"

            msg2tweet = msg['reply_to_message']
            print("Reply msg:", list(msg2tweet.keys()))
            if 'text' in msg2tweet:
                body = "{}: {}".format(msg2tweet['from']['username'], msg2tweet['text'])
                status = twitter.update_status(status=body)
            elif 'photo' in msg2tweet:
                photo_id = msg2tweet['photo'][-1]['file_id']
                photo_path = bot.getFile(photo_id)['file_path'].split("/")[-1]
                bot.download_file(photo_id, photo_path)
                # photo_file = open("https://api.telegram.org/file/bot{}/{}".format(os.environ['BOT_TOKEN'], photo_path))
                caption = "{}: {}".format(msg2tweet['from']['username'], msg2tweet['caption']) if 'caption' in msg2tweet else msg2tweet['from']['username']

                status = twitter.update_with_media(photo_path, status=caption)
        else:
            status = twitter.update_status(status="{}: {}".format(sender['username'], body))

        return "[Tweet posted!](https://twitter.com/realbspst/status/{})".format(status.id)

    if cmd == "untweet":
        # Deletes a tweet
        if len(body.strip()) == 0:
            if not 'reply_to_message' in msg:
                # Delete last tweet
                id2delete = twitter.user_timeline(count=1)[0].id
            else:
                # TODO
                return
        else:
            if '/' in body:
                id2delete = int(body.strip().split('/')[-1])
            else:
                id2delete = int(body.strip())

        # Delete tweet
        twitter.destroy_status(id2delete)
        return "Untweeted message"

def handle(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    sender = msg['from']
    sender_id, sender_name = sender['id'], sender['first_name']
    print(content_type, chat_type, chat_id, sender_name)
    print('< ', msg['text'])
    print(list(msg.keys()))

    # Limit access
    access = True

    if chat_id != int(os.environ['GROUP_ID']) and chat_type == "supergroup":
        bot.sendMessage(chat_id, "Sorry, this is a private bot.")
        bot.sendMessage(chat_id, "https://github.com/bspst/shiibot")
        return

    if chat_type != "supergroup":
        access = False

    reply = None
    try:
        if content_type == 'text':
            if msg['text'].strip()[0] == '/':
                reply = parse_message(msg, access)

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
