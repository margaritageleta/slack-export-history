#!python3
# This script 'slack.py' downloads DMs. I can't believe there aren't more complete
# and official tools to do this.
# Slack recently change User Token authentiction and dropped some deprecated apis.
# This used old apis:
# https://gist.githubusercontent.com/Chandler/fb7a070f52883849de35/raw/f74bcec8c1c12ff2126212bb3d52e7f634e94b25/slack_history.py 
# Tried using these changes but still had problems:
# https://gist.github.com/Chandler/fb7a070f52883849de35#gistcomment-3451274
# Finally found this which mostly worked just had to make some fixes and add --all:
# https://github.com/margaritageleta/slack-export-history
#
# Unfortunately it only grabs one-to-one DMs, not multi-user chats. 
# It also doesn't grab channels. I think there are other tools that do that?
#
# python3 slack.py --token xoxp-4988244079-19823645074-1832659426481-blah  --debug --all
#
# As the github README says, you have to Create New App and configure its User Token Scopes
# then Install App into your Workspace to get a User Token. The "OAuth and Permissions" link on left
# shows your "OAuth Tokens for Your Team" e.g. "xoxp-4988244079...". 
# PS: I don't understand "for Your Team" because it's your user token that has access to
# your DMs so it should never be shared with your team? Anyway afaik the app is only
# visible by you.
# 
# It creates a bunch of json files in a "slack-data" subdirectory. The files
# are named with the userid you you were chatting with.
#
# $ jq . 'chat_D5NPV744Q_(2900-2941).txt'
# ...
#  {
#    "user_id": "U220GNV2T",
#    "user_name": "pray",
#    "text": "Good. Rainy and cool. It's good to see Lena.",
#    "ts": "1496765013.166083",
#    "date": "2017-06-06 16:03:33"
#  },
# ...
# 

import os
import json
import shutil
import requests
import argparse
import time
import sys
import traceback

from datetime import datetime
try:
    from pick import pick
except:
    print('You need to "pip3 install pick" or always use --all and comment out the pick() call.')
    sys.exit(1)

def auth(token):
    try: 
        r = requests.post('https://slack.com/api/auth.test', data = {'token': token})
        r.raise_for_status()

        data = r.json()
        if data['ok'] and data['ok']:
            print(f"Successfully authenticated for team {data['team']} (ID {data['team_id']}) and user {data['user']} (ID {data['user_id']})")
            return True
        else:
            print(f"Something went wrong. Error: {data['error']}")
            return False

    except Exception as e:
        print(f'Something went wrong. Status code: {r.status_code}')
        return False

def retrieve_data(endpoint, payload, token):
    try: 
        r = requests.post(f'https://slack.com/api/{endpoint}', data = payload)
        r.raise_for_status()
        print(f'Data retrieved OK. Status code: {r.status_code}')
        # print('!!!r.text=%s' % (r.text[:500]))
        data =  r.json()
        # print('!!!%s' % (json.dumps(data, indent=4)[:500]))
        if data['ok']:
            with open(f'{endpoint}.json', 'w') as f:
                json.dump(data, f, indent=4)
        else:
            print(f"Error: {data['error']}")

    except Exception as e:
        print(f'Something went wrong. Status code: {r.status_code}')

def fetch_users():
    with open('users.list.json') as f:
        users_dump = json.loads(f.read())
        users = {}
        for member in users_dump['members']:
            # if not member['is_bot']:
            users[member['id']] = {
                'name': member['name'], 
                'real_name': member['profile']['real_name']
            }
    return users

def fetch_conversations():
    with open('conversations.list.json') as f:
        conversations_dump = json.loads(f.read())
        conversations_dict = {}
        conversations_list = []
        for conver in conversations_dump['channels']:
            if conver['is_im']:
                #print('!!!conver=%s' % (conver))
                conversations_dict[conver['id']] = {
                    'user_id': conver['user'], 
                    'user_name': users[conver['user']]['name']
                }
                conversations_list.append(conver['id'])
        return (conversations_dict, conversations_list)

        """ These are only available if the types are specified on POST conversations.list?
        if conver['is_mpim']:
            channels[conver['id']] = {
                'creator': conver['creator'], 
            }
        if conver['is_channel']:
            channels[conver['id']] = {
                'creator': conver['creator'], 
                'is_private': conver['is_private']
            }
        """

def fetch_message_data(payload, token):
    r = data = None
    back = 0

    try: 
        # while there are older messages
        while r == None or data['has_more']:
            # and it is not the first request
            if r != None:
                # change the 'latest' argument to fetch older messages
                payload['latest'] = data['messages'][-1]['ts'] 
            
            r = requests.post(f'https://slack.com/api/conversations.history', data = payload)
            r.raise_for_status()
            print(f'Data retrieved OK. Status code: {r.status_code}')
            time.sleep(1)

            data =  r.json()
            if data['ok']:
                messages = []
                for message in data['messages']:
                    # print(u'!!!message=%s' % (message.keys()))
                    messages.append({
                    'user_id': message['user'] if 'user' in message else 'UNKNOWN', 
                    'user_name': users[message['user']]['name'] if 'user' in message else message['username'] if 'username' in message else 'UNKNOWN',
                    'text': message['text'],
                    'ts': message['ts'],
                    'date': datetime.fromtimestamp(float(message['ts'])).strftime('%Y-%m-%d %H:%M:%S')
                })
                with open(f"chat_{payload['channel']}_({back}-{back + len(data['messages']) - 1}).txt", 'w') as f:
                    json.dump(messages, f, indent=4)
                back += len(data['messages'])
            else:
                print(f"Error: {data['error']}")

    except Exception as e:
        print('Exception: %s' % (repr(e)))
        traceback.print_exc()
        print(f'Something went wrong. Status code: {r.status_code}')
        sys.exit(1)

if __name__ == "__main__":

    # Define parser to pass OAuth token
    parser = argparse.ArgumentParser(description = 'Export Slack history')
    parser.add_argument('--token', required = True, help = "OAuth Access Token")
    parser.add_argument('--all', required = False, action='store_true', help = "whether to save DMs with all users")
    parser.add_argument('--debug', required = False, action='store_true', help = "whether to show HTTP requests")
    args = parser.parse_args()


    if args.debug:
        import logging
        import contextlib
        from http.client import HTTPConnection # py3
        HTTPConnection.debuglevel = 5
        logging.basicConfig()
        logging.getLogger().setLevel(logging.DEBUG)
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True

    # Do Auth Test to check user
    if auth(args.token):

        # Define the payload to do requests at Slack API
        PAYLOAD = {
        }

        # Create a directory where to store the data
        dir = 'slack-data'
        if not os.path.exists(dir):
            os.makedirs(dir)
        os.chdir(dir) 

        # Retrieve users and conversations lists
        retrieve_data('users.list', PAYLOAD, args.token)
        users = fetch_users()

        PAYLOAD['types'] = 'im'
        retrieve_data('conversations.list', PAYLOAD, args.token)

        # Select chat to export
        title = 'Please the conversation to export: '
        convers, options = fetch_conversations()

        if args.all:
            for id in options:
                p = PAYLOAD.copy()
                print(f'\nPreparing to export chat {id} ({convers[id]["user_name"]})...\n')
                time.sleep(1)
                p['channel'] = id
                fetch_message_data(p)
                time.sleep(1)
        else:
            option, index = pick([f"Chat {option} with {convers[option]['user_name']}" for option in options], title)
            PAYLOAD['channel'] = options[index]

            # Export chat
            print('\nPreparing to export chat ...\n')
            fetch_message_data(PAYLOAD)


    else:
        # Auth fail
        pass