from utils.globals import COLOURS, START_CHIPS
from players.player_base import Player
from board import Board
import numpy as np

class GameMaster():
    def __init__(self, initiator: Player, responder: Player, board: Board):
        self.initiator = initiator      # player that always makes the first offer
        self.responder = responder      # player that always responds to the first offer
        self.board = board
        
    def setup(self):
        self.board.new_board()          # creates a new playing board
        
        # setting up initial chips for players
        self.initiator.chips = [np.random.choice(COLOURS) for _ in range(START_CHIPS)]
        self.responder.chips = [np.random.choice(COLOURS) for _ in range(START_CHIPS)]
        
    def handle_offer(self, offer, offer_maker):
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
        
        i = 0
        while True:
            if i % 2 == 0:
                offer = self.initiator.offer_out()
                
                if offer == None: # plater decides to end negotiations
                    break
                else:
                    response = self.responder.offer_in(offer)
                    self.initiator.offer_evaluate(offer, response)
                    
                    if response == "accept":
                        self.handle_offer(offer, offer_maker="initiator")
                        pass
            else:
                offer = self.responder.offer_out()
                
                if offer == None:   # player decides to end negotiations
                    break
                else:
                    response = self.initiator.offer_in(offer)
                    self.responder.offer_evaluate(offer, response)
                    if response == "accept":
                        self.handle_offer(offer, offer_maker="responder")
                        pass
            
            i += 1
            
        self.evaluate(penalty=i)
            
    def evaluate(self, penalty):
        pass