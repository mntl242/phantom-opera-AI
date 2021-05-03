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
set up fantom logging
"""
fantom_logger = logging.getLogger()
fantom_logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(asctime)s :: %(levelname)s :: %(message)s", "%H:%M:%S")
# file
if os.path.exists("./logs/fantom.log"):
    os.remove("./logs/fantom.log")
file_handler = RotatingFileHandler('./logs/fantom.log', 'a', 1000000, 1)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
fantom_logger.addHandler(file_handler)
# stream
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.WARNING)
fantom_logger.addHandler(stream_handler)


class Player():

    fantom= None

    def __init__(self):

        self.end = False
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def connect(self):
        self.socket.connect((host, port))

    def reset(self):
        self.socket.close()
    
    def find_index(self, lst, key, value):
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

    def state_list(self, lst, flag):
        """
        returns a list of dicts of characters
        if flag == True, they're suspect, else they're innocent
        """
        res = []
        for dic in lst:
            if dic["suspect"] == flag:
                res.append(dic)
        return res

    def algo(self, question):
        data = question["data"]
        game_state = question["game state"]
        self.fantom = game_state["fantom"]
        all_position = self.find_key(game_state['characters'], 'position')
        suspect_list = self.state_list(game_state['characters'], True)
        shadow = game_state['shadow']
        # always plays character "red" first when available
        if question["question type"] == "select character":
            red_index = self.find_index(data, "color", "red")
            if red_index != None:
                return red_index
        # activates "grey" power in a room with the most people
        if question["question type"] == "grey character power":
            res = max(all_position,key=all_position.count)
            if res != shadow:
                return [i for i, x in enumerate(data) if x == res][0]
        # activates "white" power to spread people around
        if question["question type"] == "activate white power":
            return 1
        # activates "black" power if the room has shadow
        if question["question type"] == "activate black power":
            black_position= all_position[self.find_index(game_state['characters'], "color", "black")]
            if game_state["shadow"] == black_position:
                return 1
            return 0
        # never activates "purple" power
        if question["question type"] == "activate purple power":
            return 0
        # select a position where there is shadow or no other character
        if question["question type"] == "select position":
            res = [x for x in data if x not in list(set(all_position))]
            if shadow in data:
                return [i for i, x in enumerate(data) if x == shadow][0]
            elif res != []:
                #print(data, res)
                choice = random.choice(res)
                return [i for i, x in enumerate(data) if x == choice][0]
        # if no condition was found, play random value
        return random.randint(0, len(question["data"])-1)



    def answer(self, question):
        # work
        data = question["data"]
        game_state = question["game state"]
        response_index = self.algo(question)
        # log
        fantom_logger.debug("|\n|")
        fantom_logger.debug("fantom answers")
        fantom_logger.debug(f"question type ----- {question['question type']}")
        fantom_logger.debug(f"data -------------- {data}")
        fantom_logger.debug(f"response index ---- {response_index}")
        fantom_logger.debug(f"response ---------- {data[response_index]}")

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
