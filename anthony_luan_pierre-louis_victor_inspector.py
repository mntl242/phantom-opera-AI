import json
import logging
import os
import random
import socket
from logging.handlers import RotatingFileHandler

import protocol

host = "localhost"
port = 12000
# HEADERSIZE = 10

"""
set up inspector logging
"""
inspector_logger = logging.getLogger()
inspector_logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(asctime)s :: %(levelname)s :: %(message)s", "%H:%M:%S")
# file
if os.path.exists("./logs/inspector.log"):
    os.remove("./logs/inspector.log")
file_handler = RotatingFileHandler('./logs/inspector.log', 'a', 1000000, 1)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
inspector_logger.addHandler(file_handler)
# stream
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.WARNING)
inspector_logger.addHandler(stream_handler)


class Player():

    def __init__(self):

        self.end = False
        # self.old_question = ""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def connect(self):
        self.socket.connect((host, port))

    def reset(self):
        self.socket.close()

    def find_dict_index(self, lst, key, value):
        """
        returns the index of an element in a list of dict for a given key/value pair
        """
        for i, dic, in enumerate(lst):
            if dic[key] == value:
                return i
        return None

    def find_key(self, lst, key):
        """
        returns a list containing all values for given key from a list of dicts
        """
        res = [sub[key] for sub in lst]
        return res

    def innocence_list(self, lst, flag):
        """
        returns a list of dicts of characters
        if flag == True, they're suspect, else they're innocent
        """
        res = []
        for dic in lst:
            if dic["suspect"] == flag:
                res.append(dic)
        return res

    def algorithm(self, question):
        data = question["data"]
        game_state = question["game state"]
        # all characters' current position
        all_position = self.find_key(game_state['characters'], 'position')
        # remaining suspects and their positions
        suspect_list = self.innocence_list(game_state['characters'], True)
        suspect_position = self.find_key(suspect_list, 'position')
        # innocents and their positions
        innocent_list = self.innocence_list(game_state['characters'], True)
        innocent_position = self.find_key(innocent_list, 'position')
        # always plays character "red" first when available
        if question["question type"] == "select character":
            red_index = self.find_dict_index(data, "color", "red")
            if red_index != None:
                return red_index
        # activates "grey" power in a random room with no suspect
        if question["question type"] == "grey character power":
            possible_position = [i for i in range(10)]
            res = [x for x in possible_position if x not in list(set(suspect_position))]
            if res != []:
                return random.choice(res)
        # characters go into lit rooms with suspects
        if question["question type"] == "select position":
            res = [x for x in data if x in list(set(suspect_position)) and x != game_state['shadow']]
            if res != []:
                return random.choice(res)
        # if no condition was found, play random value
        return random.randint(0, len(question["data"])-1)

    def answer(self, question):
        # work
        data = question["data"]
        game_state = question["game state"]
        response_index = self.algorithm(question)
        # log
        inspector_logger.debug("|\n|")
        inspector_logger.debug(f"game state ----- {question['game state']['characters']}")
        inspector_logger.debug("inspector answers")
        inspector_logger.debug(f"question type ----- {question['question type']}")
        inspector_logger.debug(f"data -------------- {data}")
        inspector_logger.debug(f"response index ---- {response_index}")
        inspector_logger.debug(f"response ---------- {data[response_index]}")
        return response_index

    def handle_json(self, data):
        data = json.loads(data)
        response = self.answer(data)
        # send back to server
        bytes_data = json.dumps(response).encode("utf-8")
        protocol.send_json(self.socket, bytes_data)

    def run(self):

        self.connect()

        while self.end is not True:
            received_message = protocol.receive_json(self.socket)
            if received_message:
                self.handle_json(received_message)
            else:
                print("no message, finished learning")
                self.end = True


p = Player()

p.run()
