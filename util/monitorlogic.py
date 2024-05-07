import os
import json

def save_info(guild_id, channel_id, message_id, host, port):
    directory = 'data'
    filepath = os.path.join(directory, 'server_info.json')

    if not os.path.exists(directory):
        os.makedirs(directory)

    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}

    guild_data = data.get(str(guild_id), [])
    guild_data.append({
        'channel_id': channel_id,
        'message_id': message_id,
        'server': {
            'host': host,
            'port': port
        }
    })
    data[str(guild_id)] = guild_data

    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)

def load_info(guild_id):
    directory = 'data'
    filepath = os.path.join(directory, 'server_info.json')

    if not os.path.exists(directory):
        os.makedirs(directory)

    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            return data.get(str(guild_id))
    except FileNotFoundError:
        return None
    
def update_info(guild_id, channel_id, new_message_id, host, port):
    filepath = os.path.join('data', 'server_info.json')

    if not os.path.exists(filepath):
        return

    with open(filepath, 'r') as f:
        data = json.load(f)

    if str(guild_id) in data:
        for info in data[str(guild_id)]:
            if info['channel_id'] == channel_id and info['server']['host'] == host and info['server']['port'] == port:
                info['message_id'] = new_message_id
                break

    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)

  
def clear_servers():
    directory = 'data'
    filepath = os.path.join(directory, 'server_info.json')
    
    if not os.path.exists(directory):
        os.makedirs(directory)

    with open(filepath, 'w') as f:
        json.dump({}, f, indent=4)
