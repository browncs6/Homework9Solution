#!/usr/bin/python3

import os

import eventlet
from eventlet import wsgi
from eventlet import websocket
from enum import Enum, unique
from urllib import parse
import json
import sys
import traceback
import re


from storage import Store
from wslogger import WebsocketLogger
PORT = 7000

participants = {}
offline = set()
store = Store()


@unique
class MESSAGE_TYPE(Enum):
    CONNECT = 0
    MSG = 1
    HISTORY = 2
    LIST = 3
    SENT = 4
    ERROR = 5


@unique
class ERROR_TYPE(Enum):
    LOGIN_ERROR = 0
    INVALID_MESSAGE_TYPE = 1
    UNKNOWN_MESSAGE_TYPE = 2
    MALFORMED_MESSAGE = 3
    ILLEGAL_MESSAGE = 4
    MALFORMED_URL = 5
    TOKEN_ERROR = 6

@websocket.WebSocketWSGI
def handle(ws):
    token = ws.environ['QUERY_STRING'].split("=")[1]
    username, err = store.token_to_username(token, ws.environ["REMOTE_ADDR"])
    wsl = WebsocketLogger(ws, username)
    if err != "":
        wsl.send(make_error(ERROR_TYPE.TOKEN_ERROR, err))
        return;
    participants[username] = wsl
    offline.discard(username)
    for name, socket in participants.items():
        socket.send(make_list())
    try:
        while True:
            m = wsl.wait()
            if m is None:
                break
            else:
                handle_message(username, m)
    except:
        print(traceback.format_exc())
    finally:
        participants.pop(username, None)
        offline.add(username)
        for name, socket in participants.items():
            socket.send(make_list())


def handle_message(from_user, m):
    wsl = participants[from_user]
    wsl.send(make_error(ERROR_TYPE.INVALID_MESSAGE_TYPE,
                            "Do not send messages to the websocket. POST messages to /chat."))

def dict_shape_err(d, expected_keys, is_payload):
    error_suffix_keys = "payload" if is_payload else "all messages"
    error_suffix_count = "payload" if is_payload else "message"
    for key in expected_keys:
        if not key in d.keys():
            return f"'{key}' must be present in {error_suffix_keys}"
    if len(d.keys()) != len(expected_keys):
        return f"too many keys in {error_suffix_count}"
    return ""

def make_payload_err(from_user, payload, expected_keys):
    err = dict_shape_err(payload, expected_keys, True)
    if err != "":
        return make_error(ERROR_TYPE.MALFORMED_MESSAGE, err)
    return None

def handle_msg(from_user, m):
    err = make_payload_err(from_user, m["payload"], ["to", "msg"])
    if err != None:
        return err
    err = store.add_msg(from_user, m["payload"]["to"], m["payload"]["msg"])
    if err == "":
        if m["payload"]["to"] in participants.keys():
            participants[m["payload"]["to"]].send(
                make_msg(from_user, m["payload"]["msg"]))
        return make_sent()
    else:
        return make_error(
            ERROR_TYPE.ILLEGAL_MESSAGE, err)

def handle_history(from_user, m):
    err = make_payload_err(from_user, m["payload"], ["user"])
    if err != None:
        return err
    history, err = store.get_history(from_user, m["payload"]["user"])
    if err != "":
        return make_error(
            ERROR_TYPE.ILLEGAL_MESSAGE, err)
    return make_history(history)

def make_connect(token):
    return make_message(MESSAGE_TYPE.CONNECT, {"token": token})


def make_msg(from_user, msg):
    return make_message(MESSAGE_TYPE.MSG, {"from": from_user, "msg": msg})


def make_history(history):
    return make_message(
        MESSAGE_TYPE.HISTORY, history
    )


def make_list():
    return make_message(MESSAGE_TYPE.LIST, {"online": list(participants.keys()), "offline": list(offline)})


def make_sent():
    return {"type": MESSAGE_TYPE.SENT.value}


def make_error(errtype, msg):
    return make_message(MESSAGE_TYPE.ERROR, {"type": errtype.value, "msg": msg})


def make_message(message_type, payload):
    return {"type": message_type.value, "payload": payload}

def handle_post(environ):
    try:
        request_body_size = int(environ.get('CONTENT_LENGTH', 0))
    except (ValueError):
        request_body_size = 0
    m = json.loads(environ['wsgi.input'].read(request_body_size).decode("utf-8"))
    address = environ["REMOTE_ADDR"]

    if "token" in m:
        err = dict_shape_err(m, ["type", "payload", "token"], False)
        if err != "":
            return make_error(ERROR_TYPE.MALFORMED_MESSAGE, err)
        from_user, err = store.token_to_username(m["token"], address)
        if err != "":
            return make_error(ERROR_TYPE.TOKEN_ERROR, err)
        if (m["type"] == MESSAGE_TYPE.MSG.value):
            return handle_msg(from_user, m)
        elif (m["type"] == MESSAGE_TYPE.HISTORY.value):
            return handle_history(from_user, m)
        else:
            return make_error(ERROR_TYPE.INVALID_MESSAGE_TYPE, 
                "The only message types that are valid to send to the backend are CONNECT, MSG, and HISTORY")
    else:
        err = dict_shape_err(m, ["type", "payload"], False)
        if err != "":
            return make_error(ERROR_TYPE.MALFORMED_MESSAGE, err)
        if (m["type"] != MESSAGE_TYPE.CONNECT.value):
            return make_error(ERROR_TYPE.MALFORMED_MESSAGE, "The only message that may not have a token is a CONNECT message")
        err = dict_shape_err(m["payload"], ["username", "password"], True)
        if err != "":
            return make_error(ERROR_TYPE.MALFORMED_MESSAGE, err)
        if m["payload"]["username"] in participants:
            return make_error(ERROR_TYPE.LOGIN_ERROR, f"'{m['payload']['username']}' is logged in elsewhere")
        token, err = store.log_in(m["payload"]["username"], m["payload"]["password"], address)
        if err != "":
            return make_error(ERROR_TYPE.LOGIN_ERROR, err)
        return make_connect(token)
    
    return make_error(ERROR_TYPE.UNKNOWN_MESSAGE_TYPE, "Not set up yet")



def dispatch(environ, start_response):
    """Resolves to the web page or the websocket depending on the path."""
    if environ['PATH_INFO'] == '/websocket':
        querystr = environ['QUERY_STRING']
        match = re.search("^token=[a-zA-Z0-9]{24}$", querystr)
        if match == None:
            start_response('200 OK', [('content-type', 'application/json'), ("Access-Control-Allow-Origin", "*")])
            return [json.dumps(make_error(ERROR_TYPE.MALFORMED_URL, "/websocket must also have ?token=<your token> at the end"))]
        else:
            token = querystr.split("=")[1]
            username, err = store.token_to_username(token, environ["REMOTE_ADDR"])
            if err != "":
                print(f"Token error: {err}")
                start_response('200 OK', [('content-type', 'application/json'), ("Access-Control-Allow-Origin", "*")])
                return [json.dumps(make_error(ERROR_TYPE.TOKEN_ERROR, f"Token error: {err}"))]
            if username in participants:
                return [json.dumps(make_error(ERROR_TYPE.TOKEN_ERROR, f"Token is already being used"))]
        return handle(environ, start_response)
    if environ['PATH_INFO'] == '/chat':
        start_response('200 OK', [('content-type', 'application/json'), ("Access-Control-Allow-Origin", "*")])
        return [json.dumps(handle_post(environ))]
    else:
        start_response('200 OK', [('content-type', 'text/html'), ("Access-Control-Allow-Origin", "*")])
        return ["Please either use /websocket for accessing the websocket or /chat for accessing the REST api. This server does not serve HTML."]


if __name__ == "__main__":
    # run an example app from the command line
    listener = eventlet.listen(('127.0.0.1', PORT))
    # print("\nVisit http://localhost:7000/ in your websocket-capable browser.\n")
    wsgi.server(listener, dispatch)
