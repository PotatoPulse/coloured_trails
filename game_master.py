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
        self.initiator.chips = [x for x in self.initiator.chips if x not in set(offer[initiator])]
        self.responder.chips = [x for x in self.initiator.chips if x not in set(offer[responder])]
        
        # add chips received from other player
        self.initiator.chips.extend(offer[initiator])
        self.responder.chips.extend(offer[responder])
            
        
    def play(self):
        self.setup()
        
        i = 1
        while True:
            offer = None
            accepted = None
            if (i % 2) == 1:
                offer = self.initiator.offer_out()
                
                if offer == None: # plater decides to end negotiations
                    break
                else:
                    accepted = self.responder.offer_in(offer)
                    self.initiator.offer_evaluate(offer, accepted)
                    
                    if accepted:
                        self.handle_offer(offer, offer_maker="initiator")
            else:
                offer = self.responder.offer_out()
                
                if offer == None:   # player decides to end negotiations
                    break
                else:
                    accepted = self.initiator.offer_in(offer)
                    self.responder.offer_evaluate(offer, accepted)
                    if accepted:
                        self.handle_offer(offer, offer_maker="responder")
            
            i += 1
            
        self.evaluate(penalty=i)
            
    def evaluate(self, penalty):
        best_position_initiator, unused_chips_initiator = find_best_path(self.initiator.chips, self.initiator.goal, self.board)
        best_position_responder, unused_chips_responder = find_best_path(self.responder.chips, self.responder.goal, self.board)
        distance_initiator = None #get_distance(best_position_initiator, self.initiator.goal)
        distance_responder = None #get_distance(best_position_responder, self.responder.goal)
        
        win_score_initiator = 100 if distance_initiator == 0 else 0
        win_score_responder = 100 if distance_responder == 0 else 0
        score_initiator = distance_initiator * 10 - penalty + 5 * unused_chips_initiator + win_score_initiator
        score_responder = distance_responder * 10 - penalty + 5 * unused_chips_responder + win_score_responder
        
        self.initiator.evaluate(score_initiator)
        self.responder.evaluate(score_responder)
        pass