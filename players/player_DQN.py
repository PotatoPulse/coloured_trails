from utils.globals import BOARD_SIZE
from board import Board
from players.player_base import Player
from pathfinder import find_best_path, manhattan_distance
import torch
import torch.nn as nn

class DQNPlayer(Player):
    def __init__(self, epsilon_start, epsilon_end, board: Board, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.epsilon_start = epsilon_start  # epsilon at start of training
        self.epsilon_end = epsilon_end      # epsilon at end of training, lowered by epsilon decay
        self.board = Board
        
        # number of states = possible board configurations + possible goal states 
        # + current chip distribution + chip distribution resulting from last offer
        n_states = 1 + 12 + 8 + 8
        
        # new chip distribution
        n_actions = 8
        
        # initiate 3 layer NN
        self.nn = [
            nn.Linear(n_states, 128),
            nn.Linear(128, 128),
            nn.Linear(128, n_actions)
        ]
        
        # reward look up table
        self.r_table = {}
        self.compute_r_table()
    
    def compute_r_table(self):
        ''' computes rewards the agent would get over all possible chip distributions and goals on possible boards '''
        # iterate over goals
        for pos in self.board.valid_goals:
            goal = self.board.grid[pos[0]][pos[1]]
            start_distance = manhattan_distance(self.board.start, goal)
            
            # iterate over chips distributions
            for n_chips in range(1, len(self.all_chips)+1):
                chips_owned = self.all_chips[:n_chips]
                
                shortest_distance, unused_chips = find_best_path(goal, chips_owned, self.board)
                
                win_score = 500 if shortest_distance == 0 else 0
                steps = start_distance - shortest_distance
                
                reward = steps * 100 + unused_chips * 50 + win_score
                
                self.r_table[goal][chips_owned] = reward
    
    def forward_pass(self, x):
        x = nn.functional.relu(self.nn[0](x))
        x = nn.functional.relu(self.nn[1](x))
        return self.nn[3](x)