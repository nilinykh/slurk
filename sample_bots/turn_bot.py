#!/bin/env python

import argparse
import sys

from random import randint
from socketIO_client import SocketIO, BaseNamespace

chat_namespace = None
users = {}
self_id = None
turn_done = []


def add_user(room, id):
    global users

    room = int(room)
    id = int(id)
    print("adding user", id, "to room", room)

    if room == 1:
        return

    if room not in users:
        users[room] = []
    users[room].append(id)

    # remove id duplicates
    users[room] = list(set(users[room]))


class ChatNamespace(BaseNamespace):

    def on_joined_room(self,data):
        global users, self_id

        self_id = data['self']['id']

        for user in data['users']:
            if user['id'] != self_id:
                add_user(data['room']['id'], user['id'])

        # start "game" as soon as there are two users in the meetup room
        room = data['room']['id']
        if room in users and len(users[room]) == 2:
            self.ask_question(data)

    @staticmethod
    def on_status(data):
        global users

        if data['user']['id'] != self_id:
            add_user(data['room']['id'], data['user']['id'])

    def on_new_task_room(self, data):
        print("hello!!! I have been triggered!")
        if data['task']['name'] != 'meetup':
            return

        room = data['room']
        print("Joining room", room['name'])
        self.emit('join_task', {'room': room['id']})
        self.emit("command", {'room': room['id'], 'data': ['listen_to', 'message']})
        self.emit("command", {'room': room['id'], 'data': ['listen_to', 'show']})
        self.emit("command", {'room': room['id'], 'data': ['listen_to', 'hide']})

    # ask question and hide input area of the 'listener'
    def ask_question(self, data):
        global turn_done
        
        room = data['room']['id']
        users = [(user['id'], user['name']) for user in data['users']]
        active, passive = users[0], users[1]
        question = self.question()
        self.emit("text", {"msg": f"Welcome {active[1]} and {passive[1]}!", 
                           "room": room})
        self.emit("text", {"msg": f"{active[1]}, please answer the following question: " +
                                  question,
                           "room": room})
        self.on_hide({"data": ["input"], "user": passive[0], "room": room})

    def question(self):
        return "Put question here.."

    def on_message(self, data):
        global users, turn_done

        room = data["user"]["latest_room"]["id"]
        if data["user"]["name"] == "TurnBot" or room in turn_done:
            return
        ids = [user for user in users[room]]
        turn_done.append(room)
        for user in ids:
            self.on_show({"data": ["input"], "user": user, "room": room})

    def on_show(self, data):
        for parameter in data['data']:
            if parameter == "input" or parameter == "all":
                self.emit('update_permissions', {"user": data["user"],
                                                 "room": data["room"],
                                                 "input": True})

    def on_hide(self, data):
        for parameter in data['data']:
            if parameter == "input" or parameter == "all":
                self.emit('update_permissions', {"user": data["user"],
                                                 "room": data["room"],
                                                 "input": False})


class LoginNamespace(BaseNamespace):
    @staticmethod
    def on_login_status(data):
        global chat_namespace
        if data["success"]:
            chat_namespace = socketIO.define(ChatNamespace, '/chat')
        else:
            print("Could not login to server")
            sys.exit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Example MultiBot')
    parser.add_argument('token',
                        help='token for logging in as bot ' +
                        '(see SERVURL/token)')
    parser.add_argument('-c', '--chat_host',
                        help='full URL (protocol, hostname; ' +
                        'ending with /) of chat server',
                        default='http://localhost')
    parser.add_argument('-p', '--chat_port', type=int,
                        help='port of chat server', default=5000)
    args = parser.parse_args()

    with SocketIO(args.chat_host, args.chat_port) as socketIO:
        login_namespace = socketIO.define(LoginNamespace, '/login')
        login_namespace.emit('connectWithToken', {
                             'token': args.token, 'name': "TurnBot"})
        socketIO.wait()

