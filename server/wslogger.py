import json


class WebsocketLogger:

    def __init__(self, ws, username=None):
        self.ws = ws
        self.username = username

    def send(self, m):
        print(f"SENDING {m} TO {self.username}")
        self.ws.send(json.dumps(m).replace("<", "&lt;").replace(">", "&gt;"))

    def wait(self):
        raw = self.ws.wait()
        if raw == None:
            print(f"{self.username} DISCONNECTED")
            return None
        else:
            print(f"RECEIVED {raw} FROM {self.username}")
            return json.loads(raw)

    def set_username(self, username):
        if self.username == None:
            self.username = username
        else:
            print(f"USERNAME ALREADY SET TO {self.username}")
