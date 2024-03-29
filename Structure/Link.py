from Device.Components import MechanicalComponents
from Device.Motor import Motor
from Device.Gear import SpurGear
from .SystemSensor import SystemSensor

# Class
class Link_V1(MechanicalComponents):
    def __init__(self, 
                 motor:Motor, 
                 system_sensor: SystemSensor,
                 z=[1, 2],
                 delay_motor=0.0001,
                 right = True,
                 name=None,
                 ):
        super().__init__(name=name)
        self.motor = motor 
        self.system_sensor = system_sensor
        self.gear = SpurGear(z=z)
        self.delay_motor = delay_motor
        self.right = right
        
    def step(self, angle=0, skip_check_sensor=False):
        if not skip_check_sensor:
            # Control motor step
            return self.motor.step(angle=self.gear.calcParameter(input=angle, inverse=True), 
                                delay=self.delay_motor, 
                                checkStop=lambda angle=0, sign_steps=-1, exit=False: self.system_sensor.checkStop(check_right=self.right, sign_steps=sign_steps, exit=exit)
                                )
        else:
            return self.motor.step(angle=self.gear.calcParameter(input=angle, inverse=True), 
                                delay=self.delay_motor)
        
    def getAngle(self):
        return self.motor.history_step_angle
        
    