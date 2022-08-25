import os
import json
import shutil
import requests
import argparse

from datetime import datetime
from pick import pick

def auth(token):
    try: 
        r = requests.post('https://slack.com/api/auth.test', data = {'token': token})
        r.raise_for_status()

        data = r.json()
        if data['ok']:
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
        headers = {'Authorization': 'Bearer ' + token, 'Content-type': 'application/x-www-form-urlencoded'}
        
        r = requests.get(f'https://slack.com/api/{endpoint}', params = payload, headers = headers)
        r.raise_for_status()
        print(f'Data retrieved OK. Status code: {r.status_code}')

        data =  r.json()
        if data['ok']:
            with open(f'{endpoint}.json', 'w') as f:
                json.dump(data, f)
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
                conversations_dict[conver['id']] = {
                    'user_id': conver['user'], 
                    'user_name': users[conver['user']]['name']
                }
                conversations_list.append(conver['id'])
        return (conversations_dict, conversations_list)

        """
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
            
            headers = {'Authorization': 'Bearer ' + token, 'Content-type': 'application/x-www-form-urlencoded'}
            
            r = requests.get(f'https://slack.com/api/conversations.history', params = payload, headers = headers)
            r.raise_for_status()
            print(f'Data retrieved OK. Status code: {r.status_code}')

            data =  r.json()
            if data['ok']:
                messages = []
                for message in data['messages']:
                    messages.append({
                    'user_id': message['user'], 
                    'user_name': users[message['user']]['name'],
                    'text': message['text'],
                    'ts': message['ts'],
                    'date': datetime.fromtimestamp(float(message['ts'])).strftime('%Y-%m-%d %H:%M:%S')
                })
                with open(f"chat_{payload['channel']}_({back}-{back + len(data['messages']) - 1}).txt", 'w') as f:
                    json.dump(messages, f)
                back += len(data['messages'])
            else:
                print(f"Error: {data['error']}")

    except Exception as e:
        print(e)
        print(f'Something went wrong. Status code: {r.status_code}')

if __name__ == "__main__":

    # Define parser to pass OAuth token
    parser = argparse.ArgumentParser(description = 'Export Slack history')
    parser.add_argument('--token', required = True, help = "OAuth Access Token")
    args = parser.parse_args()

    # Do Auth Test to check user
    if auth(args.token):

        # Define the payload to do requests at Slack API
        PAYLOAD = {
        }

        # Create a directory where to store the data
        dir = 'slack-data'
        if os.path.exists(dir):
            shutil.rmtree(dir)
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

        option, index = pick([f"Chat {option} with {convers[option]['user_name']}" for option in options], title)
        PAYLOAD['channel'] = options[index]

        # Export chat
        print('\nPreparing to export chat ...\n')
        fetch_message_data(PAYLOAD, args.token)

    else:
        # Auth fail
        pass
        
