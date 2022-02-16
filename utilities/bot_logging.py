import requests
import sys
import json

class BotLogging():
    def __init__(self, url, username, channel):
        self.url = url
        self.username = username
        self.channel = channel
    
    def send_message(self, message):
        data = {
            "username": self.username,
            "icon_emoji": ":satellite:",
            "channel" : self.channel,
            "text": message
        }

        byte_length = str(sys.getsizeof(data))
        headers = {'Content-Type': "application/json", 'Content-Length': byte_length}
        result = requests.post(self.url, data=json.dumps(data), headers=headers)

        try:
            result.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(err)