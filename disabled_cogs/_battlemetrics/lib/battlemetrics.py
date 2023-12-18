import aiohttp
import uuid
import time
import json
from time import strftime, localtime
from datetime import datetime, timedelta

BASE_URL = "https://api.battlemetrics.com"
api_key = None
headers = None
response_data = None


async def setup(token: str) -> None:
    """Sets up the wrapper.

    Args:
        api_key (str): Your battlemetrics API token.

    Returns:
        None: Doesn't return anything.
    """
    global api_key, headers
    api_key = token
    headers = {"Authorization": f"Bearer {api_key}"}


async def _parse_octet_stream(response) -> dict:
    """Takes your banlist file from the API request and processes it into a dictionary
    Args:
        response (octet-stream): The file response from the API
    Returns:
        dict: Returns the converted file in dictionary form.
    """

    cfg_str = response.decode('utf-8')
    ban_dict = {}
    for line in cfg_str.split("\n"):
        if line.startswith("banid"):
            line_parts = line.split(" ")
            steam_id = line_parts[1]
            player_name = line_parts[2].strip('"')
            reason_parts = line_parts[3:-1]
            duration = line_parts[-1]
            if duration == "-1":
                duration = "Permanent"
            if duration.isdigit():
                duration = int(duration)
                try:
                    duration = strftime(
                        '%Y-%m-%d %H:%M:%S', localtime(duration))
                except:
                    duration = "FOREVER!"
            reason = " ".join(reason_parts).strip('"')
            ban_dict[steam_id] = {
                "playername": player_name, "reason": reason, "expires": duration}
    return response


async def _replace_char_at_position(input_string, position, new_character):
    return input_string[:position] + new_character + input_string[position + 1:]


async def _make_request(method: str, url: str, data: dict = None) -> dict:
    """Queries the API and spits out the response.
    Args:
        method (str): One of: GET, POST, PATCH, DELETE
        url (str): The endpoint/url you wish to query.
        data (dict, optional): Any params or json data you wish to send to enhance your experience?. Defaults to None.
    Raises:
        Exception: Doom and gloom.
    Returns:
        dict: The response from the server.
    """
    global headers, response_data
    async with aiohttp.ClientSession(headers=headers) as session:
        method_list = ["POST", "PATCH"]
        if method in method_list:
            async with session.request(method=method, url=url, json=data) as r:
                response_content = await r.content.read()
                if r.status == '429':
                    print(
                        "You're being rate limited by the API. Please wait a minute before trying again.")
                    return
                try:
                    response = json.loads(response_content)
                except:
                    json_string = response_content.decode('utf-8')
                    json_dict = None
                    loops = 0
                    while not json_dict:
                        if loops == 100000:
                            print("Loop count reached..")
                            break
                        try:
                            json_dict = json.loads(json_string)
                        except json.decoder.JSONDecodeError as e:
                            expecting = e.args[0].split()[1]
                            expecting.replace("'", "")
                            expecting.replace("\"", "")
                            if len(expecting) == 3:
                                expecting = expecting.replace("'", "")
                            else:
                                expecting = expecting.split()
                                expecting = f"\"{expecting[0]}\":"
                            json_string = await _replace_char_at_position(json_string, e.pos, expecting)
                        loops += 1
                    response = json_dict
                return response
        else:
            async with session.request(method=method, url=url, params=data) as r:
                content_type = r.headers.get('content-type', '')
                if r.status == '429':
                    print(
                        "You're being rate limited by the API. Please wait a minute before trying again.")
                    return
                if 'json' in content_type:
                    try:
                        response = await r.json()
                    except:
                        json_string = response_content.decode('utf-8')
                        json_dict = None
                        loops = 0
                        while not json_dict:
                            if loops == 100000:
                                print("Loop count reached..")
                                break
                            try:
                                json_dict = json.loads(json_string)
                            except json.decoder.JSONDecodeError as e:
                                expecting = e.args[0].split()[1]
                                expecting.replace("'", "")
                                expecting.replace("\"", "")
                                if len(expecting) == 3:
                                    expecting = expecting.replace("'", "")
                                else:
                                    expecting = expecting.split()
                                    expecting = f"\"{expecting[0]}\":"
                                json_string = await _replace_char_at_position(json_string, e.pos, expecting)
                            loops += 1
                        response = json_dict
                elif 'octet-stream' in content_type:
                    response = await _parse_octet_stream(await r.content.read())
                elif "text/html" in content_type:
                    response = await r.content.read()
                    response = str(response)
                    response = response.replace("'", "")
                    response = response.replace("b", "")
                else:
                    raise Exception(
                        f"Unsupported content type: {content_type}")
    if response_data:
        if not response_data.get('pages'):
            response_data = response
            response_data['pages'] = []
    return response


def calculate_future_date(input_string):
    # Extract the numeric part and unit from the input string
    number = int(input_string[:-1])
    unit = input_string[-1]

    # Define a dictionary to map units to timedelta objects
    unit_to_timedelta = {
        'd': timedelta(days=number),
        'w': timedelta(weeks=number),
        'm': timedelta(days=number*30),  # Approximate for months
        'h': timedelta(hours=number),    # Hours
    }

    # Get the timedelta object based on the unit
    delta = unit_to_timedelta.get(unit)

    if delta:
        # Calculate the future date by adding the timedelta to the current date
        future_date = str(datetime.now() + delta)
        future_date = future_date.replace(" ", "T")
        future_date += "Z"
        return future_date
    else:
        return None


async def check_api_scopes(token: str = None) -> dict:
    """Retrieves the tokens scopes from the oauth.
    Documentation: None.
    Args:
        api_key (str, optional): Your given API token. Defaults to the one supplied to this battlemetrics class.
    Returns:
        dict: The tokens data.
    """
    global api_key
    if not token:
        token = api_key

    url = f"https://www.battlemetrics.com/oauth/introspect"
    data = {
        "token": token
    }
    return await _make_request(method="POST", url=url, data=data)


async def next() -> dict:
    global response_data

    if not response_data['links'].get('next'):
        return
    url = response_data['links']['next']
    if response_data['pages']:
        if response_data['pages'][-1]['links'].get('next'):
            url = response_data['pages'][-1]['links']['next']
    response_data = await _make_request(method="GET", url=url)
    response_data['pages'].append(response_data)
    return response_data


async def session_info(filter_server: int = None, filter_game: str = None, filter_organizations: int = None, filter_player: int = None, filter_identifiers: int = None) -> dict:
    """Returns the session information for the targeted server, game or organization.
    Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-session-/sessions
    Args:
        server (int, optional): Targeted server. Defaults to None.
        game (str, optional): Targeted game. Defaults to None.
        organizations (int, optional): Targeted Organization. Defaults to None.
        player (int, optional): Targeted player. Defaults to None.
        identifiers (int, optional): Targeted identifiers. Defaults to None.
    Returns:
        dict: Session information.
    """

    url = f"{BASE_URL}/sessions"
    data = {
        "include": "identifier,server,player",
        "page[size]": "100"
    }
    if filter_server:
        data["filter[servers]"] = filter_server
    if filter_game:
        data["filter[game]"] = filter_game
    if filter_organizations:
        data["filter[organizations]"] = filter_organizations
    if filter_player:
        data["filter[players]"] = filter_player
    if filter_identifiers:
        data["filter[identifiers]"] = filter_identifiers
    return await _make_request(method="GET", url=url, data=data)


async def session_coplay(sessionid: str) -> dict:
    """Returns a list of sessions that were active during the same time as the provided session id.
    Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-session-/sessions/{(%23%2Fdefinitions%2Fsession%2Fdefinitions%2Fidentity)}/relationships/coplay
    Args:
        sessionid (str): The session ID you want to lookup
    Returns:
        dict: A dictionary response from the server.
    """

    url = f"{BASE_URL}/sessions/{sessionid}/relationships/coplay"
    data = {
        "include": "identifier,server,player",
        "page[size]": "100"
    }
    return await _make_request(method="GET", url=url, data=data)


async def server_list(search: str = None, countries: list = None, favorited: bool = False, game: str = None,
                      blacklist: str = None, whitelist: str = None, organization: str = None, rcon: bool = True) -> dict:
    """List, search and filter servers.
    Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-server-/servers
    Args:
        search (str, optional): Search for specific server. Defaults to None.
        countries (list, optional): Server in a country. Defaults to None.
        favorited (bool, optional): Favorited or not on battlemetrics. Defaults to False.
        game (str, optional): Specific game. Defaults to None.
        blacklist (str, optional): Blacklisted servers. Defaults to None.
        whitelist (str, optional): Whitelisted servers. Defaults to None.
        organization (str, optional): Organization ID. Defaults to None.
        rcon (bool, optional): RCON only. Defaults to False.
    Returns:
        dict: Dictionary response from battlemetrics.
    """

    url = f"{BASE_URL}/servers"
    data = {
        "page[size]": "100",
        "include": "serverGroup",
        "filter[favorites]": str(favorited).lower(),
        "filter[rcon]": str(rcon).lower()
    }
    if search:
        data["filter[search]"] = search
    if countries:
        data["filter[countries]"] = countries
    if game:
        data["filter[game]"] = game
    if blacklist:
        data["filter[ids][blacklist]"] = blacklist
    if whitelist:
        data["filter[ids][whitelist]"] = whitelist
    if organization:
        data["filter[organizations]"] = int(organization)
    return await _make_request(method="GET", url=url, data=data)


async def server_create(server_ip: str, server_port: str, port_query: str, game: str, server_gsp: str = None, organization_id: int = None, banlist_id: str = None, server_group: str = None) -> dict:
    """Add a server to the system.
    Documentation: https://www.battlemetrics.com/developers/documentation#link-POST-server-/servers
    The documentation does not provide information on how to properly use the params after the "Game" param.
    Args:
        server_ip (str): The IP of your server
        server_port (str): The port of the server
        port_query (str): The port query of the server
        game (str): The game of the server
        server_gsp (str): game server provider
        organization_id (int): The organization ID the server belongs to
        banlist_id (str): A banlist ID the server uses.
        server_group (str): The server group.
    Returns:
        dict: Response from battlemetrics.
    """

    url = f"{BASE_URL}/servers"
    data = {
        "data": {
            "type": "server",
            "attributes": {
                "ip": f"{server_ip}",
                "port": f"{server_port}",
                "portQuery": f"{port_query}"
            },
            "relationships": {
                "game": {
                    "data": {
                        "type": "game",
                        "id": f"{game}"
                    }
                }
            }
        }
    }
    return await _make_request(method="POST", url=url, data=data)


async def server_update(server_id: int) -> dict:
    pass
 #  data = {
 #      "data": {
 #          "type": "server",
 #          "id": "42",
 #          "attributes": {
 #              "portRCON": 2302,
 #              "rconPassword": "password",
 #              "metadata": {
 #              },
 #              "ip": "127.0.0.1",
 #              "address": "play.example.com",
 #              "port": 2302,
 #              "portQuery": 2303,
 #              "private": False
 #          },
 #          "relationships": {
 #              "defaultBanList": {
 #                  "data": {
 #                      "type": "banList",
 #                      "id": "01234567-89ab-cdef-0123-456789abcdef"
 #                  }
 #              }
 #          }
 #      }
 #  }


async def server_enable_rcon(server_id: int) -> dict:
    # This endpoint is not completed by the creator of this wrapper.
    pass


async def server_send_console_command(server_id: int, command: str) -> dict:
    """
    Sends a raw server console command. These commands are usually what you can type in game via the F1 console.
    An example: mute <steamid> <duration> <reason>
    another is: kick <steamid>
    Args:
        server_id (int): The server you want the command to run on.
        command (str): The command you want to attempt to run!
    Returns:
        dict: If it was successful or not.
    """

    url = f"{BASE_URL}/servers/{server_id}/command"
    data = {
        "data":
        {
            "type": "rconCommand",
            "attributes":
            {
                "command": "raw",
                "options":
                {
                    "raw": f"{command}"
                }
            }
        }
    }
    return await _make_request(method="POST", url=url, data=data)


async def server_delete_rcon(server_id: int) -> dict:
    """
    Names on the tin, deletes the RCON for your server
    Documentation: https://www.battlemetrics.com/developers/documentation#link-DELETE-server-/servers/{(%23%2Fdefinitions%2Fserver%2Fdefinitions%2Fidentity)}/rcon
    Args:
        server_id (int): The server ID.
    Returns:
        dict: Response from the server.
    """

    url = f"{BASE_URL}/servers/{server_id}/rcon"
    return await _make_request(method="DELETE", url=url)


async def server_disconnect_rcon(server_id: int) -> dict:
    """
    Names on the tin, disconnects RCON from your server.
    Documentation: https://www.battlemetrics.com/developers/documentation#link-DELETE-server-/servers/{(%23%2Fdefinitions%2Fserver%2Fdefinitions%2Fidentity)}/rcon/disconnect
    Args:
        server_id (int): Server ID
    Returns:
        dict: Response from the server.
    """

    url = f"{BASE_URL}/servers/{server_id}/rcon/disconnect"
    return await _make_request(method="DELETE", url=url)


async def server_connect_rcon(server_id: int) -> dict:
    """Names on the tin, connects RCON to your server.
    Documentation: https://www.battlemetrics.com/developers/documentation#link-DELETE-server-/servers/{(%23%2Fdefinitions%2Fserver%2Fdefinitions%2Fidentity)}/rcon/connect
    Args:
        server_id (int): Server ID
    Returns:
        dict: Response from the server.
    """

    url = f"{BASE_URL}/servers/{server_id}/rcon/connect"
    return await _make_request(method="DELETE", url=url)


async def server_info(server_id: int) -> dict:
    """Server info.
    Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-server-/servers/{(%23%2Fdefinitions%2Fserver%2Fdefinitions%2Fidentity)}
    Args:
        server_id (int): The server ID
    Returns:
        dict: The server information.
    """

    url = f"{BASE_URL}/servers/{server_id}"
    data = {
        "include": "player,identifier,session,serverEvent,uptime:7,uptime:30,uptime:90,serverGroup,serverDescription,organization,orgDescription,orgGroupDescription"
    }

    return await _make_request(method="GET", url=url, data=data)


async def player_count_history(server_id: int, start_time: str = None, end_time: str = None, resolution: str = "raw") -> dict:
    """Player Count History
    Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-server-/servers/{(%23%2Fdefinitions%2Fserver%2Fdefinitions%2Fidentity)}/player-count-history
    Args:
        server_id (int): The server ID
        start_time (str, optional): The UTC start time. Defaults to 1 day ago.
        end_time (str, optional): The UTC end time. Defaults to today/now.
        resolution (str, optional): One of: "raw" or "30" or "60" or "1440". Defaults to "raw"
    Returns:
        dict: A datapoint of the player count history.
    """

    if not start_time:
        now = datetime.utcnow()
        start_time = now - timedelta(days=1)
        start_time = start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    if not end_time:
        end_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    url = f"{BASE_URL}/servers/{server_id}/player-count-history"
    data = {
        "start": start_time,
        "end": end_time,
        "resolution": resolution
    }
    return await _make_request(method="GET", url=url, data=data)


async def server_rank_history(server_id: int, start_time: str = None, end_time: str = None) -> dict:
    """Server Rank History
    Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-server-/servers/{(%23%2Fdefinitions%2Fserver%2Fdefinitions%2Fidentity)}/rank-history
    Args:
        server_id (int): The server ID
        start_time (str, optional): The UTC start time. Defaults to 1 day ago.
        end_time (str, optional): The UTC end time. Defaults to today/now.
    Returns:
        dict: Datapoint of the server rank history.
    """

    if not start_time:
        now = datetime.utcnow()
        start_time = now - timedelta(days=1)
        start_time = start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    if not end_time:
        end_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    url = f"{BASE_URL}/servers/{server_id}/rank-history"
    data = {
        "start": start_time,
        "stop": end_time
    }
    return await _make_request(method="GET", url=url, data=data)


async def server_group_rank_history(server_id: int, start_time: str = None, end_time: str = None) -> dict:
    """Group Rank History. The server must belong to a group.
    Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-server-/servers/{(%23%2Fdefinitions%2Fserver%2Fdefinitions%2Fidentity)}/group-rank-history
    Args:
        server_id (int): The server ID
        start_time (str, optional): The UTC start time. Defaults to 1 day ago.
        end_time (str, optional): The UTC end time. Defaults to today/now.
    Returns:
        dict: Datapoint of the server group rank history.
    """

    if not start_time:
        now = datetime.utcnow()
        start_time = now - timedelta(days=1)
        start_time = start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    if not end_time:
        end_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    url = f"{BASE_URL}/servers/{server_id}/group-rank-history"
    data = {
        "start": start_time,
        "end": end_time
    }
    return await _make_request(method="GET", url=url, data=data)


async def server_time_played_history(server_id: int, start_time: str = None, end_time: str = None) -> dict:
    """Time Played History
    Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-server-/servers/{(%23%2Fdefinitions%2Fserver%2Fdefinitions%2Fidentity)}/time-played-history
    Args:
        server_id (int): The server ID
        start_time (str, optional): The UTC start time. Defaults to 1 day ago.
        end_time (str, optional): The UTC end time. Defaults to today/now.
    Returns:
        dict: Datapoint of the server time played history.
    """

    if not start_time:
        now = datetime.utcnow()
        start_time = now - timedelta(days=1)
        start_time = start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    if not end_time:
        end_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    url = f"{BASE_URL}/servers/{server_id}/time-played-history"
    data = {
        "start": start_time,
        "stop": end_time
    }
    return await _make_request(method="GET", url=url, data=data)


async def server_first_time_played_history(server_id: int, start_time: str = None, end_time: str = None) -> dict:
    """First Time Player History
    Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-server-/servers/{(%23%2Fdefinitions%2Fserver%2Fdefinitions%2Fidentity)}/first-time-history
    Args:
        server_id (int): The server ID
        start_time (str, optional): The UTC start time. Defaults to 1 day ago.
        end_time (str, optional): The UTC end time. Defaults to today/now.
    Returns:
        dict: Datapoint of the server first time played history.
    """

    if not start_time:
        now = datetime.utcnow()
        start_time = now - timedelta(days=1)
        start_time = start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    if not end_time:
        end_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    url = f"{BASE_URL}/servers/{server_id}/first-time-history"
    data = {
        "start": start_time,
        "end": end_time
    }
    return await _make_request(method="GET", url=url, data=data)


async def server_unique_players_history(server_id: int, start_time: str = None, end_time: str = None) -> dict:
    """Unique Player History
    Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-server-/servers/{(%23%2Fdefinitions%2Fserver%2Fdefinitions%2Fidentity)}/unique-player-history
    Args:
        server_id (int): The server ID
        start_time (str, optional): The UTC start time. Defaults to 1 day ago.
        end_time (str, optional): The UTC end time. Defaults to today/now.
    Returns:
        dict: Datapoint of the server unique players history.
    """

    if not start_time:
        now = datetime.utcnow()
        start_time = now - timedelta(days=1)
        start_time = start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    if not end_time:
        end_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    url = f"{BASE_URL}/servers/{server_id}/unique-player-history"
    data = {
        "start": start_time,
        "end": end_time
    }
    return await _make_request(method="GET", url=url, data=data)


async def server_session_history(server_id: int, start_time: str = None, end_time: str = None) -> dict:
    """Session history
    Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-server-/servers/{(%23%2Fdefinitions%2Fserver%2Fdefinitions%2Fidentity)}/relationships/sessions
    Args:
        server_id (int): The server ID
        start_time (str, optional): The UTC start time. Defaults to 1 day ago.
        end_time (str, optional): The UTC end time. Defaults to today/now.
    Returns:
        dict: Datapoint of the server session history.
    """

    if not start_time:
        now = datetime.utcnow()
        start_time = now - timedelta(days=1)
        start_time = start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    if not end_time:
        end_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    url = f"{BASE_URL}/servers/{server_id}/relationships/sessions"
    data = {
        "start": start_time,
        "stop": end_time,
        "include": "player"
    }
    return await _make_request(method="GET", url=url, data=data)


async def server_force_update(server_id: int) -> dict:
    """Force Update will cause us to immediately queue the server to be queried and updated. This is limited to subscribers and users who belong to the organization that owns the server if it is claimed.
        This endpoint has a rate limit of once every 30 seconds per server, and 10 every five minutes per user.
    Documentation: https://www.battlemetrics.com/developers/documentation#link-POST-server-/servers/{(%23%2Fdefinitions%2Fserver%2Fdefinitions%2Fidentity)}/force-update
    Args:
        server_id (int): The server ID
    Returns:
        dict: Response from the server.
    """

    url = f"{BASE_URL}/servers/{server_id}/force-update"
    return await _make_request(method="POST", url=url)


async def server_outage_history(server_id: int, uptime: str = "90", start_time: str = None, end_time: str = None) -> dict:
    """Outage History. Outages are periods of time that the server did not respond to queries. Outage history stored and available for 90 days.
    Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-server-/servers/{(%23%2Fdefinitions%2Fserver%2Fdefinitions%2Fidentity)}/relationships/outages
    Args:
        server_id (int): The server ID
        uptime (str, optional): One of 7, 30 or 90. Defaults to "90".
        start_time (str, optional): The UTC start time. Defaults to 1 day ago.
        end_time (str, optional): The UTC end time. Defaults to Today/now.
    Returns:
        dict: The server outage history.
    """

    if not start_time:
        now = datetime.utcnow()
        start_time = now - timedelta(days=1)
        start_time = start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    if not end_time:
        end_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    url = f"{BASE_URL}/servers/{server_id}/relationships/outages"
    data = {
        "page[size]": "100",
        "filter[range]": f"{start_time}:{end_time}",
        "include": f"uptime:{uptime}"
    }
    return await _make_request(method="GET", url=url, data=data)


async def server_downtime_history(server_id: int, resolution: str = "60", start_time: str = None, end_time: str = None) -> dict:
    """Downtime History. Value is number of seconds the server was offline during that period. The default resolution provides daily values (1440 minutes).
    Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-server-/servers/{(%23%2Fdefinitions%2Fserver%2Fdefinitions%2Fidentity)}/relationships/downtime
    Args:
        server_id (int): The server ID
        resolution (str, optional): One of 60 or 1440. Defaults to "60".
        start_time (str, optional): The UTC start time. Defaults to 1 day ago.
        end_time (str, optional): The UTC end time. Defaults to Today/now.
    Returns:
        dict: The server Downtime history.
    """

    if not start_time:
        now = datetime.utcnow()
        start_time = now - timedelta(days=1)
        start_time = start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    if not end_time:
        end_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    url = f"{BASE_URL}/servers/{server_id}/relationships/downtime"
    data = {
        "page[size]": "100",
        "start": f"{start_time}",
        "stop": f"{end_time}",
        "resolution": f"{resolution}"
    }
    return await _make_request(method="GET", url=url, data=data)


async def player_identifiers(player_id: int) -> dict:
    """Get player identifiers and related players and identifiers.
    Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-relatedIdentifier-/players/{(%23%2Fdefinitions%2Fplayer%2Fdefinitions%2Fidentity)}/relationships/related-identifiers
    Args:
        player_id (int): The player battlemetrics Identifier.
    Returns:
        dict: Players related identifiers.
    """

    url = f"{BASE_URL}/players/{player_id}/relationships/related-identifiers"
    data = {
        "include": "player,identifier",
        "page[size]": "100"
    }
    return await _make_request(method="GET", url=url, data=data)


async def note_create(note: str, organization_id: int, player_id: int, shared: bool = True) -> dict:
    """Create a new note
    Documentation: https://www.battlemetrics.com/developers/documentation#link-POST-playerNote-/players/{(%23%2Fdefinitions%2Fplayer%2Fdefinitions%2Fidentity)}/relationships/notes
    Args:
        note (str): The note it
        shared (bool): Will this be shared or not? (True or False), default is True
        organization_id (int): The organization ID this note belongs to.
        player_id (int): The battlemetrics ID of the player this note is attached to.
    Returns:
        dict: Response from server (was it successful?)
    """

    url = f"{BASE_URL}/players/{player_id}/relationships/notes"
    data = {
        "data": {
            "type": "playerNote",
            "attributes": {
                "note": note,
                "shared": shared
            },
            "relationships": {
                "organization": {
                    "data": {
                        "type": "organization",
                        "id": f"{organization_id}",
                    }
                }
            }
        }
    }
    return await _make_request(method="POST", url=url, data=data)


async def note_delete(player_id: int, note_id: str) -> dict:
    """Delete an existing note.
    Documentation: https://www.battlemetrics.com/developers/documentation#link-DELETE-playerNote-/players/{(%23%2Fdefinitions%2Fplayer%2Fdefinitions%2Fidentity)}/relationships/notes/{(%23%2Fdefinitions%2FplayerNote%2Fdefinitions%2Fidentity)}
    Args:
        player_id (int): The battlemetrics ID of the player the note is attached to.
        note_id (str): The note ID it
    Returns:
        dict: Response from server.
    """

    url = f"{BASE_URL}/players/{player_id}/relationships/notes/{note_id}"
    return await _make_request(method="DELETE", url=url)


async def note_list(player_id: int, filter_personal: bool = False) -> dict:
    """List existing note.
    Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-playerNote-/players/{(%23%2Fdefinitions%2Fplayer%2Fdefinitions%2Fidentity)}/relationships/notes
    Args:
        player_id (int): The battlemetrics ID of the player.
        filter_personal (bool, optional): List only your notes?. Defaults to False.
    Returns:
        dict: List of notes on users profile.
    """

    url = f"{BASE_URL}/players/{player_id}/relationships/notes"
    data = {
        "include": "user,organization",
        "page[size]": "100"
    }
    if filter_personal:
        data["filter[personal]"] = str(filter_personal).lower()
    return await _make_request(method="GET", url=url, data=data)


async def note_update(player_id: int, note_id: str, note: str, shared: bool, append: bool = False) -> dict:
    """Update an existing note.
    Documentation: https://www.battlemetrics.com/developers/documentation#link-PATCH-playerNote-/players/{(%23%2Fdefinitions%2Fplayer%2Fdefinitions%2Fidentity)}/relationships/notes/{(%23%2Fdefinitions%2FplayerNote%2Fdefinitions%2Fidentity)}
    Args:
        player_id (int): The battlemetrics ID of the user.
        note_id (str): The ID of the note.
        note (str): The new note.
        shared (bool): Shared?
    Returns:
        dict: Response from server.
    """

    url = f"{BASE_URL}/players/{player_id}/relationships/notes/{note_id}"
    if append:
        existingnote = note_info(player_id=player_id, note_id=note_id)
        if existingnote:
            existingnote = existingnote['data']['attributes']['note']
        note = f"{existingnote}\n{note}"
    data = {
        "data": {
            "type": "playerNote",
            "id": "example",
            "attributes": {
                "note": f"{note}",
                "shared": f"{str(shared).lower()}"
            }
        }
    }
    return await _make_request(method="PATCH", url=url, data=data)


async def note_info(player_id: int, note_id: str) -> dict:
    """Info for existing note.
    Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-playerNote-/players/{(%23%2Fdefinitions%2Fplayer%2Fdefinitions%2Fidentity)}/relationships/notes/{(%23%2Fdefinitions%2FplayerNote%2Fdefinitions%2Fidentity)}
    Args:
        player_id (int): The battlemetrics ID of the user.
        note_id (str): The ID of the note.
    Returns:
        dict: Response from the server.
    """

    url = f"{BASE_URL}/players/{player_id}/relationships/notes/{note_id}"
    return await _make_request(method="GET", url=url)


async def flag_create(color: str, description: str, icon_name: str, flag_name: str, organization_id: int, user_id: int) -> dict:
    """Create a new flag
    Documentation: https://www.battlemetrics.com/developers/documentation#link-POST-playerFlag-/player-flags
    Args:
        color (str): The color of the flag. pattern: ^#[0-9a-fA-F]{6}$
        description (str): Flag Description
        icon_name (str): Icon name. Refer to documentation
        flag_name (str): Name of flag
        organization_id (int): The organization ID the flag belongs to
        user_id (int): The User ID the flag is created by.
    Returns:
        dict: Response from server.
    """

    url = f"{BASE_URL}/player-flags"
    data = {
        "data": {
            "type": "playerFlag",
            "attributes": {
                "icon": f"{icon_name}",
                "name": f"{flag_name}",
                "color": f"{color}",
                "description": f"{description}"
            },
            "relationships": {
                "organization": {
                    "data": {
                        "type": "organization",
                        "id": f"{organization_id}"
                    }
                },
                "user": {
                    "data": {
                        "type": "user",
                        "id": f"{user_id}"
                    }
                }
            }
        }
    }
    return await _make_request(method="POST", url=url, data=data)


async def flag_delete(flag_id: str) -> dict:
    """Delete an existing flag.
    Documentation: https://www.battlemetrics.com/developers/documentation#link-DELETE-playerFlag-/player-flags/{(%23%2Fdefinitions%2FplayerFlag%2Fdefinitions%2Fidentity)}
    Args:
        flag_id (str): The ID of the flag
    Returns:
        dict: Response from the server.
    """

    url = f"{BASE_URL}/player-flags/{flag_id}"
    return await _make_request(method="DELETE", url=url)


async def flag_info(flag_id: str) -> dict:
    """Info for existing flag.
    Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-playerFlag-/player-flags/{(%23%2Fdefinitions%2FplayerFlag%2Fdefinitions%2Fidentity)}
    Args:
        flag_id (str): The ID of the flag
    Returns:
        dict: Dictionary response of the flag data.
    """

    url = f"{BASE_URL}/player-flags/{flag_id}"
    return await _make_request(method="GET", url=url)


async def flag_list(filter_personal: bool = False) -> dict:
    """List existing player flags.
    Documentation:https://www.battlemetrics.com/developers/documentation#link-GET-playerFlag-/player-flags
    Args:
        filter_personal (bool, optional): Hide/show personal flags. Defaults to False.
    Returns:
        dict: Dictionary response of a list of flags.
    """

    url = f"{BASE_URL}/player-flags"
    data = {
        "page[size]": "100",
        "include": "organization"
    }
    if filter_personal:
        data["filter[personal]"] = str(filter_personal).lower()
    return await _make_request(method="GET", url=url, data=data)


async def flag_update(flag_id: str, color: str, description: str, icon_name: str, flag_name: str) -> dict:
    """Create a new flag
    Documentation: https://www.battlemetrics.com/developers/documentation#link-POST-playerFlag-/player-flags
    Args:
        color (str): The color of the flag. pattern: ^#[0-9a-fA-F]{6}$
        description (str): Flag Description
        icon_name (str): Icon name. Refer to documentation
        flag_name (str): Name of flag
    Returns:
        dict: Response from server.
    """

    url = f"{BASE_URL}/player-flags/{flag_id}"
    data = {
        "data": {
            "type": "playerFlag",
            "id": f"{flag_id}",
            "attributes": {
                "icon": f"{icon_name}",
                "name": f"{flag_name}",
                "color": f"{color}",
                "description": f"{description}"
            }
        }
    }
    return await _make_request(method="PATCH", url=url, data=data)


async def player_list(search: str = None, filter_online: bool = True, filter_servers: int = None, filter_organization: int = None, filter_public: bool = False) -> dict:
    """Grabs a list of players based on the filters provided. For accurate information, filter by server or organization.
    Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-player-/players
    Args:
        search (str, optional): Search for specific player. Defaults to None.
        filter_online (bool, optional): Online or offline players. Defaults to True.
        filter_servers (int, optional): Server IDs, comma separated. Defaults to None.
        filter_organization (int, optional): Organization ID. Defaults to None.
        filter_public (bool, optional): Public or private results? (RCON or Not). Defaults to False.
    Returns:
        dict: A dictionary response of all the players.
    """

    url = f"{BASE_URL}/players"
    data = {
        "page[size]": "100",
        "filter[servers]": filter_servers,
        "filter[online]": str(filter_online).lower(),
        "filter[organization]": filter_organization,
        "filter[public]": str(filter_public).lower(),
        "include": "identifiers"
    }
    if search:
        data["filter[search]"] = search
    return await _make_request(method="GET", url=url, data=data)


async def player_info(identifier: int) -> dict:

    """Retrieves the battlemetrics player information.

    Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-player-/players/{(%23%2Fdefinitions%2Fplayer%2Fdefinitions%2Fidentity)}

    Args:
        identifier (int): The Battlemetrics ID of the targeted player.

    Returns:
        dict: Returns everything you can view in a DICT form.

    """

    url = f"{BASE_URL}/players/{identifier}"
    data = {
        "include": "identifier,server,playerCounter,playerFlag,flagPlayer"
    }
    return await _make_request(method="GET", url=url, data=data)


async def player_play_history(player_id: int, server_id: int, start_time: str = None, end_time: str = None) -> dict:
    """Returns the data we use for rendering time played history charts. Start and stop are truncated to the date.
    Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-player-/players/{(%23%2Fdefinitions%2Fplayer%2Fdefinitions%2Fidentity)}/time-played-history/{(%23%2Fdefinitions%2Fserver%2Fdefinitions%2Fidentity)}
    Args:
        player_id (int): The battlemetrics player ID.
        server_id (int): The server ID
        start_time (str): The UTC start. defaults to 5 days ago.
        end_time (str): The UTC end. Defaults to now.
    Returns:
        dict: Dictionary of Datapoints.
    """

    if not start_time:
        now = datetime.utcnow()
        start_time = now - timedelta(days=5)
        start_time = start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    if not end_time:
        # end_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        now = datetime.utcnow()
        end_time = now + timedelta(days=1)
        end_time = end_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    url = f"{BASE_URL}/players/{player_id}/time-played-history/{server_id}"
    data = {
        "start": start_time,
        "stop": end_time
    }
    return await _make_request(method="GET", url=url, data=data)


async def player_server_info(player_id: int, server_id: int) -> dict:
    """Returns server specifics for the given player and server.
    Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-player-/players/{(%23%2Fdefinitions%2Fplayer%2Fdefinitions%2Fidentity)}/servers/{(%23%2Fdefinitions%2Fserver%2Fdefinitions%2Fidentity)}
    Args:
        player_id (int): The battlemetrics player ID.
        server_id (int): The server ID
    Returns:
        dict: Response from the server showing the player server info.
    """

    url = f"{BASE_URL}/players/{player_id}/servers/{server_id}"
    return await _make_request(method="GET", url=url)


async def player_match_identifiers(identifier: str, type: str = None) -> dict:
    """Searches for one or more identifiers.
    This API method is only available to authenticated users. It is also rate limited to one request a second.
    Documentation: https://www.battlemetrics.com/developers/documentation#link-POST-player-/players/match
    Args:
        identifier (str): The specific identifier.
        type (str, optional): one of:"steamID" or "BEGUID" or "legacyBEGUID" or "ip" or "name" or "survivorName" or "steamFamilyShareOwner" or "conanCharName" or "egsID" or "funcomID" or "playFabID" or "mcUUID" or "7dtdEOS" or "battlebitHWID"
    Returns:
        dict: Dictionary response of any matches.
    """

    url = f"{BASE_URL}/players/match?include=player,server,identifier,playerFlag,flagPlayer"
    data = {
        "data": [
            {
                "type": "identifier",
                "attributes": {
                    "type": f"{type}",
                    "identifier": f"{identifier}"
                }
            }
        ]
    }
    return await _make_request(method="POST", url=url, data=data)


async def player_session_history(player_id: int, filter_server: str = None, filter_organization: str = None) -> dict:
    """Returns player's session history.
    Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-player-/players/{(%23%2Fdefinitions%2Fplayer%2Fdefinitions%2Fidentity)}/relationships/sessions
    Args:
        player_id (int): The battlemetrics player id
        filter_server (str, optional): The specific server ID. Defaults to None.
        filter_organization (str, optional): The specific organization ID. Defaults to None.
    Returns:
        dict: Returns a players session history.
    """

    url = f"{BASE_URL}/players/{player_id}/relationships/sessions"
    data = {
        "include": "identifier,server",
        "page[size]": "100"
    }
    if filter_server:
        data["filter[servers]"] = filter_server
    if filter_organization:
        data["filter[organization]"] = filter_organization
    return await _make_request(method="GET", url=url, data=data)


async def organization_info(organization_id: int) -> dict:
    """Returns an organizations profile.
    Documentation: Not documented in the API.
    Args:
        organization_id (int): An organizations battlemetrics ID.
    Returns:
        dict: The information about your organization or a targeted organization
    """

    url = f"{BASE_URL}/organizations/{organization_id}"
    data = {
        "include": "organizationUser,banList,role,organizationStats"
    }
    return await _make_request(method="GET", url=url, data=data)


async def organization_stats(organization_id: int, start: str, end: str, game: str = None) -> dict:
    """Gets the player stats for the organization
    Documentation: https://www.battlemetrics.com/developers/documentation#resource-organizationStats
    Args:
        organization_id (int): Organization ID
        start (str): UTC start time. Defaults to 7 days ago.
        end (str): UTC end time. Defaults to today.
        game (str, optional): Targeted game, example: rust. Defaults to None.
    Returns:
        dict: Player stats for the organization.
    """

    if not start:
        now = datetime.utcnow()
        start = now - timedelta(days=1)
        start = start.strftime('%Y-%m-%dT%H:%M:%SZ')
    if not end:
        end = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    url = f"{BASE_URL}/organizations/{organization_id}/stats/players"
    data = {
        "filter[range]": f"{start}:{end}"
    }
    if game:
        data["filter[game]"] = game
    return await _make_request(method="GET", url=url, data=data)


async def organization_friend_list(organization_id: str, filter_accepted: bool = True, filter_origin: bool = True, filter_name: str = None, filter_reciprocated: bool = True) -> dict:
    """Gets all the organization friends.
    Documentation: https://www.battlemetrics.com/developers/documentation#resource-organizationFriend
    Args:
        organization_id (str): Your organization ID
        filter_accepted (bool, optional): True or False. Have they accepted our friendship?. Defaults to True.
        filter_origin (bool, optional): True or False. Defaults to True.
        filter_name (str, optional): Name of a specific organization. Defaults to None.
        filter_reciprocated (bool, optional): True or False. Are the feelings mutual?. Defaults to True.
    Returns:
        dict: Returns all the friendship information based on the paramaters set.
    """

    url = f"{BASE_URL}/organizations/{organization_id}/relationships/friends"
    data = {
        "include": "organization",
        "filter[accepted]": str(filter_accepted).lower(),
        "filter[origin]": str(filter_origin).lower(),
        "filter[reciprocated]": str(filter_reciprocated).lower()
    }
    if filter_name:
        data['filter[name]'] = filter_name
    return await _make_request(method="GET", url=url, data=data)


async def organization_friend(organization_id: int, friend_organization_id: int) -> dict:
    """Gets the friend information for your organization.
    Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-organizationFriend-/organizations/{(%23%2Fdefinitions%2Forganization%2Fdefinitions%2Fidentity)}/relationships/friends/{(%23%2Fdefinitions%2Forganization%2Fdefinitions%2Fidentity)}
    Args:
        organization_id (int): Your organization ID
        friend_organization_id (int): Friend organization ID
    Returns:
        dict: Dictionary response about the organization friendship
    """

    url = f"{BASE_URL}/organizations/{organization_id}/relationships/friends/{friend_organization_id}"
    data = {
        "include": "organization,playerFlag,organizationStats"
    }
    return await _make_request(method="GET", url=url, data=data)


async def organization_friend_update(organization_id: int, friend_organization_id: int, identifiers: list, playerflag: str, shared_notes: bool = True, accepted: bool = True) -> dict:
    """Updates your organizations friendship.
    Documentation: https://www.battlemetrics.com/developers/documentation#link-PATCH-organizationFriend-/organizations/{(%23%2Fdefinitions%2Forganization%2Fdefinitions%2Fidentity)}/relationships/friends/{(%23%2Fdefinitions%2Forganization%2Fdefinitions%2Fidentity)}
    Args:
        organization_id (int): Your organization ID
        friend_organization_id (int): The friendly organizations ID.
        identifiers (list): [ip, steamID], identifiers to be shared.
        shared_notes (bool, optional): Sharing Notes?
        accepted (bool, optional):Accepted friendship?
    Returns:
        dict: Returns a dictionary response on the new updated friendship.
    """

    url = f"https://api.battlemetrics.com/organizations/{organization_id}/relationships/friends/{friend_organization_id}"
    data = {
        "data": {
            "id": friend_organization_id,
            "type": "organizationFriend",
            "attributes": {
                "accepted": str(accepted).lower(),
                "identifiers": identifiers,
                "notes": str(shared_notes).lower()
            }
        }
    }
    return await _make_request(method="PATCH", url=url, data=data)


async def organization_friend_create(organization_id: int, friendly_org: int, identifiers: list, shared_notes: bool = True) -> dict:
    """Creates a new friend invite to the targeted organization ID
    Documentation: https://www.battlemetrics.com/developers/documentation#link-POST-organizationFriend-/organizations/{(%23%2Fdefinitions%2Forganization%2Fdefinitions%2Fidentity)}/relationships/friends
    Args:
        organization_id (int): Your organization ID
        friendly_org (int): Targeted organization ID
        identifiers (list): ["steamID", "ip"]
        shared_notes (bool, optional): Sharing notes? Defaults to True.
    Returns:
        dict: Returns the dictionary response from the server
    """

    url = f"https://api.battlemetrics.com/organizations/{organization_id}/relationships/friends"
    data = {
        "data": {
            "type": "organizationFriend",
            "attributes": {
                "identifiers": identifiers,
                "notes": str(shared_notes).lower()
            },
            "relationships": {
                "friend": {
                    "data": {
                        "type": "organization",
                        "id": f"{friendly_org}"
                    }
                },
                "flagsShared": {
                    "data": [
                        {
                            "type": "playerFlag",
                            "id": f"{uuid.uuid5}"
                        }
                    ]
                }
            }
        }
    }
    return await _make_request(method="POST", url=url, data=data)


async def organization_friend_delete(organization_id: int, friends_id: int) -> dict:
    """Deletes a friendship
    Documentation: https://www.battlemetrics.com/developers/documentation#link-DELETE-organizationFriend-/organizations/{(%23%2Fdefinitions%2Forganization%2Fdefinitions%2Fidentity)}/relationships/friends/{(%23%2Fdefinitions%2Forganization%2Fdefinitions%2Fidentity)}
    Args:
        organization_id (int): Your organization ID
        friends_id (int): Friends organization ID
    Returns:
        dict: Response from the server.
    """

    url = f"{BASE_URL}/organizations/{organization_id}/relationships/friends/{friends_id}"
    return await _make_request(method="DELETE", url=url)


async def organization_player_stats(organization_id: int, start_date: str = None, end_date: str = None) -> dict:
    """Returns the statistics of all the players who have joined your server and where they're from.
    Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-organization-/organizations/{(%23%2Fdefinitions%2Forganization%2Fdefinitions%2Fidentity)}/stats/players
    Args:
        organization_id (int): Your organization ID
        start_date (str, optional): Start date, max 90 days. Defaults to 90 days ago.
        end_date (str, optional): End date, defaults to now.
    Returns:
        dict: Returns a dictionary of all the stats!
    """

    url = f"{BASE_URL}/organizations/{organization_id}/stats/players"
    if not start_date:
        now = datetime.utcnow()
        start_date = now - timedelta(days=1)
        start_date = start_date.strftime('%Y-%m-%dT%H:%M:%SZ')
    if not end_date:
        end_date = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    data = {
        "filter[game]": "rust",
        "filter[range]": f"{start_date}:{end_date}"
    }
    return await _make_request(method="GET", url=url, data=data)


async def native_ban_info(server: int = None, ban: str = None) -> dict:
    """Returns all the native bans
    Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-banNative-/bans-native
    Args:
        server (int, optional): Target server. Defaults to None.
        ban (int, optional): Target ban. Defaults to None.
    Returns:
        dict: All native bans.
    """

    data = {
        "page[size]": "100",
        "include": "server,ban",
        "sort": "-createdAt",
        "fields[ban]": "reason",
        "fields[server]": "name",
        "fields[banNative]": "createdAt,reason"
    }
    if ban:
        data["filter[ban]"] = ban
    if server:
        data["filter[server]"] = server
    url = f"{BASE_URL}/bans-native"
    return await _make_request(method="GET", url=url, data=data)


async def native_force_update(native_id: str) -> dict:
    """Forces an update on a native ban
    Documentation: https://www.battlemetrics.com/developers/documentation#link-POST-banNative-/bans-native/{(%23%2Fdefinitions%2FbanNative%2Fdefinitions%2Fidentity)}/force-update
    Args:
        native_id (str): Targeted native ban
    Returns:
        dict: Response from the server.
    """

    url = f"{BASE_URL}/bans-native/{native_id}/force-update"
    return await _make_request(method="POST", url=url)


async def leaderboard_info(server_id: int,  start: str = None, end: str = None, player: int = None) -> dict:
    """Displays the leaderboard for a specific player.
    Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-leaderboardPlayer-/servers/{(%23%2Fdefinitions%2Fserver%2Fdefinitions%2Fidentity)}/relationships/leaderboards/time
    Args:
        server_id (int): The server ID
        player (int): Battlemetrics player ID
        start (str): UTC Start date. Defaults to 1 day ago.
        end (str): UTC End date. Defaults to today.
    Returns:
        dict: Returns the leaderboard information for the player.
    """

    if not start:
        now = datetime.utcnow()
        start = now - timedelta(days=1)
        start = start.strftime('%Y-%m-%dT%H:%M:%SZ')
    if not end:
        end = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    data = {
        "page[size]": "100",
        "filter[period]": f"{start}:{end}",
        "fields[leaderboardPlayer]": "name,value"
    }
    if player:
        data['filter[player]'] = player
    url = f"{BASE_URL}/servers/{server_id}/relationships/leaderboards/time"
    return await _make_request(method="GET", url=url, data=data)


async def game_features(game: str = None) -> dict:
    """Lists the game features for the specified game
    Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-gameFeature-/game-features
    Args:
        game (str, optional): _description_. Defaults to None.
    Returns:
        dict: Returns a dictionary of the game features.
    """

    data = {
        "page[size]": "100"
    }
    if game:
        data['filter[game]'] = game
    url = f"{BASE_URL}/game-features"
    return await _make_request(method="GET", url=url, data=data)


async def game_feature_options(feature_id: str, sort: str = "players") -> dict:
    """Gets the game feature options.
    Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-gameFeatureOption-/game-features/{(%23%2Fdefinitions%2FgameFeature%2Fdefinitions%2Fidentity)}/relationships/options
    Args:
        feature_id (str): The ID of the game Feature.
        sort (str, optional): Takes "count" and "players". Defaults to "players".
    Returns:
        dict: Game feature options
    """

    data = {
        "page[size]": "100",
        "sort": sort
    }
    url = f"{BASE_URL}/game-features/{feature_id}/relationships/options"
    return await _make_request(method="GET", url=url, data=data)


async def game_list(game: str = None) -> dict:
    """Lists all the games Battlemetrics can view.
    Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-game-/games
    Args:
        game (str, optional): Refine it to a specific game. Or leave as none.
    Returns:
        dict: Games information!
    """

    data = {
        "page[size]": "100"
    }
    if game:
        data['fields[game]'] = game
    url = f"{BASE_URL}/games"
    return await _make_request(method="GET", url=url, data=data)


async def game_info(game_id: str, game: str = None) -> dict:
    """Gets information on a specific game.
    Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-game-/games/{(%23%2Fdefinitions%2Fgame%2Fdefinitions%2Fidentity)}
    Args:
        game_id (str): The ID of a specific game.
        game (str, optional): Limit it to a specific game, or leave as none.
    Returns:
        dict: Game information.
    """

    data = {
        "page[size]": "100"
    }
    if game:
        data['fields[game]'] = game
    url = f"{BASE_URL}/games/{game_id}"
    return await _make_request(method="GET", url=url, data=data)


async def player_flag_add(player_id: int, flag_id: str = None) -> dict:
    """Creates or adds a flag to the targeted players profile.
    Documentation: https://www.battlemetrics.com/developers/documentation#link-POST-flagPlayer-/players/{(%23%2Fdefinitions%2Fplayer%2Fdefinitions%2Fidentity)}/relationships/flags
    Args:
        player_id (int): Battlemetrics ID of the player.
        flag_id (str, optional): An existing flag ID. Defaults to None.
    Returns:
        dict: Player profile relating to the new flag.
    """

    url = f"{BASE_URL}/players/{player_id}/relationships/flags"
    data = {
        "data": [
            {
                "type": "payerFlag"
            }
        ]
    }
    if flag_id:
        data['data'][0]['id'] = flag_id
    return await _make_request(method="POST", url=url, data=data)


async def player_flag_info(player_id: int) -> dict:
    """Returns all the flags on a players profile
    Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-flagPlayer-/players/{(%23%2Fdefinitions%2Fplayer%2Fdefinitions%2Fidentity)}/relationships/flags
    Args:
        player_id (int): Battlemetrics ID of the targeted player.
    Returns:
        dict: The profile with all the flags.
    """

    data = {
        "page[size]": "100",
        "include": "playerFlag"
    }
    url = f"{BASE_URL}/players/{player_id}/relationships/flags"
    return await _make_request(method="GET", url=url, data=data)


async def player_flag_delete(player_id: int, flag_id: str) -> dict:
    """Deletes a targeted flag from a targeted player ID
    Documentation: https://www.battlemetrics.com/developers/documentation#link-DELETE-flagPlayer-/players/{(%23%2Fdefinitions%2Fplayer%2Fdefinitions%2Fidentity)}/relationships/flags/{(%23%2Fdefinitions%2FplayerFlag%2Fdefinitions%2Fidentity)}
    Args:
        player_id (int): Battlemetrics ID of the player.
        flag_id (str): FLAG ID
    Returns:
        dict: If you were successful or not.
    """

    url = f"{BASE_URL}/players/{player_id}/relationships/flags/{flag_id}"
    return await _make_request(method="DELETE", url=url)


async def metrics(name: str = "games.rust.players", start_date: str = None, end_date: str = None, resolution: str = "60") -> dict:
    """A data point as used in time series information.
    Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-dataPoint-/metrics
    Args:
        name (str, optional): "games.{game}.players" and "games.{game}.players.steam", defaults to "games.rust.players"
        start_date (str, optional) UTC time format. Defaults to Current Date.
        end_date (str, optional): UTC time format. Defaults to 1 day ago.
        resolution (str, optional): raw, 30, 60 or 1440. Defaults to "60".
    Returns:
        dict: a bunch of numbers.
    """

    url = f"{BASE_URL}/metrics"
    # current_time = datetime.utcnow()
    # current_time_str = current_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    if not start_date:
        now = datetime.utcnow()
        start_date = now - timedelta(days=1)
        start_date = start_date.strftime('%Y-%m-%dT%H:%M:%SZ')
    if not end_date:
        end_date = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    data = {
        "metrics[0][name]": name,
        "metrics[0][range]": f"{start_date}:{end_date}",
        "metrics[0][resolution]": resolution
    }
    return await _make_request(method="GET", url=url, data=data)


async def player_coplay_info(player_id: int, time_start: str = None, time_end: str = None, player_names: str = None, organization_names: str = None, server_names: str = None) -> dict:
    """Gets the coplay data related to the targeted player
    Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-coplayRelation-/players/{(%23%2Fdefinitions%2Fplayer%2Fdefinitions%2Fidentity)}/relationships/coplay
    Args:
        player_id (int): The BATTLEMETRICS id of the targeted player
        time_start (str): UTC time start. Defaults to 7 days ago
        time_end (str): UTC time ends. Defaults to day.
        player_names (str, optional): Player names to target. Defaults to None.
        organization_names (str, optional): Specific Organizations. Defaults to None.
        server_names (str, optional): Specific servers. Defaults to None.
    Returns:
        dict: A dictionary response of all the coplay users.
    """

    if not time_start:
        now = datetime.utcnow()
        time_start = now - timedelta(days=1)
        time_start = time_start.strftime('%Y-%m-%dT%H:%M:%SZ')
    if not time_end:
        time_end = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    data = {
        "filter[period]": f"{time_start}:{time_end}",
        "page[size]": "100",
        "fields[coplayrelation]": "name,duration"
    }
    if player_names:
        data["filter[players]"] = player_names
    if organization_names:
        data["filter[organizations]"] = organization_names
    if server_names:
        data["filter[servers]"] = server_names
    url = f"{BASE_URL}/players/{player_id}/relationships/coplay"
    return await _make_request(method="GET", url=url, data=data)


async def organization_commands_activity(organization_id: int, summary: bool = False, users: str = None, commands: str = None, time_start: str = None, time_end: str = None, servers: int = None) -> dict:
    """Grabs all the command activity related to the targeted organization
    Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-commandStats-/organizations/{(%23%2Fdefinitions%2Forganization%2Fdefinitions%2Fidentity)}/relationships/command-stats
    Args:
        organization_id (int): The Organization ID
        summary (bool, optional): A summary. Defaults to False.
        users (str, optional): Specific users?. Defaults to None.
        commands (str, optional): Specific Commands?. Defaults to None.
        time_start (str, optional): UTC start time. Defaults to 7 days ago.
        time_end (str, optional): UTC end time. Defaults to today.
        servers (int, optional): Targeted servers. Defaults to None.
    Returns:
        dict: Returns command usage data.
    """

    if not time_start:
        now = datetime.utcnow()
        time_start = now - timedelta(days=1)
        time_start = time_start.strftime('%Y-%m-%dT%H:%M:%SZ')
    if not time_end:
        time_end = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    data = {
        "filter[timestamp]": f"{time_start}:{time_end}"
    }
    if summary:
        data['filter[summary]'] = str(summary).lower()
    if users:
        data['filter[users]'] = users
    if commands:
        data['filter[commands]'] = commands
    if servers:
        data['filter[servers]'] = servers
    url = f"{BASE_URL}/organizations/{organization_id}/relationships/command-stats"
    return await _make_request(method="GET", url=url, data=data)


async def ban_list(search: str = None, player_id: int = None, banlist: str = None, expired: bool = True, exempt: bool = False, server: int = None, organization_id: int = None):
    """List, search and filter existing bans.
    Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-ban-/bans
    Returns:
        dict: A dictionary response telling you if it worked or not.
    """

    data = {
        "include": "server,user,player,organization",
        "filter[expired]": str(expired).lower(),
        "filter[exempt]": str(exempt).lower(),
        "sort": "-timestamp",
        "page[size]": "100"
    }
    if organization_id:
        data['filter[organization]'] = organization_id
    if player_id:
        data['filter[player]'] = player_id
    if server:
        data['filter[server]'] = server
    if search:
        data['filter[search]'] = search
    if banlist:
        data['filter[banList]'] = banlist
    url = f"{BASE_URL}/bans"
    return await _make_request(method="GET", url=url, data=data)


async def ban_create(reason: str, note: str, steamid: str, battlemetrics_id: str, org_id: str, banlist: str, server_id: str,
                     expires: str = None,
                     orgwide: bool = True) -> dict:
    """Bans a user from your server or organization.
    Documentation: https://www.battlemetrics.com/developers/documentation#link-POST-ban-/bans
    Args:
        reason (str): Reason for the ban (This is what the user/server sees)
        note (str): Note attached to the ban (Admins/staff can see this)
        steamid (str): Steam ID of the banned user
        battlemetrics_id (str): Battlemetrics ID of the banned user
        org_id (str): Organization ID the ban is associated to.
        banlist (str): Banlist the ban is associated to.
        server_id (str): Server ID the ban is associated to.
        expires (str, optional): Expiration, leave none for permanent. Defaults to None.
        orgwide (bool, optional): Orgwide or single server?. Defaults to True.
    Returns:
        dict: The results, whether it was successful or not.
    """

    if expires:
        try:
            expiration_time = datetime.strptime(
                expires, "%Y-%m-%dT%H:%M:%S.%fZ")
        except ValueError:
            raise ValueError(
                "Invalid expiration time format. Please provide time in format 'YYYY-MM-DDTHH:MM:SS.sssZ'.")
    data = {
        "data": {
            "type": "ban",
            "attributes": {
                "uid": str(uuid.uuid4()),
                "timestamp": time.now(),
                "reason": reason,
                "note": note,
                "expires": f"{expiration_time}",
                "identifiers": [
                    1000,
                    {
                        "type": "steamID",
                        "identifier": f"{steamid}",
                        "manual": True
                    }
                ],
                "orgWide": str(orgwide).lower(),
                "autoAddEnabled": False,
                "nativeEnabled": True
            },
            "relationships": {
                "player": {
                    "data": {
                        "type": "player",
                        "id": f"{battlemetrics_id}"
                    }
                },
                "server": {
                    "data": {
                        "type": "server",
                        "id": f"{server_id}"
                    }
                },
                "organization": {
                    "data": {
                        "type": "organization",
                        "id": f"{org_id}"
                    }
                },
                "user": {
                    "data": {
                        "type": "user",
                        "id": "42"
                    }
                },
                "banList": {
                    "data": {
                        "type": "banList",
                        "id": f"{banlist}"
                    }
                }
            }
        }
    }
    url = f"{BASE_URL}/bans"
    return await _make_request(method="POST", url=url, data=data)


async def banlist_export(organization_id: int, server: int = None, game: str = "Rust") -> dict:
    """Grabs you the ban list for a specific organization or server belongin to the organization.
    Only supports Rust format at the moment.
    Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-ban-/bans/export
    Args:
        server (int): The server ID you want the bans for.
        organization (int): The organizational ID
        game (str, optional): Only supports rust bans. Defaults to "Rust".
    Returns:
        dict: The ban list. Also saves it locally.
    """

    game = game.lower()
    game = "rust"
    if game == "rust":
        format = "rust/bans.cfg"
    if game == "arma2":
        format = "arma2/bans.txt"
    if game == "arma3":
        format = "arma3/bans.txt"
    if game == "squad":
        format = "squad/Bans.cfg"
    if game == "ark":
        format = "ark/banlist.txt"
    data = {
        "filter[organization]": organization_id,
        "format": format
    }
    if server:
        data["filter[organization]"] = server
    url = f"{BASE_URL}/bans/export"
    return await _make_request(method="GET", url=url, data=data)


async def ban_delete(banid: str) -> dict:
    """Deletes a ban.
    Documentation: https://www.battlemetrics.com/developers/documentation#link-DELETE-ban-/bans/{(%23%2Fdefinitions%2Fban%2Fdefinitions%2Fidentity)}
    Args:
        banid (str): The ID of the ban.
    Returns:
        dict: The response from the server.
    """

    url = f"{BASE_URL}/bans/{banid}"
    return await _make_request(method="DELETE", url=url)


async def ban_info(banid: str) -> dict:
    """The ban profile of a specific banid.
    Documentation: https://www.battlemetrics.com/developers/documentation#link-DELETE-ban-/bans/{(%23%2Fdefinitions%2Fban%2Fdefinitions%2Fidentity)}
    Args:
        banid (str): The banid.
    Returns:
        dict: The ban information
    """

    url = f"{BASE_URL}/bans/{banid}"
    return await _make_request(method="GET", url=url)


async def ban_update(banid: str, reason: str = None, note: str = None, append: bool = False) -> dict:
    """Updates a targeted ban
    Documentation: https://www.battlemetrics.com/developers/documentation#link-PATCH-ban-/bans/{(%23%2Fdefinitions%2Fban%2Fdefinitions%2Fidentity)}
    Args:
        banid (str): The target ban
        reason (str, optional): Updated reason (not required)
        note (str, optional): Updated note (not required)
        append (bool, optional): Whether you want to append the new note to the old note.
    Returns:
        dict: The response from the server.
    """

    url = f"{BASE_URL}/bans/{banid}"
    ban = await ban_info(banid=banid)
    if reason:
        ban['data']['attributes']['reason'] = reason
    if note:
        if append:
            ban['data']['attributes']['note'] += f"\n{note}"
        else:
            ban['data']['attributes']['note'] = note
    return await _make_request(method="PATCH", url=url, data=ban)


async def banlist_invite_create(organization_id: int, banlist_id: str, permManage: bool, permCreate: bool, permUpdate: bool, permDelete: bool, uses: int = 1, limit: int = 1) -> dict:
    """Creates an invite to 
    Documentation: https://www.battlemetrics.com/developers/documentation#link-POST-banListInvite-/ban-lists/{(%23%2Fdefinitions%2FbanList%2Fdefinitions%2Fidentity)}/relationships/invites
    Args:
        organization_id (int): The target organization to be invited.
        banlist_id (str): The ID of the banlist you want to create the invite for
        permManage (bool): Are they allowed to manage it?
        permCreate (bool): Can they create stuff related to this banlist?
        permUpdate (bool): Can they update the banlist?
        permDelete (bool): Can they delete stuff related to this banlist?
        uses (int, optional): Number of times this banlist invite has been used.. Defaults to 1.
        limit (int, optional): How many times it's allowed to be used. Defaults to 1.
    Returns:
        dict: Returns whether it was successful or not.
    """

    url = f"{BASE_URL}/ban-lists/{banlist_id}/relationships/invites"
    data = {
        "data": {
            "type": "banListInvite",
            "attributes": {
                "uses": uses,
                "limit": limit,
                "permManage": str(permManage).lower(),
                "permCreate": str(permCreate).lower(),
                "permUpdate": str(permUpdate).lower(),
                "permDelete": str(permDelete).lower()
            },
            "relationships": {
                "organization": {
                    "data": {
                        "type": "organization",
                        "id": f"{organization_id}"
                    }
                }
            }
        }
    }
    return await _make_request(method="POST", url=url, data=data)


async def banlist_invite_read(invite_id: str) -> dict:
    """Allows you to see the information about a specific banlist invite, such as uses.
    Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-banListInvite-/ban-list-invites/{(%23%2Fdefinitions%2FbanListInvite%2Fdefinitions%2Fidentity)}
    Args:
        invite_id (str): The banlist invite id.
    Returns:
        dict: The banlist invite information
    """

    url = f"{BASE_URL}/ban-list-invites/{invite_id}"
    data = {
        "include": "banList",
        "fields[organization]": "tz,banTemplate",
        "fields[user]": "nickname",
        "fields[banList]": "name, action",
        "fields[banListInvite]": "uses"
    }
    return await _make_request(method="GET", url=url, data=data)


async def banlist_invite_list(banlist_id: str) -> dict:
    """Returns all the invites for a specific banlist ID
    Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-banListInvite-/ban-lists/{(%23%2Fdefinitions%2FbanList%2Fdefinitions%2Fidentity)}/relationships/invites
    Args:
        banlist_id (str): The ID of a banlist
    """

    url = f"{BASE_URL}/ban-lists/{banlist_id}/relationships/invites"
    data = {
        "include": "banList",
        "fields[organization]": "tz,banTemplate",
        "fields[user]": "nickname",
        "fields[banList]": "name,action",
        "fields[banListInvite]": "uses",
        "page[size]": "100"
    }
    return await _make_request(method="GET", url=url, data=data)


async def banlist_invite_delete(banlist_id: str, banlist_invite_id: str) -> dict:
    """Deletes an invite from a targeted banlist
    Documentation: https://www.battlemetrics.com/developers/documentation#link-DELETE-banListInvite-/ban-lists/{(%23%2Fdefinitions%2FbanList%2Fdefinitions%2Fidentity)}/relationships/invites/{(%23%2Fdefinitions%2FbanListInvite%2Fdefinitions%2Fidentity)}
    Args:
        banlist_id (str): The target banlist
        banlist_invite_id (str): The target invite.
    Returns:
        dict: Whether it was successful or not.
    """

    url = f"{BASE_URL}/ban-lists/{banlist_id}/relationships/invites/{banlist_invite_id}"
    return await _make_request(method="DELETE", url=url)


async def banlist_exemption_create(banid: str, organization_id: int, reason: str = None) -> dict:
    """Creates an exemption to the banlist.
    Documentation: https://www.battlemetrics.com/developers/documentation#link-POST-banExemption-/bans/{(%23%2Fdefinitions%2Fban%2Fdefinitions%2Fidentity)}/relationships/exemptions
    Args:
        banid (str): The banid you want to create an exemption for.
        organization_id (str): The organization associated to the exemption
        reason (str, optional): Reason for the exemption. Defaults to None.
    Returns:
        dict: Whether it was successful or not.
    """

    url = f"{BASE_URL}/bans/{banid}/relationships/exemptions"
    data = {
        "data": {
            "type": "banExemption",
            "attributes": {
                    "reason": reason
            },
            "relationships": {
                "organization": {
                    "data": {
                        "type": "organization",
                        "id": f"{organization_id}"
                    }
                }
            }
        }
    }
    return await _make_request(method="POST", url=url, data=data)


async def banlist_exemption_delete(banid: str) -> dict:
    """Deletes an exemption
    Documentation: https://www.battlemetrics.com/developers/documentation#link-DELETE-banExemption-/bans/{(%23%2Fdefinitions%2Fban%2Fdefinitions%2Fidentity)}/relationships/exemptions
    Args:
        banid (str): The ban that has an exemption
    Returns:
        dict: Whether it was successful or not
    """

    url = f"{BASE_URL}/bans/{banid}/relationships/exemptions"
    return await _make_request(method="DELETE", url=url)


async def banlist_exemption_info_single(banid: str, exemptionid: str) -> dict:
    """Pulls information from a ban regarding a specific exemption
    Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-banExemption-/bans/{(%23%2Fdefinitions%2Fban%2Fdefinitions%2Fidentity)}/relationships/exemptions/{(%23%2Fdefinitions%2FbanExemption%2Fdefinitions%2Fidentity)}
    Args:
        banid (str): Target ban
        exemptionid (str): Target exemption
    Returns:
        dict: Information about the exemption
    """

    url = f"{BASE_URL}/bans/{banid}/relationships/exemptions/{exemptionid}"
    return await _make_request(method="GET", url=url)


async def banlist_exemption_info_all(banid: str) -> dict:
    """Pulls all exemptions related to the targeted ban
    Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-banExemption-/bans/{(%23%2Fdefinitions%2Fban%2Fdefinitions%2Fidentity)}/relationships/exemptions
    Args:
        banid (str): Target ban
    Returns:
        dict: All ban exemptions
    """

    url = f"{BASE_URL}/bans/{banid}/relationships/exemptions"
    data = {
        "fields[banExemption]": "reason"
    }
    return await _make_request(method="GET", url=url, data=data)


async def banlist_exemption_update(banid: str, exemptionid: str, reason: str) -> dict:
    """Updates a ban exemption
    Documentation: https://www.battlemetrics.com/developers/documentation#link-PATCH-banExemption-/bans/{(%23%2Fdefinitions%2Fban%2Fdefinitions%2Fidentity)}/relationships/exemptions
    Args:
        banid (str): The target ban
        exemptionid (str): The target exemption
        reason (str): New reason
    Returns:
        dict: Whether you were successful or not.
    """

    banexemption = await banlist_exemption_info_single(banid=banid, exemptionid=exemptionid)
    banexemption['data']['attributes']['reason'] = reason
    url = f"{BASE_URL}/bans/{banid}/relationships/exemptions"
    return await _make_request(method="PATCH", url=url, data=banexemption)


async def banlist_create(organization_id: int, action: str, autoadd: bool, ban_identifiers: list, native_ban: bool, list_default_reasons: list, ban_list_name: str) -> dict:
    """Creates a new banlist for your targeted organization.
    Documentation: https://www.battlemetrics.com/developers/documentation#link-POST-banList-/ban-lists
    Args:
        organization_id (str): The organization ID.
        action (str): "none", "log", "kick"
        autoadd (bool): true or false
        ban_identifiers (list): ["steamID", "ip"]
        native_ban (bool): Should this be a native ban as well?
        list_default_reasons (list): Default reason for the ban if no new reason is specified
        ban_list_name (str): Name of the banlist
    Returns:
        dict: Returns a dictionary response of the new banlist created.
    """

    url = f"{BASE_URL}/ban-lists"
    data = {
        "data": {
            "type": "banList",
            "attributes": {
                "name": f"{ban_list_name}",
                "action": f"{action}",
                "defaultIdentifiers": ban_identifiers,
                "defaultReasons": list_default_reasons,
                "defaultAutoAddEnabled": str(autoadd).lower(),
                "defaultNativeEnabled": str(native_ban).lower(),
                "nativeBanTTL": None,
                "nativeBanTempMaxExpires": None,
                "nativeBanPermMaxExpires": None
            },
            "relationships": {
                "organization": {
                    "data": {
                        "type": "organization",
                        "id": f"{organization_id}"
                    }
                },
                "owner": {
                    "data": {
                        "type": "organization",
                        "id": f"{organization_id}"
                    }
                }
            }
        }
    }
    return await _make_request(method="POST", url=url, data=data)


async def banlist_accept_invite(code: str, action: str, autoadd: bool, ban_identifiers: list, native_ban: bool, list_default_reasons: list, organization_id: str, organization_owner_id: str) -> dict:
    """Accepts an invitation to subscribe to a banlist.
    Documentation: https://www.battlemetrics.com/developers/documentation#link-POST-banList-/ban-lists/accept-invite
    Args:
        code (str): Invitation code.
        action (str): "none", "log" or "kick"
        autoadd (bool): True or False
        ban_identifiers (list): ["steamID", "ip"]
        native_ban (bool): True or False
        list_default_reasons (list): ["Banned for hacking"]
        organization_id (str): ID of your organization?
        organization_owner_id (str): ID of the owner of the organization
    Returns:
        dict: Response from server.
    """

    url = f"{BASE_URL}/ban-lists/accept-invite"
    data = {
        "data": {
            "type": "banList",
            "attributes": {
                "code": code,
                "action": action,
                "defaultIdentifiers": ban_identifiers,
                "defaultReasons": list_default_reasons,
                "defaultAutoAddEnabled": str(autoadd).lower(),
                "defaultNativeEnabled": str(native_ban).lower(),
                "nativeBanTTL": None,
                "nativeBanTempMaxExpires": None,
                "nativeBanPermMaxExpires": None
            },
            "relationships": {
                "organization": {
                    "data": {
                        "type": "organization",
                        "id": f"{organization_id}"
                    }
                },
                "owner": {
                    "data": {
                        "type": "organization",
                        "id": f"{organization_owner_id}"
                    }
                }
            }
        }
    }
    return await _make_request(method="POST", url=url, data=data)


async def banlist_unsubscribe(banlist_id: str, organization_id: str) -> dict:
    """Unscubscribes from a banlist
    Documentation: https://www.battlemetrics.com/developers/documentation#link-DELETE-banList-/ban-lists/{(%23%2Fdefinitions%2FbanList%2Fdefinitions%2Fidentity)}/relationships/organizations/{(%23%2Fdefinitions%2Forganization%2Fdefinitions%2Fidentity)}
    Args:
        banlist_id (str): ID of the banlist
        organization_id (str): Your organization ID
    Returns:
        dict: Response from server.
    """

    url = f"{BASE_URL}/ban-lists/{banlist_id}/relationships/organizations/{organization_id}"
    return await _make_request(method="DELETE", url=url)


async def banlist_list(self) -> dict:
    """Lists all your banlists for you.
    Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-banList-/ban-lists
    Returns:
        dict: A dictionary response of all the banlists you have access to.
    """

    url = f"{BASE_URL}/ban-lists"
    data = {
        "include": "server,organization,owner",
        "page[size]": "100"
    }
    return await _make_request(method="GET", url=url, data=data)


async def banlist_subbed_orgs(banlist_id: str) -> dict:
    """Lists all the organizations that are subscribed to the targeted banlist. You require manage perms to use this list (or be the owner)
    Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-banList-/ban-lists/{(%23%2Fdefinitions%2FbanList%2Fdefinitions%2Fidentity)}/relationships/organizations
    Args:
        banlist_id (str): The Banlist ID
    Returns:
        dict: A dictionary response of all the organizations subbed to the targeted banlist.
    """

    url = f"{BASE_URL}/ban-lists/{banlist_id}/relationships/organizations"
    data = {
        "include": "server,organization,owner",
        "page[size]": "100"
    }
    return await _make_request(method="GET", url=url, data=data)


async def banlist_sub_info(banlist_id: str, organization_id: str) -> dict:
    """Gets the subscriber information for a specific banlist.

    Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-banList-/ban-lists/{(%23%2Fdefinitions%2FbanList%2Fdefinitions%2Fidentity)}/relationships/organizations/{(%23%2Fdefinitions%2Forganization%2Fdefinitions%2Fidentity)}
    Args:
        banlist_id (str): The ID of the targeted banlist.
        organization_id (_type_): The ID of the targeted organization subscribed to the targeted banlist.
    Returns:
        dict: A dictionary response of all the information requested.
    """

    url = f"{BASE_URL}/ban-lists/{banlist_id}/relationships/{organization_id}"
    data = {
        "include": "organization, owner, server"
    }
    return await _make_request(method="GET", url=url, data=data)


async def banlist_read(banlist_id: str) -> dict:
    """Retrieves the name of a banlist by the banlist id
    Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-banList-/ban-lists/{(%23%2Fdefinitions%2FbanList%2Fdefinitions%2Fidentity)}
    Args:
        banlist_id (str): The ID of the banlist.
    Returns:
        dict: Returns a dictionary response of the requested data.
    """

    url = f"{BASE_URL}/ban-lists/{banlist_id}"
    data = {
        "include": "owner"
    }
    return await _make_request(method="GET", url=url, data=data)


async def banlist_update(banlist_id: str, organization_id: str, action: str = None, autoadd: bool = None, ban_identifiers: list = None, native_ban: bool = None, list_default_reasons: list = None, ban_list_name: str = None) -> dict:
    """Updates the targeted banlist with the altered information you supply
    Documentation: https://www.battlemetrics.com/developers/documentation#link-PATCH-banList-/ban-lists/{(%23%2Fdefinitions%2FbanList%2Fdefinitions%2Fidentity)}/relationships/organizations/{(%23%2Fdefinitions%2Forganization%2Fdefinitions%2Fidentity)}
    Args:
        banlist_id (str): Banlist ID.
        organization_id (str): Organization ID
        Optional paramaters default to the banlist settings.
        action (str, optional): "none", "log" or "kick"
        autoadd (bool, optional): True or False
        ban_identifiers (list, optional): ["steamID", "ip"]
        native_ban (bool, optional): True or False
        list_default_reasons (list, optional): [List of default reasons]
        ban_list_name (str, optional): Name of the banlist
    Returns:
        dict: Dictionary response of the new banlist.
    """

    banlist = await banlist_get_list(banlist_id=banlist_id)
    if not banlist:
        return None
    if action:
        banlist['attributes']['action'] = action
    if autoadd:
        banlist['attributes']['defaultAutoAddEnabled'] = str(
            autoadd).lower()
    if ban_identifiers:
        banlist['attributes']['defaultIdentifiers'] = ban_identifiers
    if native_ban:
        banlist['attributes']['defaultNativeEnabled'] = str(
            native_ban).lower()
    if list_default_reasons:
        banlist['attributes']['defaultReasons'] = list_default_reasons
    if ban_list_name:
        banlist['attributes']['name'] = ban_list_name
    url = f"{BASE_URL}/ban-lists/{banlist_id}/relationships/organizations/{organization_id}"
    return await _make_request(method="PATCH", url=url, data=banlist)


async def banlist_get_list(banlist_id: str) -> dict:
    """Returns the banlist information of the targeted banlist
    Documentation: None. Custom code.
    Args:
        banlist_id (str): The ID of the banlist you want.
    Returns:
        dict: The dictionary response of the targeted banlist.
    """

    url = f"https://api.battlemetrics.com/ban-lists"
    data = {
        "page[size]: 100"
    }
    banlists = await _make_request(method="GET", url=url, data=data)
    for banlist in banlists:
        if banlist['id'] == banlist_id:
            return banlist
    return None


async def activity_logs(filter_search: str = None, filter_servers: int = None, blacklist: str = None, whitelist: str = None) -> dict:
    """Retrieves the activity logs.
    Documentation: There is no documentation on this endpoint unfortunately.
    Args:
        blacklist (str, optional): Example: unknown, playerMessage. Defaults to None.
        whitelist (str, optional): unknown, playerMessage. Defaults to None.
    Returns:
        dict: The activity logs information.
    """
    url = f"{BASE_URL}/activity"
    data = {
        "page[size]": "100",
        "include": "organization,server,user,player"
    }

    if blacklist:
        data['filter[types][blacklist]'] = blacklist
    if whitelist:
        data['filter[types][whitelist]'] = whitelist
    if filter_servers:
        data['filter[servers]'] = filter_servers
    if filter_search:
        data['filter[search]'] = filter_search

    return await _make_request(method="GET", url=url, data=data)


async def user_organization_view() -> dict:
    """Retrieves the organizations the current API token can view.
    Documentation: This endpoint is not documented.

    Returns:
        dict: Returns a dictionary of all the organizations the user can view.
    """
    url = f"{BASE_URL}/organizations"
    data = {
        "page[size]": "100",
        "include": "organizationUser,banList,organizationStats"
    }

    return await _make_request(method="GET", url=url, data=data)