from players.player_base import Player
from itertools import combinations
import random

class RandomPlayer(Player):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.all_offers = []
        self.type = "random"
        
    def get_all_offers(self):
        self.all_offers = []
        opp_chips = [chip for chip in self.all_chips if chip not in self.chips]
        
        self.all_offers.append(((), ()))
        
        for send_size in range(0, len(self.chips) + 1):
            for receive_size in range(0, len(opp_chips)):
                for send in combinations(self.chips, send_size):
                    for receive in combinations(opp_chips, receive_size):
                        if set(send) != set(receive): # sending and receiving the same chips is not useful
                            self.all_offers.append((tuple(send), tuple(receive)))
    
    def offer_out(self) -> tuple[tuple, tuple] | None:
        '''Player sends out an offer'''
        self.get_all_offers()
        return random.choice(self.all_offers)

    def offer_in(self, offer: tuple) -> bool:
        '''Player evaluates offer and accepts or declines'''
        my_side = offer[1]
        if not set(my_side).issubset(set(self.chips)):
            return False

        return random.choice([True, False])
    
    def evaluate(self, score) -> tuple:
        pass