from utils.globals import BOARD_SIZE, COLOURS
import numpy as np

class Board():
    def __init__(self):
        self.parent_board = self.generate_parent_board()    # board on which all boards will be based
        self.board = None

    def generate_parent_board(self):
        board = []
        for height in range(BOARD_SIZE):
            row = []
            for width in range(BOARD_SIZE):
                row.append(np.random.choice(COLOURS))
            board.append(row)
        
        return board
    
    def new_board(self):
        board = self.parent_board
        board[round(BOARD_SIZE/2)][round(BOARD_SIZE/2)] = None
        
        self.board = board