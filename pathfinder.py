from utils.globals import BOARD_SIZE
from board import Board

def manhattan_distance(pos1: tuple, pos2: tuple):
    ''' returns manhattan distance between 2 positions '''
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

def find_best_path(chips: list, goal: tuple, board: Board):
    ''' returns distance from goal using chips as efficiently as possible '''
    
    middle = (int(BOARD_SIZE/2), int(BOARD_SIZE/2))
    visited = set()
    chips = list(chips)
    
    shortest_distance = float('inf') # distance between end position and goal
    unused_chips = 0
    best_path = [] # for bug fixing
    
    def recurse(visited, chips, pos, prev_distance, path):
        nonlocal shortest_distance, unused_chips, best_path
        
        distance = manhattan_distance(pos, goal)
        
        # no obstacles, so distance increase is always suboptimal
        if distance > prev_distance:
            return
        
        if distance < shortest_distance:
            shortest_distance = distance
            unused_chips = len(chips)
            best_path = path
        elif distance == shortest_distance:
            unused_chips = max(unused_chips, len(chips))
            best_path = path
        
        visited.add(pos)
        
        next_pos = [(pos[0]-1, pos[1]), 
                    (pos[0]+1, pos[1]), 
                    (pos[0], pos[1]-1), 
                    (pos[0], pos[1]+1),]
        
        # make sure possible positions are on the board
        next_pos = [(x, y) for x, y in next_pos if x >= 0 and y >= 0 and x < BOARD_SIZE and y < BOARD_SIZE and not (x, y) in visited]
        
        for row, col in next_pos:
            colour = board.grid[row][col]
            
            if not colour in chips:
                continue
            
            new_chips = chips.copy()
            new_chips.remove(colour)
            new_path = path.copy()
            new_path.append(colour)
            
            recurse(visited.copy(), new_chips, pos=(row, col), prev_distance=distance, path=new_path)
    
    recurse(visited, chips, middle, float('inf'), best_path)

    return shortest_distance, unused_chips