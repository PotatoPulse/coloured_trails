from utils.globals import CHIPS
from players.player_base import Player
from itertools import combinations, chain
from collections import Counter
import random

class RandomPlayer(Player):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = "random"
        self.all_offers = []
        
        self.get_all_offers()
        
    def get_all_offers(self):
        self.all_offers = []
        
        all_chip_sets = list(chain.from_iterable(combinations(CHIPS, r) for r in range(len(CHIPS) + 1)))
        
        for my_new_chips in all_chip_sets:
            opp_new_chips = (Counter(CHIPS) - Counter(my_new_chips)).elements()
            
            self.all_offers.append((tuple(sorted(my_new_chips)), tuple(sorted(opp_new_chips))))
    
    def offer_out(self) -> tuple[tuple, tuple] | None:
        '''Player sends out an offer'''
        return random.choice(self.all_offers)

    def offer_in(self, offer: tuple) -> bool:
        '''Player evaluates offer and accepts or declines'''
        my_side = offer[1]
        if not set(my_side).issubset(set(self.chips)):
            return False

        return random.choice([True, False])
    
    def evaluate(self, score) -> tuple:
        pass