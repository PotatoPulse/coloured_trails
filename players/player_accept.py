from players.player_base import Player
import random

# player that gives out random offers, but always accepts incoming offers

class AcceptPlayer(Player):
    def __init__(self, name = "AcceptPlayer", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name
        self.type = "accept"
    
    def offer_out(self) -> tuple[tuple, tuple] | None:
        '''Player sends out an offer'''
        return random.choice(self.all_offers)

    def offer_in(self, offer: tuple) -> bool:
        '''Player evaluates offer and accepts or declines'''
        return True
    
    def evaluate(self, score) -> tuple:
        pass