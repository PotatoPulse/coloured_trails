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
import numpy as np

def main():
    start_time = time.time()
    
    #new board
    # board = Board(valid_goals=copy.copy(VALID_GOALS))
    # board.save(name="30000_board_6")
    
    #load board
    board = Board.load("30000_board_6", copy.copy(VALID_GOALS))
    
    DQN_player1 = DQNPlayer(epsilon_start = 0.9, 
                 epsilon_end = 0.1,
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
    
    '''
    # initialising DQN Q-values by playing games against player who always accepts
    training_dummy = AcceptPlayer()
    game = GameMaster(initiator=training_dummy, responder=DQN_player1, board=board)
    game.play(max_games=500)

    # initialising DQN Q-values by playing games against player who always accepts
    training_dummy = AcceptPlayer()
    game = GameMaster(initiator=DQN_player2, responder=training_dummy, board=board)
    game.play(max_games=500)
    DQN_player2.steps = 0
    DQN_player2.save(name="Sarah")
    
    initiator = DQN_player1
    responder = DQN_player2
    game = GameMaster(initiator=initiator, responder=responder, board=board)
    game.play(max_games=30000)
    
    responder.save(name="DQN_30000_6")
    '''
    
    # simulate multiple games
    n_games = 20
    log_category = "6-1_lookahead-"
    
    for i in range(1, n_games+1):
        initiator = DQNPlayer.load(name="DQN_30000_6", board=board)
        puppet = DQNPlayer.load(name="DQN_30000_6", board=board)
        
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
        game = GameMaster(initiator=initiator, responder=responder, board=board, log_name=log_category+str(i))
        game.play(max_games=250)

    # initiator.save(name="stationary_board_DQN")
    
    end_time = time.time()
    print("Total runtime: ", round(end_time - start_time, 2))
    
    # plot aggregated results
    all_scores_initiator = []
    all_scores_responder = []
    all_goal_guess = []
    
    for i in range(1, n_games + 1):
        df = pd.read_csv(f'logs/log-{log_category}{i}.csv')
        
        all_scores_initiator.append(df['total_score_initiator'].values)
        all_scores_responder.append(df['total_score_responder'].values)
        all_goal_guess.append(df['goal_guess'].values)
        
    min_len = min(len(arr) for arr in all_scores_initiator)

    scores_initiator = np.array([arr[:min_len] for arr in all_scores_initiator])
    scores_responder = np.array([arr[:min_len] for arr in all_scores_responder])
    goal_guess = np.array([arr[:min_len] for arr in all_goal_guess])
    
    mean_initiator = scores_initiator.mean(axis=0)
    mean_responder = scores_responder.mean(axis=0)
    mean_goal = goal_guess.mean(axis=0)
    
    std_initiator = scores_initiator.std(axis=0)
    std_responder = scores_responder.std(axis=0)
    std_goal = goal_guess.std(axis=0)
    
    plt.figure(figsize=(10, 6))
    plt.plot(mean_initiator, label='Initiator [DQN] (avg cumulative score)', linewidth=2)
    plt.fill_between(range(len(mean_initiator)), mean_initiator - std_initiator, mean_initiator + std_initiator, alpha=0.2)
    plt.plot(mean_responder, label='Responder [ToM] (avg cumulative score)', linewidth=2)
    plt.fill_between(range(len(mean_responder)), mean_responder - std_responder, mean_responder + std_responder, alpha=0.2)

    plt.xlabel('Game #')
    plt.ylabel('Total Score')
    plt.title(f'Average Score Progression Over {n_games} Runs')
    plt.legend(loc='upper left')
    plt.grid(True)
    plt.tight_layout()
    plt.show()
    
    plt.figure(figsize=(10, 6))
    plt.plot(mean_goal, label='Perceived probability of goal', linewidth=2)
    plt.fill_between(range(len(mean_goal)), mean_goal - std_goal, mean_goal + std_goal, alpha=0.2)

    plt.xlabel('Game #')
    plt.ylabel('Perceived probability of goal')
    plt.title(f'Perceived Probability of Goal Over {n_games} Runs')
    plt.legend(loc='upper left')
    plt.grid(True)
    plt.tight_layout()
    plt.show()
    
    '''
    # plot singular results
    df = pd.read_csv(f"logs/log-{initiator.type}-{responder.type}.csv")
    
    plt.figure(figsize=(10, 6))
    plt.plot(df['total_score_initiator'], label='Initiator', linewidth=2)
    plt.plot(df['total_score_responder'], label='Responder', linewidth=2)
    
    plt.xlabel('Game #')
    plt.ylabel('Total Score')
    plt.title('Score Progression Over Games')
    plt.legend(loc='upper left')
    plt.grid(True)
    plt.tight_layout()

    plt.show()
    
    plt.figure(figsize=(10, 6))
    plt.plot(df['goal_guess'], label='Perceived probability of goal', linewidth=2)
    
    plt.xlabel('Game #')
    plt.ylabel('Total Score')
    plt.title('Perceived Probability of Goal Over Games')
    plt.legend(loc='upper left')
    plt.grid(True)
    plt.tight_layout()

    plt.show()
    '''

if __name__ == "__main__":
    main()