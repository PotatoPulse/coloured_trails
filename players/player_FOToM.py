from utils.globals import VALID_GOALS, CHIPS
from players.player_base import Player
from board import Board
from players.player_DQN import DQNPlayer
import torch
import numpy as np
import random

class FOToMPlayer(Player):
    def __init__(self,
                 epsilon_start: float, 
                 epsilon_end: float,
                 epsilon_decay: float,
                 gamma: float,
                 lr: float,
                 board: Board,
                 batch_size: int = 32,
                 name: str = "FOToM_player",
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type="FOToM"
        self.DQN = DQNPlayer(epsilon_start, epsilon_end, epsilon_decay, gamma, lr, board, batch_size, name+"_puppet")
        self.epsilon_start = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.name = name
        self.board = board
        self.prev_offer = None
        self.goal_guess = None
        self.start_reward = None
        
        self.transition = [None]*4
        
        self.steps = 0
        
    def predict_best_action(self, state):
        state = state.view(-1)
        
        if self.goal_guess == None:
            self.goal_guess = self.goal
        
        opponent_state = state.clone()
        
        # set up guessed goal for opponent
        new_goal_state = torch.zeros(12)
        new_goal_state[VALID_GOALS.index(self.goal_guess)] = 1
        opponent_state[:12] = new_goal_state
        
        # set up chip distribution for opponent
        distribution = state[12:20]
        flipped_distribution = 1 - distribution
        opponent_state[12:20] = flipped_distribution
        
        max_return = (-float('inf'))
        best_action = None
        for offer in self.all_offers:
            # simulate action using DQN net
            opponent_prev_offer = torch.tensor([chip in offer[1] for chip in CHIPS], dtype=torch.float32)
            opponent_state[20:28] = opponent_prev_offer
            
            raw_action = self.DQN.policy_net(opponent_state.unsqueeze(0))
            action_index = raw_action.argmax().item()
            action = self.all_offers[action_index]
            
            # accept or decline?
            if sorted(action[1]) == sorted(offer[0]):
                continue
            
            next_state = state.clone()
            next_prev_offer = torch.tensor([chip in action[1] for chip in CHIPS], dtype=torch.float32)
            next_state[20:28] = next_prev_offer
            
            raw_action = self.DQN.policy_net(next_state.unsqueeze(0))
            max_value, action_index = raw_action.max(dim=1)
            
            if max_value.item() > max_return:
                max_return = max_value.item()
                best_action = offer
                
        return best_action
        
    def take_action(self, state):
        epsilon = self.epsilon_end + (self.epsilon_start - self.epsilon_end) * \
            np.exp(-1 * self.steps / self.epsilon_decay)
        self.steps += 1
        
        if random.random() > epsilon:
            # ToM prediction
            action = self.predict_best_action(state)
            pass
        else:
            # Take a random (exploratory) action
            action = random.choice(self.all_offers)
        
        return action
    
    def offer_out(self):
        if self.transition[0] == None:
            self.new_game()
            
        state = self.DQN.get_state()
        action = self.take_action(state)
        
        self.transition[0] = state
        self.transition[1] = torch.tensor([[self.all_offers.index(action)]])
        
        offer_me = action[0]
        offer_opp = action[1]
        
        return (tuple(offer_me), tuple(offer_opp))
    
    def offer_in(self, offer):
        if self.transition[0] == None:
            self.new_game()
            
        self.DQN.prev_offer = offer
        
        state = self.DQN.get_state()
        
        if self.transition[0] != None:
            self.transition[3] = state
            self.DQN.transition = self.transition
            self.DQN.store_transition()
            self.transition = [None]*4
        
        action = self.take_action(state)
        
        action_me = action[0]
                
        if sorted(action_me) == sorted(offer[1]):
            return True     # accept offer
        else:
            return False    # decline offer
        
    def offer_evaluate(self, offer, accepted):
        if accepted:
            # initial reward - new reward
            self.transition[2] = self.DQN.r_table[self.board.code][self.goal][tuple(sorted(offer[0]))] - self.start_reward # store reward
            self.DQN.store_transition()
            self.transition = [None]*4
        else:
            self.transition[2] = 0 # reward
        
    def new_game(self):
        self.DQN.board = self.board
        self.DQN.chips = self.chips
        self.DQN.compute_r_table()
        self.start_reward = self.DQN.r_table[self.board.code][self.goal][tuple(sorted(self.chips))]