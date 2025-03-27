from utils.globals import COLOURS, START_CHIPS, CHIPS
from players.player_base import Player
from board import Board
from pathfinder import find_best_path, manhattan_distance
import random

class GameMaster():
    def __init__(self, initiator: Player, responder: Player, board: Board):
        self.initiator = initiator      # player that always makes the first offer
        self.responder = responder      # player that always responds to the first offer
        self.board = board
        self.initiator.board = board
        self.responder.board = board
        
        self.initiator.role = "initiator"
        self.responder.role = "responder"
        
        self.total_score_initiator = 0
        self.total_score_responder = 0
        
    def setup(self):
        self.board.new_board()          # creates a new playing board
        
        for player in [self.initiator, self.responder]:
            # assign goal positions to players
            player.goal, player.goal_idx = self.board.random_goal_pos()
            
            # give players access to board
            player.board = self.board
            if player.type == "DQN":
                player.compute_r_table()
        
        chips = CHIPS.copy()
        
        # setting up initial chips for players
        self.initiator.chips = random.sample(chips, START_CHIPS)
        for chip in self.initiator.chips:
            chips.remove(chip)
        self.responder.chips = chips

    def handle_offer(self, offer, offer_maker):
        print(f"Offer accepted --- offer: {offer}, made by: {offer_maker}")
        # obtain initiator and responder index in offer
        initiator = 0 if offer_maker == "initiator" else 1
        responder = 1 - initiator
        
        self.initiator.chips = offer[initiator]
        self.responder.chips = offer[responder]
        
    def play(self, max_games):
        self.setup()
        
        players = [self.initiator, self.responder]
        
        games = 0
        i = 0
        while True:
            if games >= max_games:
                break
            
            offer = None
            accepted = None
            
            # obtain index for turns
            sender = i % 2
            receiver = 1 - sender
            
            offer = players[sender].offer_out()
            
            if offer == (players[sender].chips, players[receiver].chips): # player decides to end negotiations
                # break
                games += 1
                self.evaluate(penalty=i)
                self.setup()
                i = 0
            else:
                accepted = players[receiver].offer_in(offer)
                players[sender].offer_evaluate(offer, accepted)
                
                if accepted:
                    self.handle_offer(offer, offer_maker=players[sender].role)
                    games += 1
                    self.evaluate(penalty=i)
                    self.setup()
                    i = 0
            
            i += 1
        
        self.evaluate(penalty=i)
        print("Total score initiator:", self.total_score_initiator)
        print("Total score responder:", self.total_score_responder)

    def evaluate(self, penalty):
        print('')
        # Manhattan distance from best attainable position to goal and unused chips
        start_distance_initiator = manhattan_distance(self.board.start, self.initiator.goal)
        distance_initiator, unused_chips_initiator = find_best_path(self.initiator.chips, self.initiator.goal, self.board)
        start_distance_responder = manhattan_distance(self.board.start, self.responder.goal)
        distance_responder, unused_chips_responder = find_best_path(self.responder.chips, self.responder.goal, self.board)
        
        print(self.board)
        
        print(f"GAME ENDED: distance initiator: {distance_initiator}, distance responder: {distance_responder}")
        print(f"initiator goal: {self.initiator.goal}, responder goal: {self.responder.goal}")
        print(f"initiator chips: {self.initiator.chips}, responder chips: {self.responder.chips} -- total count: {len(self.initiator.chips) + len(self.responder.chips)}")
        
        win_score_initiator = 500 if distance_initiator == 0 else 0
        win_score_responder = 500 if distance_responder == 0 else 0
        steps_initiator = start_distance_initiator - distance_initiator
        steps_responder = start_distance_responder - distance_responder
        
        # steps towards goal are worth 100 points, unused chips are worth 50 points, 
        # reaching goal is worth 500 points and each round of negotiations is a penalty of 1
        score_initiator = steps_initiator * 100 - penalty + 50 * unused_chips_initiator + win_score_initiator
        score_responder = steps_responder * 100 - penalty + 50 * unused_chips_responder + win_score_responder
        
        self.initiator.evaluate(score_initiator)
        self.responder.evaluate(score_responder)
        
        self.total_score_initiator += score_initiator
        self.total_score_responder += score_responder