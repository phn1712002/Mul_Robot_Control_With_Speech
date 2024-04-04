import numpy as np
from pyfirmata import Arduino
from .Components import ElectronicComponents
from Tools.Delay import delayMicroseconds
from Tools.Math import funcTimeDelayStep



# Interfaces
class Motor(ElectronicComponents):
    def __init__(self, board: Arduino, name=None):
        super().__init__(board=board, name=name)
        self.history_step_angle = None
        
    def classify(self) -> str: pass
    
# Class
class Model_17HS3401(Motor):
    def __init__(self, 
                 board:Arduino,
                 step_pin:int, 
                 dir_pin:int,
                 div_step=1,
                 pos_dir=0,
                 step_skip=1,
                 slow_coef=0.8,
                 name=None):
        
        # Env
        super().__init__(board=board, name=name)
        self.HIGHT = 1
        self.LOW = 0
        
        self.dir_pin = board.get_pin(f'd:{dir_pin}:o')
        self.step_pin = board.get_pin(f'd:{step_pin}:o')
        self.div_step = div_step
        self.pos_dir = pos_dir
        self.step_skip = step_skip
        self.slow_coef = slow_coef
        
        # Save info step motor
        self.history_step_angle = 0
        self._step_angle_conts = 1.8
        self.step_angle = self._step_angle_conts / div_step        
        
    def step(self, angle, delay=0.0001, checkStop=None):
        
        # Convert angle, i
        if angle.__class__ is tuple:
            angle, i = angle
        elif angle.__class__ is int:
            i = 1

        # Calc steps of motor with angle and get dir 
        steps = angle / self.step_angle
        direction = None
        sign_steps = np.sign(steps)  
        steps = np.abs(int(steps))
        if sign_steps == True: direction = self.pos_dir
        else: direction = not self.pos_dir 
        
        # Create checkPoint show break in steps
        in_progress_break = False
        
        # Control direction
        self.dir_pin.write(direction)
        for idx in range(steps):
            delay_calc = delay + funcTimeDelayStep(steps, self.slow_coef * delay, idx)
            # Control Motor
            self.step_pin.write(self.HIGHT)
            delayMicroseconds(delay_calc)
            self.step_pin.write(self.LOW)
            delayMicroseconds(delay_calc)
            
            # Calc angle future
            temp_angle = self.history_step_angle + self.step_angle * i * sign_steps
            
            # Check stop
            if not checkStop is None and idx % self.step_skip == 0:
                if checkStop(angle=temp_angle, sign_steps=sign_steps) == True: in_progress_break = True
                
            
            # Break out
            if not in_progress_break: self.history_step_angle = temp_angle
            else: break
            
        # Exit checkStop and create reset checkStop
        if not checkStop is None:
            checkStop(exit=True)
        delayMicroseconds(delay)
        
        return self.history_step_angle, in_progress_break
                          
class Model_MG90S(Motor):
    def __init__(self, board:Arduino, pin:int, name=None):
        super().__init__(board=board, name=name)
        self.servo = board.get_pin(f'd:{pin}:s')
        self.angle_current = 0
        
    def step(self, angle, delay=15):
        sign_steps = np.sign(angle - self.angle_current)
        for idx in range(int(self.angle_current), int(angle), int(sign_steps)):
            self.servo.write(idx)
            delayMicroseconds(delay)
        self.angle_current = angle
        return self.angle_current
             

