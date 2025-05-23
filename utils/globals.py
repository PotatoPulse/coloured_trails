BOARD_SIZE = 5
START_CHIPS = 4
COLOURS = ["black", "purple", "white", "grey",] # "yellow"]
COLOUR_TRANSLATION = {"b": "black", "p": "purple", "w": "white", "g": "grey", "y": "yellow"}

# fixed chips
# CHIPS = sorted(["black", "purple", "white", "grey", "yellow", "black", "purple", "white"])
CHIPS = sorted(["black", "purple", "white", "grey", "black", "purple", "white", "grey"])

VALID_GOALS = [
    (0, 0), (0, 1), (0, 3), (0, 4),
    (1, 0), (1, 4),
    (3, 0), (3, 4),
    (4, 0), (4, 1), (4, 3), (4, 4),
]