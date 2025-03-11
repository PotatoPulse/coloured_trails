from utils.globals import COLOURS, START_CHIPS
from players.player_base import Player
from board import Board
from pathfinder import find_best_path
import numpy as np

class GameMaster():
    def __init__(self, initiator: Player, responder: Player, board: Board):
        self.initiator = initiator      # player that always makes the first offer
        self.responder = responder      # player that always responds to the first offer
        self.board = board
        self.initiator.board = board
        self.responder.board = board
        
        self.initiator.role = "initiator"
        self.responder.role = "responder"
        
    def setup(self):
        self.board.new_board()          # creates a new playing board
        
        # setting up initial chips for players
        self.initiator.chips = [np.random.choice(COLOURS) for _ in range(START_CHIPS)]
        self.responder.chips = [np.random.choice(COLOURS) for _ in range(START_CHIPS)]
        
        # giving players access to information of what chips are in play
        all_chips = self.initiator.chips + self.responder.chips
        self.initiator.all_chips = all_chips
        self.responder.all_chips = all_chips
        
        # assign goal positions to players
        self.initiator.goal = self.board.random_pos()
        self.responder.goal = self.board.random_pos()

    def handle_offer(self, offer, offer_maker):
        print(f"Offer accepted --- offer: {offer}, made by: {offer_maker}")
        # obtain initiator and responder index in offer
        initiator = 0 if offer_maker == "initiator" else 1
        responder = 1 - initiator
            
        # remove chips given away by each player
        for chip in offer[initiator]:
            self.initiator.chips.remove(chip)
            
        for chip in offer[responder]:
            self.responder.chips.remove(chip)
        
        # add chips received from other player
        self.initiator.chips.extend(offer[initiator])
        self.responder.chips.extend(offer[responder])
            
        
    def play(self):
        self.setup()
        
        players = [self.initiator, self.responder]
        
        i = 0
        while True:
            offer = None
            accepted = None
            
            # obtain index for turns
            sender = i % 2
            receiver = 1 - sender
            
            offer = players[sender].offer_out()
            
            if offer == ((), ()): # player decides to end negotiations
                break
            else:
                accepted = players[receiver].offer_in(offer)
                players[sender].offer_evaluate(offer, accepted)
                
                if accepted:
                    self.handle_offer(offer, offer_maker=players[sender].role)
            
            i += 1
            
        self.evaluate(penalty=i)

    def evaluate(self, penalty):
        # Manhattan distance from best attainable position to goal and unused chips
        distance_initiator, unused_chips_initiator = find_best_path(self.initiator.chips, self.initiator.goal, self.board)
        distance_responder, unused_chips_responder = find_best_path(self.responder.chips, self.responder.goal, self.board)
        
        print(self.board)
        
        print(f"GAME ENDED: distance initiator: {distance_initiator}, distance responder: {distance_responder}")
        print(f"initiator goal: {self.initiator.goal}, responder goal: {self.responder.goal}")
        print(f"initiator chips: {self.initiator.chips}, responder chips: {self.responder.chips} -- total count: {len(self.initiator.chips) + len(self.responder.chips)}")
        
        win_score_initiator = 500 if distance_initiator == 0 else 0
        win_score_responder = 500 if distance_responder == 0 else 0
        score_initiator = distance_initiator * 100 - penalty + 50 * unused_chips_initiator + win_score_initiator
        score_responder = distance_responder * 100 - penalty + 50 * unused_chips_responder + win_score_responder
        
        self.initiator.evaluate(score_initiator)
        self.responder.evaluate(score_responder)