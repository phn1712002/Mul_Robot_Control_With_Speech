# Interfaces
class ElectronicComponents:
    def __init__(self, 
                 name=None,
                 board=None,
                 pin=0,
                 ):
        self.name = name
        self.board = board
        self.pin = pin

class MechanicalComponents:
    def __init__(self, name=None):
        self.name = name