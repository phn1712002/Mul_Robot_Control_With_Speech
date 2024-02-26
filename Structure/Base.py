from Device.Components import MechanicalComponents
from Device.Motor import Motor
from Device.Gear import SpurGear

# Class
class Base_V1(MechanicalComponents):
    def __init__(self, 
                 motor: Motor, 
                 z=[1, 2], 
                 angle_limit=[-60, 60],
                 delay_motor=0.0001,
                 name=None):
        super().__init__(name=name)
        self.motor = motor
        self.gear = SpurGear(z=z)
        self.angle_limit = angle_limit
        self.delay_motor = delay_motor
        self.sign_steps_break = None
        
    def step(self, angle):
        def checkStop_fn(self, angle, sign_steps):
            """ Function callbacks using in steps with task checkStop (stop motor when got stuck)
                Like fucntion checkStop_fn in Link.py
                Just different checkStop with angle, no switch limit
    
            Args:
                self (Link_V1): Self Structure
                sign_steps (int, [-1, 1]): Dir of motor
                angle (float) : angle current of Structure

            Returns:
                bool: True - Break, False - No Break
            """
            # Check angle
            check = angle < self.angle_limit[0] or angle > self.angle_limit[1] # Diffenrent Link.py
            
            if check:
                if self.sign_steps_break == None: return True
                if self.sign_steps_break == sign_steps: return True
                else:
                    self.sign_steps_break = None
                    return False
        
        # Control motor step
        return self.motor.step(angle=self.gear.calcParameter(input=angle, inverse=True), delay=self.delay_motor, checkStop=lambda angle, sign_steps, exit: checkStop_fn(self, angle, sign_steps))        
        
    def getAngle(self):
        return self.motor.history_step_angle