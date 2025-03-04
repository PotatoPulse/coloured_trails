from board import Board
from players.player_random import RandomPlayer
from game_master import GameMaster

def main():
    board = Board()
    player1 = RandomPlayer()
    player2 = RandomPlayer()
    
    game = GameMaster(initiator=player1, responder=player2, board=board)
    game.play()

if __name__ == "__main__":
    main()