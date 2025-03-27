from utils.globals import BOARD_SIZE, COLOURS
import random

class Board():
    def __init__(self, valid_goals):
        self.parent_board = self.generate_parent_board()    # board on which all boards will be based
        self.grid = None
        self.start = (int(BOARD_SIZE/2), int(BOARD_SIZE/2))
        self.valid_goals = valid_goals
        self.code = ""

    def generate_parent_board(self):
        board = []
        for height in range(BOARD_SIZE):
            row = []
            for width in range(BOARD_SIZE):
                row.append(random.choice(COLOURS))
            board.append(row)
        
        return board
    
    def new_board(self):
        board = [row.copy() for row in self.parent_board]
        random.shuffle(board)   # shuffle rows
        
        board[self.start[0]][self.start[1]] = None  # No colour needed where the players begin - in the middle
        
        self.grid = board
        self.update_code()
        
    def random_goal_pos(self):
        index, goal = random.choice(list(enumerate(self.valid_goals)))
        return goal, index
    
    def update_code(self):
        code = ""
        for row in self.grid:
            for colour in row:
                if not colour == None:
                    code += colour[0]
        
        self.code = code
        
    def __str__(self):
        string = ""
        
        for row in self.grid:
            row_str = "[" + ", ".join(col[0] if col is not None else "#" for col in row) + "]\n"
            string += row_str
        
        return string
