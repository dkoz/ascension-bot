import aiohttp
import base64
import socket

class AsaProtocol:
    def __init__(self, client_id, client_secret, deployment_id, epic_api):
        self.client_id = client_id
        self.client_secret = client_secret
        self.deployment_id = deployment_id
        self.epic_api = epic_api

    async def query(self, host, port):
        host = host if self.is_ip_address(host) else self.resolve_dns(host)
        try:
            access_token = await self.get_access_token()
            server_info = await self.query_server_info(access_token, host, port)

            sessions = server_info.get('sessions', [])
            if not sessions:
                raise Exception("No sessions found")

            desired_session = sessions[0]

            attributes = desired_session.get('attributes', {})
            settings = desired_session.get('settings', {})

            result = {
                'name': attributes.get('CUSTOMSERVERNAME_s', 'Unknown Server'),
                'nameversion': attributes.get('SESSIONNAMEUPPER_s', 'Unknown Server'),
                'map': attributes.get('MAPNAME_s', 'Unknown Map'),
                'password': attributes.get('SERVERPASSWORD_b', False),
                'numplayers': desired_session.get('totalPlayers', 0),
                'maxplayers': settings.get('maxPublicPlayers', 0),
                'connect': attributes.get('ADDRESS_s', '') + ':' + str(port),
                'ping': attributes.get('EOSSERVERPING_l', "Unknown Ping"),
                'platform': attributes.get('SERVERPLATFORMTYPE_s', "Unknown Platform"),
                'raw': desired_session
            }
        except Exception as e:
            result = {
                'raw': {'error': str(e)},
                'name': 'Unknown Server',
                'map': 'Unknown Map',
                'password': False,
                'numplayers': 0,
                'maxplayers': 0,
                'connect': f"{host}:{port}",
                'ping': 'Unknown Ping'
            }

        return result

    async def get_access_token(self):
        url = f"{self.epic_api}/auth/v1/oauth/token"
        auth = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        headers = {
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        body = f"grant_type=client_credentials&deployment_id={self.deployment_id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=body) as response:
                response.raise_for_status()
                data = await response.json()
                return data['access_token']

    async def query_server_info(self, access_token, host, port):
        url = f"{self.epic_api}/matchmaking/v1/{self.deployment_id}/filter"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        criteria = [
            {"key": "attributes.ADDRESS_s", "op": "EQUAL", "value": host},
            {"key": "attributes.ADDRESSBOUND_s", "op": "CONTAINS", "value": f":{port}"}
        ]

        body = {"criteria": criteria}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=body) as response:
                response.raise_for_status()
                return await response.json()

    def is_ip_address(self, host):
        try:
            socket.inet_aton(host)
            return True
        except socket.error:
            return False

    def resolve_dns(self, host):
        try:
            return socket.gethostbyname(host)
        except socket.gaierror:
            return host