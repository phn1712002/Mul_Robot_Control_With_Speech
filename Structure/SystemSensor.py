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
        self.check_m_firts_break = None
        self.flag_firts_break = True
        
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
            
            list_sw = [self.check_l(), self.check_r()]
            check_sw = bool(self.check_m() + list_sw[check_right])
            limit = self.limit[check_right]
            idx = int(max(sign_steps, 0))
            reversed_idx = int(not bool(idx))
            
            if self.wait_break_out:
                stop = False
                
                if self.flag_firts_break:
                    self.check_m_firts_break = self.check_m()
                    self.flag_firts_break = False
                    
                if not(check_sw): 
                    self.wait_break_out = False
                    self.flag_firts_break = True
                    self.limit[check_right][reversed_idx] = None
                    if self.check_m_firts_break != self.check_m() and not(self.check_m()):
                        if [self.check_l(), self.check_r()][not(check_right)]:
                            if self.limit[not(check_right)][idx] is None: pass
                            else: self.limit[not(check_right)][reversed_idx] = None
                        else:
                            self.limit[not(check_right)] = [None, None]
                    delayMicroseconds(self.time_delay_break_out)
            else:
                if check_sw:
                    if limit == [None, None]: 
                        stop = True
                        self.limit[check_right][idx] = sign_steps
                    elif sign_steps in limit: stop = True
                    elif not (sign_steps in limit):
                        self.wait_break_out = True
                        stop = False
                else: stop = False
                
                if self.check_m():
                    self.limit[not(check_right)][reversed_idx] = -sign_steps
                
            return stop