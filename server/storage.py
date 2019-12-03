import datetime
import hashlib
import string
import secrets


max_length_username = 10
min_length_username = 2
min_length_password = 4

class Store:

    def __init__(self):
        self.usernames = {}
        self.messages = []
        self.token_key_map = {}

    def add_msg(self, from_user, to_user, contents):
        if not from_user in self.usernames.keys():
            return f"user '{from_user}' does not exist"
        if from_user == to_user:
            return "source and destination users must be different"
        if to_user in self.usernames.keys():
            self.messages.append(Message(from_user, to_user, contents))
            return ""
        else:
            return f"user '{to_user}' does not exist"

    def make_salt():
        alphabet = string.ascii_letters + string.digits
        salt = ''.join(secrets.choice(alphabet) for i in range(8))
        return salt

    def salt_and_hash(salt, password):
        salted = password + salt
        hashed = salted.encode('utf-8')
        return hashed

    def log_in(self, username, password, address):
        if len(username) > max_length_username:
            return "", f"Username '{username}' is longer than the maximum of {max_length_username} characters"
        if len(username) < min_length_username:
            return "", f"Username '{username}' is shorter than the minimum of {min_length_username} characters"
        if len(password) < min_length_password:
            return "", f"Password is shorter than the minimum of {min_length_password} characters"
        if not username.isalnum():
            return "", f"Username '{username}' is not alphanumeric"
        if username in self.usernames:
            # check if password is correct
            salt, hashed, token = self.usernames[username]
            hashed_from_user = Store.salt_and_hash(salt, password)
            correct = hashed == hashed_from_user
            if correct:
                if token.is_valid(address):
                    token.refresh()
                else:
                    token = TempToken(address)
                    self.usernames[username] = (salt, hashed, token)
                    self.token_key_map[token.key] = username
                return token.key, ""
            else:
                return "", f"Incorrect password/{username} already registered"
        else:
            # make new password
            salt = Store.make_salt()
            token = TempToken(address)
            self.usernames[username] = (salt, Store.salt_and_hash(salt, password), token)
            self.token_key_map[token.key] = username
            return token.key, ""

    def message_to_object(self, msg):
        return {"from": msg.from_user, "to": msg.to_user, "msg": msg.contents}


    def get_history(self, username, other_user):
        if username == other_user:
            return [], "source and destination users must be different"
        if not other_user in self.usernames.keys():
            return [], f"user '{other_user}' does not exist"
        if not username in self.usernames.keys():
            return [], f"user '{username}' does not exist"
        user_messages = list(filter(lambda x: (x.from_user == username) or (
            x.to_user == username), self.messages))
        relevant_messages = list(filter(lambda x: (x.from_user == other_user) or (
            x.to_user == other_user), user_messages))
        return list(map(self.message_to_object, relevant_messages)), ""

    def token_to_username(self, token_string, address):
        if token_string in self.token_key_map:
            username = self.token_key_map[token_string]
            salt, hashed, token = self.usernames[username]
            if token.is_expired():
                return username, "Token is expired"
            if token.is_valid(address):
                return username, ""
            else:
                return username, "IP address invalid for token"
        else:
            return "", "Token not found"


class Message:
    def __init__(self, from_user, to_user, contents, timestamp=datetime.datetime.now()):
        self.from_user = from_user
        self.to_user = to_user
        self.contents = contents
        self.timestamp = timestamp

class TempToken:
    def __init__(self, address):
        self.timestamp = datetime.datetime.now()
        self.expiration = self.timestamp + datetime.timedelta(hours=1)
        self.address = address
        alphabet = string.ascii_letters + string.digits
        self.key = ''.join(secrets.choice(alphabet) for i in range(24))

    def is_valid(self, address):
        return address == self.address and not self.is_expired()

    def is_expired(self):
        return datetime.datetime.now() > self.expiration

    def refresh(self):
        self.timestamp = datetime.datetime.now()
        self.expiration = self.timestamp + datetime.timedelta(hours=1)
