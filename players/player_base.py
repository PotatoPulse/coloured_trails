

class Player():
    def __init__(self):
        self.chips = []     # player chips on public display
        self.all_chips = []
        self.board = None
        self.goal = None
        self.type = "base"
        self.role = ""
        pass

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