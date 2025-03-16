from board import Board
from players.player_random import RandomPlayer
from game_master import GameMaster

def main():
    valid_goals = [
        (0, 0), (0, 1), (0, 3), (0, 4),
        (1, 0), (1, 4),
        (3, 0), (3, 4),
        (4, 0), (4, 1), (4, 3), (4, 4),
    ]
    
    board = Board(valid_goals)
    player1 = RandomPlayer()
    player2 = RandomPlayer()
    
    game = GameMaster(initiator=player1, responder=player2, board=board)
    game.play()

if __name__ == "__main__":
    main()