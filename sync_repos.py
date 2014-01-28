#! /usr/bin/python3

import xmlrpc.client

SATELLITE_URL = 'https://pm1.solutions.local/rpc/api'
SATELLITE_LOGIN = ''
SATELLITE_PASSWORD = ''

client = xmlrpc.client.Server(SATELLITE_URL, verbose=0)
key = client.auth.login(SATELLITE_LOGIN, SATELLITE_PASSWORD)

existing_channels = [x['label'] for x in client.channel.list_all_channels(key)]

for channel in existing_channels:
    try:
        client.channel.software.sync_repo(key, channel)
    except Exception:
        raise
