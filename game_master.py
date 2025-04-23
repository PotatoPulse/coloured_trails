from utils.globals import START_CHIPS, CHIPS
from players.player_base import Player
from board import Board
from pathfinder import find_best_path, manhattan_distance
import random
import os
import csv

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
            
            if player.type in ("DQN", "FOToM"):
                player.transition = [None]*4
        
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
        self.init_log_file()
        self.setup()
        
        self.max_games = max_games
        
        players = [self.initiator, self.responder]
        
        self.games = 0
        i = 0
        self.offers_accepted = 0
        while True:
            for idx, player in enumerate(players):
                if player.type == "FOToM":
                    if player.goal_guess == players[1 - idx].goal:
                        print("## Correct goal guessed ##")
            
            if self.games >= max_games:
                break
            
            if i >= 100:
                print("~ Max negotiations reached ~")
                self.games += 1
                self.evaluate(penalty=i)
                self.setup()
                i = 0
            
            offer = None
            accepted = None
            
            # obtain index for turns
            sender = i % 2
            receiver = 1 - sender
            
            offer = players[sender].offer_out()
            # print("offer: ", offer, f"made by: {players[sender].name}")
            
            if offer == (players[sender].chips, players[receiver].chips): # player decides to end negotiations
                print(f"Player {players[sender].name} ended negotiations")
                self.games += 1
                self.evaluate(penalty=i)
                self.setup()
                i = 0
            else:
                accepted = players[receiver].offer_in(offer)
                players[sender].offer_evaluate(offer, accepted)
                
                if accepted:
                    self.offers_accepted += 1
                    self.handle_offer(offer, offer_maker=players[sender].role)
                    self.games += 1
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
        score_initiator = steps_initiator * 100 + unused_chips_initiator * 50 + win_score_initiator
        score_responder = steps_responder * 100 + unused_chips_responder * 50 + win_score_responder
        
        self.total_score_initiator += score_initiator
        self.total_score_responder += score_responder
        
        print("Game ", round((self.games/self.max_games)*100, 2),"% completed")
        
        self.log_scores()
        
    def init_log_file(self):
        log_file = f'logs/log-{self.initiator.type}-{self.responder.type}.csv'
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        with open(log_file, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['total_score_initiator', 'total_score_responder', 'offers_accepted'])
        
    def log_scores(self):
        log_file = f'logs/log-{self.initiator.type}-{self.responder.type}.csv'
        
        with open(log_file, "a", newline='') as csv_file:
            writer = csv.writer(csv_file)
        
            writer.writerow([self.total_score_initiator, self.total_score_responder, self.offers_accepted])