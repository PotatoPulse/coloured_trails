from utils.globals import CHIPS
from itertools import combinations, chain
from collections import Counter

class Player():
    def __init__(self):
        self.chips = []     # player chips on public display
        self.all_chips = CHIPS
        self.board = None
        self.goal = None
        self.goal_idx = None
        self.type = "base"
        self.role = ""
        self.all_offers = []
        self.get_all_offers()
        
    def get_all_offers(self):
        all_chip_sets = list(chain.from_iterable(combinations(CHIPS, r) for r in range(len(CHIPS) + 1)))
        
        for my_new_chips in all_chip_sets:
            opp_new_chips = (Counter(CHIPS) - Counter(my_new_chips)).elements()
            
            self.all_offers.append((tuple(sorted(my_new_chips)), tuple(sorted(opp_new_chips))))

    def offer_out(self):
        '''Player sends out an offer'''
        pass

    def offer_in(self):
        '''Player evaluates offer and accepts or declines'''
        pass
    
    def offer_evaluate(self, offer: tuple, accepted: bool):
        '''Player receives feedback on given offer'''
        pass
    
    def evaluate(self, score: int):
        '''Player receives feedback on game'''
        pass
    
    def end_game(self):
        pass