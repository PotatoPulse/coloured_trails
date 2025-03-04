from utils.globals import BOARD_SIZE, COLOURS
import random

class Board():
    def __init__(self):
        self.parent_board = self.generate_parent_board()    # board on which all boards will be based
        self.grid = None

    def generate_parent_board(self):
        board = []
        for height in range(BOARD_SIZE):
            row = []
            for width in range(BOARD_SIZE):
                row.append(random.choice(COLOURS))
            board.append(row)
        
        return board
    
    def new_board(self):
        board = self.parent_board
        board[round(BOARD_SIZE/2)][round(BOARD_SIZE/2)] = None # No colour needed where the players begin - in the middle
        
        self.grid = board
        
    def random_pos(self):
        valid_positions = [
            (r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) if self.grid[r][c] is not None
        ]
        
        return random.choice(valid_positions) if valid_positions else None