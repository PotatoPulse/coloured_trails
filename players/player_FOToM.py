from utils.globals import CHIPS
from players.player_base import Player
from board import Board
from players.player_DQN import DQNPlayer
import torch
import numpy as np
import random
from collections import Counter
import os
import json

class FOToMPlayer(Player):
    def __init__(self,
                 epsilon_start: float, 
                 epsilon_end: float,
                 epsilon_decay: float,
                 gamma: float,
                 lr: float,
                 goal_lr: float,
                 board: Board,
                 batch_size: int = 32,
                 name: str = "FOToM_player",
                 DQN_agent: DQNPlayer = None,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = "FOToM"
        if DQN_agent:
            self.DQN = DQN_agent
            self.DQN.name = name + "_puppet"
        else:
            self.DQN = DQNPlayer(epsilon_start, epsilon_end, epsilon_decay, gamma, lr, board, batch_size, name+"_puppet")
        self.epsilon_start = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.goal_lr = goal_lr
        self.name = name
        self.board = board
        self.prev_offer = None
        self.own_prev_offer = None
        self.goal_guess = None
        self.goal_distribution = [1/12]*12
        self.start_reward = None
        
        self.transition = [None]*4
        
        self.steps = 0
        
    def encode_offer(self, offer_me):
        """Encodes offer as a count vector aligned with CHIPS (handles duplicates correctly)."""
        offer_counter = Counter(offer_me)
        result = []

        for chip in CHIPS:
            if offer_counter[chip] > 0:
                result.append(1.0)
                offer_counter[chip] -= 1
            else:
                result.append(0.0)

        return torch.tensor(result, dtype=torch.float32)
    
    def construct_opponent_state(self, state, goal, prev_offer=None):
        """Builds opponent's state given a guessed goal and optional previous offer 
        (where prev_offer only contains chips that would be assigned to opponent)."""
        state = state.view(-1)
        opponent_state = state.clone()

        # set up opponent goal state
        goal_vec = torch.zeros(12)
        goal_vec[self.board.valid_goals.index(goal)] = 1
        opponent_state[:12] = goal_vec

        # flip chip distribution
        distribution = state[12:20]
        opponent_state[12:20] = 1 - distribution

        # encode previous offer if provided
        if prev_offer is not None:
            opponent_state[20:28] = self.encode_offer(prev_offer)

        return opponent_state
    
    def predict_action(self, state):
        with torch.no_grad():
            q_values = self.DQN.policy_net(state.unsqueeze(0))
            best_idx = q_values.argmax().item()
            best_action = self.all_offers[best_idx]
            best_value = q_values[0, best_idx].item()
        return best_action, best_value
    
    def offers_match(self, a, b):
        return sorted(tuple(a)) == sorted(tuple(b))
    
    def predict_best_action(self, state):
        state = state.view(-1)

        if self.goal_guess is None:
            self.goal_guess = self.goal

        max_return = 0
        best_action = None
        best_predicted_response = None
        best_next_action = None
        
        for offer in self.all_offers:
            if self.offers_match(offer[0], self.chips):
                best_action = offer
        # best_action = [offer in self.all_offers if offer[0] == self.chips]

        for offer in self.all_offers:
            # simulate opponent response
            opponent_state = self.construct_opponent_state(state, self.goal_guess, offer[1])
            predicted_response, _ = self.predict_action(opponent_state)

            # opponent stops negotiations
            if self.offers_match(predicted_response[1], tuple(self.chips)):
                value = 0
            # opponent accepts
            elif self.offers_match(predicted_response[1], offer[0]):
                value = self.DQN.r_table[self.board.code][self.goal][tuple(sorted(offer[0]))]
            else:
                # simulate next state if rejected
                next_state = state.clone()
                next_state[20:28] = self.encode_offer(predicted_response[1])
                
                next_action, value = self.predict_action(next_state)
                
            if not (isinstance(value, int) or isinstance(value, float)):
                print("value was not an int")
                exit()
                value = 0

            if value > max_return:
                max_return = value
                best_action = offer
                best_predicted_response = predicted_response
                best_next_action = next_action
                
        print(f"own action: {best_action} - opp action: {best_predicted_response} - next action: {best_next_action} - value: {max_return}")

        return best_action
        
    def guess_opp_goal(self, offer, state):
        # if no prev offer made, use the chip distribution
        if self.own_prev_offer == None:
            opp_chips = (Counter(CHIPS) - Counter(self.chips)).elements()
            self.own_prev_offer = [[], opp_chips] #if chip is not in self.chips, it should go in index 1
        
        state = state.view(-1)
        updates = np.zeros(12)

        for goal_idx, goal in enumerate(self.board.valid_goals):
            opponent_state = self.construct_opponent_state(state, goal, self.own_prev_offer[1])
            predicted_action, _ = self.predict_action(opponent_state)

            if self.offers_match(predicted_action[0], offer[1]):
                updates[goal_idx] = 1
            else:
                updates[goal_idx] = -1

        updates *= self.goal_lr

        new_distribution = self.goal_distribution + updates
        new_distribution = np.clip(new_distribution, 0.0001, None)
        new_distribution /= np.sum(new_distribution)

        self.goal_distribution = new_distribution
        self.goal_guess = self.board.valid_goals[np.argmax(self.goal_distribution)]
        
    def take_action(self, state):
        epsilon = self.epsilon_end + (self.epsilon_start - self.epsilon_end) * \
            np.exp(-1 * self.steps / self.epsilon_decay)
        self.steps += 1
        
        if random.random() > epsilon:
            # ToM prediction
            action = self.predict_best_action(state)
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
        
        offer = (sorted(tuple(offer_me)), sorted(tuple(offer_opp)))
        self.own_prev_offer = offer
        
        return offer
    
    def offer_in(self, offer):
        if self.transition[0] == None:
            self.new_game()
        
        self.DQN.prev_offer = offer
        
        state = self.DQN.get_state()
        
        # let's guess the goal according to offer in state
        self.guess_opp_goal(offer, state)
        
        if self.transition[0] != None:
            self.transition[3] = state
            self.DQN.transition = self.transition
            self.DQN.store_transition()
            self.transition = [None]*4
        
        action = self.take_action(state)
                
        if self.offers_match(action[0], offer[1]):
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
        
    def save(self, name):
        path = os.path.join(os.getcwd(), "saves", name)
        
        metadata = {
            "epsilon_start": self.epsilon_start,
            "epsilon_end": self.epsilon_end,
            "epsilon_decay": self.epsilon_decay,
            "gamma": self.DQN.gamma,
            "lr": self.DQN.lr,
            "goal_lr": self.goal_lr,
            "batch_size": self.DQN.batch_size,
            "goal_distribution": self.goal_distribution,
            "steps": self.steps,
            "name": self.name
        }
        
        with open(os.path.join(path, "config.json"), "w") as f:
            json.dump(metadata, f, indent=4)
            
        self.DQN.save(name + "_puppet")
    
    @classmethod
    def load(cls, name, board):
        path = os.path.join(os.getcwd(), "saves", f"FOToM-{name}")

        with open(os.path.join(path, "config.json"), "r") as f:
            config = json.load(f)

        puppet = DQNPlayer.load(name + "_puppet", board)

        agent = cls(
            epsilon_start=config["epsilon_start"],
            epsilon_end=config["epsilon_end"],
            epsilon_decay=config["epsilon_decay"],
            gamma=config["gamma"],
            lr=config["lr"],
            goal_lr=config["goal_lr"],
            board=board,
            batch_size=config["batch_size"],
            name=config["name"],
            DQN_agent=puppet
        )
        agent.steps = config["steps"]
        agent.goal_distribution = config["goal_distribution"]

        return agent