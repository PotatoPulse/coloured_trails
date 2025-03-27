from board import Board
from players.player_random import RandomPlayer
from players.player_DQN import DQNPlayer
from game_master import GameMaster

def main():
    valid_goals = [
        (0, 0), (0, 1), (0, 3), (0, 4),
        (1, 0), (1, 4),
        (3, 0), (3, 4),
        (4, 0), (4, 1), (4, 3), (4, 4),
    ]
    
    board = Board(valid_goals)
    player1 = DQNPlayer(epsilon_start = 0.5, 
                 epsilon_end = 0.05,
                 epsilon_decay = 1000,
                 gamma = 0.99,
                 lr = 1e-4,
                 board = board,
                 batch_size = 32,
                 name = "John")
    player2 = RandomPlayer()
    
    game = GameMaster(initiator=player1, responder=player2, board=board)
    game.play(max_games=1000)

if __name__ == "__main__":
    main()