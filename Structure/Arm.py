from Device.Motor import Motor
from Device.Components import MechanicalComponents
from Device.Gear import SpurGear
# Class
class PickDropMechanism_V1(MechanicalComponents):
    def __init__(self, 
                 motor: Motor, 
                 z=[1, 2], 
                 angle_limit=[0 , 120],
                 delay_motor=0.5,
                 name=None):
        super().__init__(name=name)
        self.motor = motor
        self.delay_motor = delay_motor
        self.gear = SpurGear(z)
        self.angle_limit = [self.gear.calcParameter(angle_limit[0], True)[0], self.gear.calcParameter(angle_limit[1], True)[0]]
        
    def open(self):
        """
            Control motor steps to open arm using pick object
        """
        self.motor.step(self.angle_limit[0], self.delay_motor)

    def close(self):
        """
            Control motor steps to open arm using drop object
        """
        self.motor.step(self.angle_limit[1], self.delay_motor)
    
   
    