from utils.globals import BOARD_SIZE, COLOURS, COLOUR_TRANSLATION
import random
import os
import csv
import copy

class Board():
    def __init__(self, valid_goals):
        self.parent_board = None    # board on which all boards will be based
        self.grid = None
        self.start = (int(BOARD_SIZE/2), int(BOARD_SIZE/2))
        self.valid_goals = valid_goals
        self.code = ""
        self.parent_code = ""
        self.indices = list(range(BOARD_SIZE))
        
        self.generate_parent_board()

    def generate_parent_board(self):
        board = []
        code = ""
        
        for height in range(BOARD_SIZE):
            row = []
            for width in range(BOARD_SIZE):
                colour = random.choice(COLOURS)
                row.append(colour)
                code += colour[0]
            board.append(row)
        
        self.parent_board = board
        self.parent_code = code
    
    def generate_parent_from_code(self, parent_code):
        board = []
        row = []
        
        for idx, char in enumerate(parent_code):
            row.append(COLOUR_TRANSLATION[char])
            if (idx + 1) % BOARD_SIZE == 0:
                board.append(row)
                row = []
        
        self.parent_board = board
    
    def new_board(self):
        board = [row.copy() for row in self.parent_board]
        
        # random.shuffle(self.indices)
        
        board = [board[i] for i in self.indices]
        
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
    
    def save(self, name):
        path = os.path.join(os.getcwd(), "saves")
        save_path = os.path.join(path, name + ".csv")
        
        with open(save_path, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["parent_code"])
            writer.writerow([self.parent_code])
    
    @classmethod
    def load(cls, name, valid_goals):
        path = os.path.join(os.getcwd(), "saves")
        save_path = os.path.join(path, name + ".csv")

        with open(save_path, mode='r') as f:
            reader = csv.DictReader(f)
            data = next(reader)
            parent_code = data["parent_code"]

        board = cls(valid_goals)
        board.generate_parent_from_code(parent_code)
        board.new_board()

        return board