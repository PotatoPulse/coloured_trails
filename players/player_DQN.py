from utils.globals import BOARD_SIZE, CHIPS
from board import Board
from players.player_base import Player
from pathfinder import find_best_path, manhattan_distance
from collections import Counter, deque, defaultdict
from itertools import combinations
import torch
import torch.nn as nn
import random
import numpy as np

class DQN(nn.Module):
    def __init__(self, n_states, n_actions):
        super(DQN, self).__init__()
        self.layer1 = nn.Linear(n_states, 128)
        self.layer2 = nn.Linear(128, 128)
        self.layer3 = nn.Linear(128, n_actions)
    
    def forward(self, x):
        x = nn.functional.relu(self.layer1(x))
        x = nn.functional.relu(self.layer2(x))
        return self.layer3(x)


class DQNPlayer(Player):
    def __init__(self, epsilon_start: float, 
                 epsilon_end: float,
                 epsilon_decay: float,
                 gamma: float,
                 lr: float,
                 board: Board,
                 batch_size: int = 32,
                 name: str = "DQN_player",
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = "DQN"
        self.epsilon_start = epsilon_start  # epsilon at start of training
        self.epsilon_end = epsilon_end      # epsilon at end of training, lowered by epsilon decay
        self.epsilon_decay = epsilon_decay  # decay rate of epsilon during training
        self.gamma = gamma                  # discount factor
        self.lr = lr                        # learning rate
        self.batch_size = batch_size
        self.steps = 0                      # actions completed
        self.start_reward = 0
        self.prev_offer = None              # offer previously raised by opponent
        self.board = board
        self.name = name
        
        # number of states = possible board configurations + possible goal states 
        # + current chip distribution + chip distribution resulting from last offer
        n_states = 120 + 12 + 8 + 8 
        
        # actions = all possible offers
        n_actions = len(self.all_offers)
        
        # initiate policy and target net
        self.policy_net = DQN(n_states, n_actions)
        self.target_net = DQN(n_states, n_actions)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        
        self.optimiser = torch.optim.AdamW(self.policy_net.parameters(), lr=self.lr, amsgrad=True)
        
        self.memory = deque(maxlen=10000)
        self.transition = [None] * 4
        
        # reward look up table
        self.r_table = defaultdict(lambda: defaultdict(dict))
    
    def get_state(self):
        goal_state = torch.zeros(12, dtype=torch.float32)       # 12 possible goals
        chip_state = torch.zeros(8, dtype=torch.float32)        # 8 chips
        prev_offer_state = torch.zeros(8, dtype=torch.float32)  # 8 chips in offer distribution
        board_state = torch.zeros(120, dtype=torch.float32)    # 5! = 120 possible boards
        
        goal_state[self.goal_idx] = 1
        
        chip_counts = Counter(self.chips)
        for idx, chip in enumerate(CHIPS):
            if chip_counts[chip] > 0:
                chip_state[idx] = 1
                chip_counts[chip] -= 1
        
        if self.prev_offer == None:
            prev_offer_state = chip_state.clone()   # act as if initial state was offered by opponent
        else:
            offer_counts = Counter(self.prev_offer[1])      # second index is chips assigned to us
            for idx, chip in enumerate(CHIPS):
                if offer_counts[chip] > 0:
                    prev_offer_state[idx] = 1
                    offer_counts[chip] -= 1
                    
        board_idx = list(self.r_table.keys()).index(self.board.code)
        board_state[board_idx] = 1
        
        state = torch.cat((goal_state, chip_state, prev_offer_state, board_state), dim=0)
        
        return state.view(1, -1)
    
    def take_action(self, state):
        epsilon = self.epsilon_end + (self.epsilon_start - self.epsilon_end) * \
            np.exp(-1 * self.steps / self.epsilon_decay)
        self.steps += 1
        
        if self.steps % 100 == 0:
            self.target_net.load_state_dict(self.policy_net.state_dict())
        
        if random.random() > epsilon:
            with torch.no_grad():
                raw_action = self.policy_net(state)
                action_index = raw_action.argmax().item()
                action = self.all_offers[action_index]
        else:
            action = random.choice(self.all_offers)
        
        return action
    
    def offer_out(self):
        if self.transition[0] == None:
            self.compute_r_table()
            self.start_reward = self.r_table[self.board.code][self.goal][tuple(sorted(self.chips))]
        
        state = self.get_state()
        
        action = self.take_action(state)
        
        self.transition[0] = state 
        self.transition[1] = torch.tensor([[self.all_offers.index(action)]])  # store action as index within all_offers list
        
        offer_me = action[0]
        offer_opp = action[1]
        
        return (tuple(offer_me), tuple(offer_opp))
    
    def offer_in(self, offer):
        if self.transition[0] == None:
            self.compute_r_table()
            self.start_reward = self.r_table[self.board.code][self.goal][tuple(sorted(self.chips))]
        
        self.prev_offer = offer
        
        state = self.get_state()
        
        if self.transition[0] != None and self.transition[2] != None:
            # update next_state in transition and store to memory
            self.transition[3] = state
            self.store_transition()
        
        action = self.take_action(state)
        
        action_me = action[0]
        
        if sorted(action_me) == sorted(offer[1]):
            return True     # accept offer
        else:
            return False    # decline offer

    def offer_evaluate(self, offer, accepted):
        if accepted:
            # initial reward - new reward
            self.transition[2] = self.r_table[self.board.code][self.goal][tuple(sorted(offer[0]))] - self.start_reward # store reward
            self.store_transition()
        else:
            self.transition[2] = 0 # reward
            # reward = self.r_table[self.board.code][self.goal][tuple(sorted(self.chips))] # 0 reward

            # wait for next state to be found out next round
    
    def compute_r_table(self):
        ''' computes rewards the agent would get over all possible chip distributions and goals on possible boards '''
        if self.board.code in self.r_table.keys():
            return
        
        print(f"Computing reward table for {self.name}...")
        
        # iterate over goals
        for goal in self.board.valid_goals:
            start_distance = manhattan_distance(self.board.start, goal)
            
            self.r_table[self.board.code][goal][()] = 0
            
            # iterate over chips distributions
            for n_chips in range(1, len(self.all_chips)+1):
                for chips_subset in combinations(self.all_chips, n_chips):
                    chips_owned = list(chips_subset)
                    shortest_distance, unused_chips = find_best_path(chips_owned, goal, self.board)
                    
                    win_score = 500 if shortest_distance == 0 else 0
                    steps = start_distance - shortest_distance
                    
                    # calculate reward the agent would get in this situation
                    reward = steps * 100 + unused_chips * 50 + win_score
                    
                    # add score to table
                    self.r_table[self.board.code][goal][tuple(sorted(chips_owned))] = reward
    
    def store_transition(self):
        if None in self.transition[:3]:
            print("NONE FOUND IN TRANSITION", self.transition)
            return
        self.memory.append(self.transition)
        self.optimise_model()
        self.transition = [None] * 4
    
    def sample_memory(self):
        return random.sample(self.memory, self.batch_size)
    
    def optimise_model(self):
        # make sure there's enough memory
        if len(self.memory) < self.batch_size:
            return
        
        transitions = self.sample_memory()
        batch = list(zip(*transitions))
        
        state_batch = torch.cat(batch[0])
        action_batch = torch.cat(batch[1])
        reward_batch = torch.tensor(batch[2], dtype=torch.float32)
        next_state_batch = batch[3]
        
        non_final_mask = torch.tensor(tuple(map(lambda s: s is not None, next_state_batch)), dtype=torch.bool)
        if any(s is not None for s in next_state_batch):
            non_final_next_states = torch.cat([s for s in next_state_batch if s is not None])
        else:
            non_final_next_states = torch.empty((0,) + state_batch.shape[1:])
        
        state_action_values = self.policy_net(state_batch).gather(1, action_batch.to(dtype=torch.int64))
        
        next_state_values = torch.zeros(self.batch_size)
        with torch.no_grad():
            if non_final_mask.any():
                next_state_values[non_final_mask] = self.target_net(non_final_next_states).max(1)[0]
        
        # bellman equation
        expected_state_action_values = (next_state_values * self.gamma) + reward_batch
        
        criterion = nn.SmoothL1Loss()
        loss = criterion(state_action_values, expected_state_action_values.unsqueeze(1))
        
        self.optimiser.zero_grad()
        loss.backward()
        
        torch.nn.utils.clip_grad_value_(self.policy_net.parameters(), 100)
        self.optimiser.step()