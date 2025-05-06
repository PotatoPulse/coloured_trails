from utils.globals import VALID_GOALS
from board import Board
from players.player_random import RandomPlayer
from players.player_DQN import DQNPlayer
from players.player_accept import AcceptPlayer
from players.player_FOToM import FOToMPlayer
from game_master import GameMaster
import pandas as pd
import matplotlib.pyplot as plt
import copy
import time

def main():
    start_time = time.time()
    
    board = Board.load("test_board", copy.copy(VALID_GOALS))
    
    DQN_player1 = DQNPlayer(epsilon_start = 0.9, 
                 epsilon_end = 0.05,
                 epsilon_decay = 1000,
                 gamma = 0.99,
                 lr = 1e-4,
                 board = board,
                 batch_size = 32,
                 name = "John")
    
    DQN_player2 = DQNPlayer(epsilon_start = 0.9, 
                 epsilon_end = 0.1, # 0.05
                 epsilon_decay = 1000,
                 gamma = 0.99,
                 lr = 1e-4,
                 board = board,
                 batch_size = 32,
                 name = "Sarah")
    
    random_player = RandomPlayer()
    
    # initialising DQN Q-values by playing games against player who always accepts
    '''
    training_dummy = AcceptPlayer()
    game = GameMaster(initiator=training_dummy, responder=ToM_player, board=board)
    game.play(max_games=1000)
    '''

    # initialising DQN Q-values by playing games against player who always accepts
    '''
    training_dummy = AcceptPlayer()
    game = GameMaster(initiator=training_dummy, responder=DQN_player2, board=board)
    game.play(max_games=500)
    '''
    
    initiator = DQNPlayer.load(name="equilibrium", board=board)
    puppet = copy.deepcopy(initiator)

    ToM_player = FOToMPlayer(epsilon_start = 0.1, 
                epsilon_end = 0.05,
                epsilon_decay = 1000,
                gamma = 0.99,
                lr = 1e-4,
                goal_lr = 0.1, # 0.5, 0.9
                prediction_epsilon = 0.05,
                board = board,
                batch_size = 32,
                name = "Daniel",
                DQN_agent = puppet)
    
    responder = ToM_player
    game = GameMaster(initiator=initiator, responder=responder, board=board)
    game.play(max_games=1000)
    
    # initiator.save(name="stationary_board_DQN")
    
    end_time = time.time()
    print("Total runtime: ", round(end_time - start_time, 2))
    
    # plot results
    df = pd.read_csv(f"logs/log-{initiator.type}-{responder.type}.csv")
    
    plt.figure(figsize=(10, 6))
    plt.plot(df['total_score_initiator'], label='Initiator', linewidth=2)
    plt.plot(df['total_score_responder'], label='Responder', linewidth=2)
    
    plt.xlabel('Game #')
    plt.ylabel('Total Score')
    plt.title('Score Progression Over Games')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    plt.show()
    
    plt.figure(figsize=(10, 6))
    plt.plot(df['offers_accepted'], label='# accepted offers', linewidth=2)
    
    plt.xlabel('Game #')
    plt.ylabel('Total Score')
    plt.title('acceptance Progression Over Games')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    plt.show()

if __name__ == "__main__":
    main()