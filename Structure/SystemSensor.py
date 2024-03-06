from pyfirmata import Arduino
from Device.Switch import Switch, Model_2A_Analog
from Device.Components import ElectronicComponents
from Tools.Delay import delayMicroseconds

class SystemSensor(ElectronicComponents):
    def __init__(self, name=None, board=None, pin=0):
        super().__init__(name, board, pin)
        
    def checkStop(self, check_right: bool, sign_steps: int, exit=False):
        """
        Function callbacks using in steps with task checkStop (stop motor when got stuck)
        Args:
            check_right: True - Check motor right, False - Check motor left
            sign_steps (int, [-1, 1]): Dir of motor
            exit: Not used

        Returns:
            bool: True - Break, False - No Break
        """
        return False
    
class MultiSwitch_V1(SystemSensor):
    def __init__(self, board: Arduino, 
                 config_switch_right: Switch, 
                 config_switch_left: Switch, 
                 config_switch_2mid: Switch, 
                 time_delay_break_out = 0.1,
                 name=None):
        super().__init__(name, board, None)
        
        
        self.board = board
        self.config_switch_right = config_switch_right
        self.config_switch_left = config_switch_left
        self.config_switch_2mid = config_switch_2mid
         
        self.switch_right = Model_2A_Analog(board=board, **self.config_switch_right)
        self.switch_left = Model_2A_Analog(board=board, **self.config_switch_left)
        self.switch_mid = Model_2A_Analog(board=board, **self.config_switch_2mid)

        
        self.check_r = self.switch_right.checkClick
        self.check_l = self.switch_left.checkClick
        self.check_m = self.switch_mid.checkClick
        
        self.limit_left = [-1, None]
        self.limit_right = [-1, None]
        self.limit = [self.limit_left ,self.limit_right]
        
        self.wait_break_out = False
        self.history_check = None
        
        
        self.time_delay_break_out = time_delay_break_out
    
    def checkStop(self, check_right=True, sign_steps=1, exit=False):
            """
            Function to check if the motor should stop when it gets stuck.

            Args:
                check_right (bool): True - Check motor right, False - Check motor left
                sign_steps (int, [-1, 1]): Dir of motor
                exit (bool): True - Exit the function, False - Continue the function

            Returns:
                bool: True - Break, False - No Break
            """
            if exit: 
                self.wait_break_out = False
                return True
            
            stop = True
            
            if self.wait_break_out:
                stop = False
                check_current = [self.check_l(), self.check_m(), self.check_r()]
                if  check_current != self.history_check:
                    delayMicroseconds(self.time_delay_break_out)
                    self.wait_break_out = False
                    index = int(max(0, sign_steps))
                    reversed_index = int(not bool(index))
                    self.limit[check_right][reversed_index] = None
                    if (check_current[1] != self.history_check[1]) and not check_current[1]:
                        return_none = True
                        if check_current[2] and (not check_right): return_none = False
                        elif check_current[0] and check_right:  return_none = False
                        if return_none: self.limit[(not check_right)][reversed_index] = None
            else:
                if self.limit[check_right][0] == self.limit[check_right][1]:
                    stop = False
                    if self.check_r() and check_right:
                        index = int(max(0, sign_steps))
                        self.limit[check_right][index] = sign_steps
                        stop = True
                    elif self.check_l() and not check_right:
                        index = int(max(0, sign_steps))
                        self.limit[check_right][index] = sign_steps
                        stop = True
                    elif self.check_m():
                        index = int(max(0, sign_steps))
                        reversed_index = int(not bool(index))
                        self.limit[check_right][index] = sign_steps
                        self.limit[(not check_right)][reversed_index] = -sign_steps
                        stop = True
                elif not(sign_steps in self.limit[check_right]): 
                    stop = False
                    self.wait_break_out = True
                    self.history_check = [self.check_l(), self.check_m(), self.check_r()]
            
            return stop