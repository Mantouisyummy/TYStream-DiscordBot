from enum import Enum

class WhenStreamEnds(int, Enum):
    EDIT = 1
    DELETE = 2
    NO_CHANGE = 3
