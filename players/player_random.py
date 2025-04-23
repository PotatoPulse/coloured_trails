from players.player_base import Player
import random

class RandomPlayer(Player):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = "random"
    
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