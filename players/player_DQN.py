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

# DQN agent, taking into account 1 possible board

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
        self.prev_offer = None              # offer previously raised by opponent
        self.board = board
        self.name = name
        
        # number of states = possible board configurations + possible goal states 
        # + current chip distribution + chip distribution resulting from last offer
        n_states = 1 + 12 + 8 + 8 
        
        # new chip distribution
        n_actions = 8
        
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
        board_state = torch.tensor([1], dtype=torch.float32)    # only 1 board for now
        goal_state = torch.zeros(12, dtype=torch.float32)       # 12 possible goals
        chip_state = torch.zeros(8, dtype=torch.float32)        # 8 chips
        prev_offer_state = torch.zeros(8, dtype=torch.float32)  # 8 chips in offer distribution
        
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
                    chip_state[idx] = 1
                    offer_counts[chip] -= 1
        
        state = torch.cat((board_state, goal_state, chip_state, prev_offer_state), dim=0)
        
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
                binary_action = (raw_action > 0.5).int()
        else:
            binary_action = torch.randint(0, 2, (1, 8), dtype=torch.int)
        
        return binary_action
    
    def offer_out(self):
        state = self.get_state()
        
        if self.transition[0] != None:
            #update next_state in transition and store to memory
            self.transition[3] = state
            self.store_transition()
        
        binary_action = self.take_action(state)
        
        self.transition[0] = state 
        self.transition[1] = binary_action
        
        offer_me = []
        offer_opp = []
        
        binary_action = binary_action.flatten().tolist()
        for idx, chip in enumerate(CHIPS):
            if binary_action[idx]:
                offer_me.append(chip)
            else:
                offer_opp.append(chip)
        
        return (tuple(offer_me), tuple(offer_opp))
    
    def offer_in(self, offer):
        self.prev_offer = offer
        
        state = self.get_state()
        
        binary_action = self.take_action(state)
        binary_action = binary_action.flatten().tolist()
        
        action_me = [CHIPS[idx] for idx, bool in enumerate(binary_action) if bool]
                
        if sorted(action_me) == sorted(offer[1]):
            return True     # accept offer
        else:
            return False    # decline offer
            
    def offer_evaluate(self, offer, accepted):
        if accepted:
            reward = self.r_table[self.board.code][self.goal][tuple(sorted(offer[0]))]
            next_state = None #How do we know the next board we'll end up in?? or: should new board be considered?
        else:
            reward = self.r_table[self.board.code][self.goal][tuple(sorted(self.chips))]
            next_state = self.transition[0]
            
        self.transition[2] = reward     # possibly extra penalty/reward depending on accepted
        self.transition[3] = next_state
    
    def compute_r_table(self):
        ''' computes rewards the agent would get over all possible chip distributions and goals on possible boards '''
        print(f"Computing reward table for {self.name}...")
        # iterate over goals
        for goal in self.board.valid_goals:
            start_distance = manhattan_distance(self.board.start, goal)
            
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
        non_final_next_states = torch.cat([s for s in next_state_batch if s is not None])
        
        state_action_values = self.policy_net(state_batch).gather(1, action_batch.to(dtype=torch.int64))
        
        next_state_values = torch.zeros(self.batch_size)
        with torch.no_grad():
            next_state_values[non_final_mask] = self.target_net(non_final_next_states).max(1)[0]
        
        expected_state_action_values = (next_state_values * self.gamma) + reward_batch
        
        criterion = nn.SmoothL1Loss()
        loss = criterion(state_action_values, expected_state_action_values.unsqueeze(1))
        
        self.optimiser.zero_grad()
        loss.backward()
        
        torch.nn.utils.clip_grad_value_(self.policy_net.parameters(), 100)
        self.optimiser.step()