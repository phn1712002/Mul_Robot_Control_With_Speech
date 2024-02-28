import pyfirmata, os
from Device.Peripherals import Micro, Camera
from Tools.Json import loadJson, saveJson
from Tools.Folder import getFileWithPar
from pyfirmata import Arduino
from Device.Motor import Model_17HS3401, Model_MG90S
from .Arm import PickDropMechanism_V1
from .Base import Base_V1
from .Link import Link_V1
from .SystemSensor import MultiSwitch_V1

class  Robot_V1:
    def __init__(self, config_or_path):
        if config_or_path.__class__ is str:
            self.config = loadJson(config_or_path)
        else:
            self.config = config_or_path 
            
        ###  Get all config for device ###
        
        self.config_board = self.config['board']
        self.config_name = self.config['name']
        
        self.config_ena_motor = self.config['ena_motor']
        
        self.config_motor_mid = self.config['motor_mid']
        self.config_link_base = self.config['link_base']
        
        self.config_switch_a_2motor = self.config['switch_a_2motor']
        
        self.config_motor_left = self.config['motor_left']
        self.config_switch_left = self.config['switch_left']
        self.config_link_1 = self.config['link_1']
        
        self.config_motor_right = self.config['motor_right']
        self.config_switch_right = self.config['switch_right']
        self.config_link_2 = self.config['link_2']
        
        self.config_motor_arm = self.config['motor_arm'] 
        self.config_link_arm = self.config['link_arm']
        
        self.config_multi_switch = self.config['multi_switch']
        # Config board
        self.board = Arduino(self.config_board)
        pyfirmata.util.Iterator(self.board).start()

        # Enable motor stepper in CNC V3
        self.ena_motor_pin = self.config_ena_motor['pin']
        self.ena_pin = self.board.get_pin(f'd:{self.ena_motor_pin}:o')
        self.ena_pin.write(self.config_ena_motor['input'])

        # Config mutil switch 
        self.multi_switch = MultiSwitch_V1(board=self.board, 
                                           config_switch_right=self.config_switch_right,
                                           config_switch_left=self.config_switch_left,
                                           config_switch_2mid=self.config_switch_a_2motor, **self.config_multi_switch)
        
        # Config motor right
        self.motor_right = Model_17HS3401(board=self.board, **self.config_motor_right)

        # Config smotor left
        self.motor_left = Model_17HS3401(board=self.board, **self.config_motor_left)
        
        # Config motor mid
        self.motor_mid = Model_17HS3401(board=self.board, **self.config_motor_mid)

        # Config motor arm
        self.motor_arm = Model_MG90S(board=self.board, **self.config_motor_arm)
        
        ### Config structure robot ###
        
        # Link_base
        self.link_base = Base_V1(motor=self.motor_mid, **self.config_link_base)
        
        # Link_1
        self.link_1 = Link_V1(motor=self.motor_left, system_sensor=self.multi_switch, **self.config_link_1, right=False)
        
        # Link_2
        self.link_2 = Link_V1(motor=self.motor_right, system_sensor=self.multi_switch, **self.config_link_2, right=True)

        # Link_arm
        self.link_arm = PickDropMechanism_V1(motor=self.motor_arm, **self.config_link_arm)

        # Check status start of Robot 
        #if not self.checkStatusStart(): raise Exception("Please set the robot state to the starting position")
    
    def checkStatusStart(self):
        if self.multi_switch.switch_right.checkClick() and self.multi_switch.switch_left.checkClick(): return True
        return False        
        
    def controlOneLink(self, index_link, angle_or_oc):
        if index_link == 0:
            output = self.link_base.step(angle=angle_or_oc)
        elif index_link == 1:
            output = self.link_1.step(angle=angle_or_oc)
        elif index_link == 2:
            output = self.link_2.step(angle=angle_or_oc)
        elif index_link == 3:
            if angle_or_oc: output = self.link_arm.open()
            else: output = self.link_arm.close()
        return output

    def getAngleOneLink(self, index_link):
        if index_link == 0:
            angle = self.link_base.getAngle()
        elif index_link == 1:
            angle = self.link_1.getAngle()
        elif index_link == 2:
            angle = self.link_2.getAngle()
        return angle 
    
    def getAngleThreeLink(self):
        return self.link_base.getAngle(), self.link_1.getAngle(), self.link_2.getAngle()  
    
    def controlThreeLink(self, angle:tuple):
        output_link_base = self.link_base.step(angle=angle[0])
        output_link1 = self.link_1.step(angle=angle[1])
        output_link2 = self.link_2.step(angle[2])
        return output_link_base, output_link1, output_link2
    
    def getConfig(self, path=None):
        if not path is None: return saveJson(path=path, data=self.config)
        return self.config
    

class Mul_RB:
    def __init__(self, path_folder_config='./Config/') -> None:
        self.path_folder_config = path_folder_config
        
        self.config_mrb = loadJson(getFileWithPar(path=path_folder_config, name_file='config_MRB.json')[0])
        
        self.cam = Camera(self.config_mrb['cam'])
        self.mic = Micro(self.config_mrb['micro'])
        
        self.ar_mul_rb = self.__settingMulRB(path_folder_config=path_folder_config)
        self.list_name_rb, self.max_idx_rb = self.__getNameAllRB()
        
    def __settingMulRB(self, path_folder_config):
        ar_mul_rb = []
        all_path_config_rb = getFileWithPar(path=path_folder_config, name_file='config_RB_*.json')
        
        for path_config in all_path_config_rb:
            ar_mul_rb.append(Robot_V1(path_config))
        return ar_mul_rb
        
    def __getNameAllRB(self):
        idx = 0
        dict_idx_name = {}
        for rb in self.ar_mul_rb:
            dict_idx_name.update({idx:rb.config_name}) 
            idx += 1
        return dict_idx_name, idx
    
    def getAngleOneLink(self, idx_or_name, idx_link): pass 
    def getAngleThreeLink(self, idx_or_name, angle): pass