from .Components import MechanicalComponents

# Interfaces
class Gear(MechanicalComponents):
    def __init__(self, name=None):
        super().__init__(name)
        self.z = None
        self.i = None
        self.i_inverse = None
    def calcParameter(self, input, inverse): pass
    def calcGear(self, z, inverse): pass

# Class
class MultiGear(Gear):
    
    def __init__(self, multi_gear=None, name=None, ):
        super().__init__(name)
        self.multi_gear = multi_gear
    
    def calcParameter(self, input, inverse):
        for index_gear in self.multi_gear:
            input *= index_gear.calcParameter(input, inverse)
        return input    
        
class SpurGear(Gear):
    def __init__(self,
                 z=[1, 2], 
                 name=None):
        super().__init__(name=name)
        self.z = z
        self.i = self.calcGear(z, True)
        self.i_inverse = self.calcGear(z, False)
        
    def calcParameter(self, input: int, inverse=False):
        """ 
            Function calc number any using Transmission ratio with task calc
        Args:
            input (int): Number any using calc with Transmission ratio
            inverse (bool, optional): True - Calc with 1/(transmission ratio) , False - Calc with transmission ratio

        Returns:
            float: Number after calc
        """
        if inverse:
            return input * self.i_inverse, self.i
        else:
            return input * self.i, self.i
        
    def calcGear(self, z, inverse=False):
        """ Calc transmission ratio in system
        Args:
            z (list): List number of teeth, list diameter
            inverse (bool, optional): True - Calc with 1/(transmission ratio) , False - Calc with transmission ratio

        Returns:
            float: Transmission ratio after calc
        """
        i = 1
        for index in range(len(z) - 1):
            i *= z[index + 1] / z[index]
        if inverse : i = 1/i
        return i