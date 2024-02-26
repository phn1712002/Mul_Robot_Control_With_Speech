from pyfirmata import Arduino
from Device.Switch import Switch, Model_2A, Model_2A_Analog
from Device.Components import ElectronicComponents
from Tools.Delay import delayMicroseconds, delaySeconds

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
         
        self.switch_right = Model_2A(board=board, **self.config_switch_right)
        self.switch_left = Model_2A(board=board, **self.config_switch_left)
        self.switch_mid = Model_2A_Analog(board=board, **self.config_switch_2mid)

        self.limit_left = [None, 1.0]
        self.limit_right = [None, 1.0]
        
        self.wait_break_out = False
        self.last_change_2motor = {
            'index':None, 
            'value':None
            } 
        
        self.last_value_del = {
            'del_value_change': False,
            'index':None, 
            'value':None,
            'change_2motor': None
            } 
        
        self.change_2motor = {
            'last_motor': None, 
            'change': False
            }
        
        
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
            
            # Return True if the limit is reached
            if check_right and None not in self.limit_right: return True
            if not check_right and None not in self.limit_left: return True
            
            # Get value of switch
            check_m = self.switch_mid.checkClick() 
            check_r = self.switch_right.checkClick()
            check_l = self.switch_left.checkClick()

            # Get index of limit
            index_check = int(max(sign_steps, 0))
            index_check_rev = int(max(-sign_steps, 0))

            # Get check in all switch
            if check_right: check = bool(check_m + check_r)
            else: check = bool(check_m + check_l)
            
            # If exit and wait break out no break angle small 
            if exit:
                if self.wait_break_out: 
                    self.wait_break_out = False
                    if check:
                    # Undo del value change
                        if self.last_value_del['del_value_change']:
                            if check_right: self.limit_left[int(self.last_value_del['index'])] = self.last_value_del['value']
                            else: self.limit_right[int(self.last_value_del['index'])] = self.last_value_del['value']
                            self.change_2motor = self.last_value_del['change_2motor']
                            self.last_value_del['index'] = None
                            self.last_value_del['value'] = None
                            self.last_value_del['del_value_change'] = False

                    else:
                        delaySeconds(self.time_delay_break_out)
                        if check_right: 
                            self.limit_right[index_check_rev] = None
                            if self.change_2motor['change']: 
                                self.limit_left[index_check] = None
                                self.change_2motor['last_motor'] = None
                                self.change_2motor['change'] = False
                            else: 
                                self.limit_left[index_check_rev] = None
                                if self.change_2motor['change']: 
                                    self.limit_right[index_check] = None
                                    self.change_2motor['last_motor'] = None
                                    self.change_2motor['change'] = False
                return True

            # Check if the motor is stuck
            del_value_change = False
            if self.change_2motor['change']:
                if self.change_2motor['last_motor'] == check_right: del_value_change = True
            
            # Check wait break out 
            if self.wait_break_out:
                if not check:
                    delaySeconds(self.time_delay_break_out)
                    self.wait_break_out = False
                    if check_right: 
                        self.limit_right[index_check_rev] = None
                        if self.change_2motor['change']: 
                            self.limit_left[index_check] = None
                            self.change_2motor['last_motor'] = None
                            self.change_2motor['change'] = False
                    else: 
                        self.limit_left[index_check_rev] = None
                        if self.change_2motor['change']: 
                            self.limit_right[index_check] = None
                            self.change_2motor['last_motor'] = None
                            self.change_2motor['change'] = False
                return False
            
            # Check break out and stop motor in limit   
            if check_right:
                if sign_steps in self.limit_right: return True
                elif -sign_steps in self.limit_right:
                    self.wait_break_out = True # Motor no stop in limit
                    # Delete value if no change motor steps
                    if del_value_change: 
                        # Save last value delete
                        self.last_value_del['del_value_change'] = del_value_change
                        self.last_value_del['index'] = int(self.last_change_2motor['index'])
                        self.last_value_del['value'] = self.limit_left[int(self.last_change_2motor['index'])]
                        self.last_value_del['change_2motor'] = self.change_2motor.copy()
                        # Delete value
                        self.limit_left[int(self.last_change_2motor['index'])] = self.last_change_2motor['value']
                        self.change_2motor['last_motor'] = None
                        self.change_2motor['change'] = False
                    return False
            else: 
                if sign_steps in self.limit_left: return True
                elif -sign_steps in self.limit_left:
                    self.wait_break_out = True # Motor no stop in limit
                    # Delete value if no change motor steps
                    if del_value_change:
                        # Save last value delete
                        self.last_value_del['del_value_change'] = del_value_change
                        self.last_value_del['index'] = int(self.last_change_2motor['index'])
                        self.last_value_del['value'] = self.limit_right[int(self.last_change_2motor['index'])]
                        self.last_value_del['change_2motor'] = self.change_2motor.copy()
                        # Delete value
                        self.limit_right[int(self.last_change_2motor['index'])] = self.last_change_2motor['value']
                        self.change_2motor['last_motor'] = None
                        self.change_2motor['change'] = False
                    return False

            # Add value to limit
            if check and not self.wait_break_out:
                if check_right: 
                    self.limit_right[index_check] = sign_steps 
                    # Check switch mid change 2 limit in 2 motor
                    if check_m:
                        self.change_2motor['last_motor'] = check_right
                        self.change_2motor['change'] = True
                        self.last_change_2motor['index'] = index_check_rev
                        self.last_change_2motor['value'] = self.limit_left[index_check_rev]
                        self.limit_left[index_check_rev] = -sign_steps
                else: 
                    self.limit_left[index_check] = sign_steps
                    # Check switch mid change 2 limit in 2 motor
                    if check_m:
                        self.change_2motor['last_motor'] = check_right
                        self.change_2motor['change'] = True
                        self.last_change_2motor['index'] = index_check_rev
                        self.last_change_2motor['value'] = self.limit_right[index_check_rev]
                        self.limit_right[index_check_rev] = -sign_steps
                return True