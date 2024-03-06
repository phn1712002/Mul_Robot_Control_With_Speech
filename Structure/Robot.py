import pyfirmata, os, threading, keyboard, re
from Device.Peripherals import Micro, Camera
from Tools.Json import loadJson, saveJson
from Tools.Folder import getFileWithPar
from pyfirmata import Arduino
from Device.Motor import Model_17HS3401, Model_MG90S
from .Arm import PickDropMechanism_V1
from .Base import Base_V1
from .Link import Link_V1
from .SystemSensor import MultiSwitch_V1
from Tools.Delay import delaySeconds
from ModelAI.Wav2Vec2.Architecture.Model import Wav2Vec2_tflite
from ModelAI.WaveUnet.Architecture.Model import WaveUnet_tflite

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
        #? Config board
        self.board = Arduino(self.config_board)
        pyfirmata.util.Iterator(self.board).start()

        #? Enable motor stepper in CNC V3
        self.ena_motor_pin = self.config_ena_motor['pin']
        self.ena_pin = self.board.get_pin(f'd:{self.ena_motor_pin}:o')
        self.ena_pin.write(self.config_ena_motor['input'])

        #? Config mutil switch 
        self.multi_switch = MultiSwitch_V1(board=self.board, 
                                           config_switch_right=self.config_switch_right,
                                           config_switch_left=self.config_switch_left,
                                           config_switch_2mid=self.config_switch_a_2motor, 
                                           **self.config_multi_switch)
        
        #? Config motor right
        self.motor_right = Model_17HS3401(board=self.board, **self.config_motor_right)

        #? Config smotor left
        self.motor_left = Model_17HS3401(board=self.board, **self.config_motor_left)
        
        #? Config motor mid
        self.motor_mid = Model_17HS3401(board=self.board, **self.config_motor_mid)

        #? Config motor arm
        self.motor_arm = Model_MG90S(board=self.board, **self.config_motor_arm)
        
        ###! Config structure robot ###
        
        #? Link_base
        self.link_base = Base_V1(motor=self.motor_mid, **self.config_link_base)
        
        #? Link_1
        self.link_1 = Link_V1(motor=self.motor_right, system_sensor=self.multi_switch, **self.config_link_1, right=True)
        
        #? Link_2
        self.link_2 = Link_V1(motor=self.motor_left, system_sensor=self.multi_switch, **self.config_link_2, right=False)

        #? Link_arm
        self.link_arm = PickDropMechanism_V1(motor=self.motor_arm, **self.config_link_arm)

        #? Check status start of Robot
        delaySeconds(1)
        if not self.checkStatusStart(): raise Exception("Please set the robot state to the starting position")
    
    def checkStatusStart(self):
        if self.multi_switch.switch_right.checkClick() and self.multi_switch.switch_left.checkClick() and not (self.multi_switch.switch_mid.checkClick()): return True
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
    
    def resetThreeAngle(self):
        x, y, z = self.getAngleThreeLink()
        return self.controlThreeLink(angle=(-x, -y, -z))

    def controlThreeLink(self, angle:tuple):
        output_link_base = self.link_base.step(angle=angle[0])
        output_link1 = self.link_1.step(angle=angle[1])
        output_link2 = self.link_2.step(angle[2])
        return output_link_base, output_link1, output_link2
    
    def getConfig(self, path=None):
        if not path is None: return saveJson(path=path, data=self.config)
        return self.config
    

class Mul_RB:
    def __init__(self, path_folder_config='./Config/', config_actions=False) -> None:
        self.path_folder_config = path_folder_config
        
        self.config_mrb = loadJson(getFileWithPar(path=path_folder_config, name_file='config_MRB.json')[0])
        self.config_model = self.config_mrb['model']
        self.config_mic = self.config_mrb['mic']
        self.config_cam =  self.config_mrb['cam']
        
        self.cam = Camera(**self.config_cam)
        self.mic = Micro(**self.config_mic)

        self.remove_noise = WaveUnet_tflite(**self.config_model['WaveUnet']).predict
        self.speech_to_text = Wav2Vec2_tflite(**self.config_model['Wav2Vec2']).predict
        self.format_text = self.__proccessText
        
        self.status_listen = threading.Thread(target=self.__thread_listen)
        self.status_control = threading.Thread(target=self.__thread_controlRB)
        
        self.run = False
        self.case_run = None
        if config_actions: self.configActions()
        self.ar_case_run = loadJson(getFileWithPar(path=path_folder_config, name_file='archive_case.json')[0])
        
        self.ar_mul_rb = self.__settingMulRB(path_folder_config=path_folder_config)
        self.list_name_rb = self.__getNameAllRB()
        
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
    
    def __nameToIdx(self, idx_or_name):
        if type(idx_or_name) == str:
            idx = self.list_name_rb[idx_or_name]
        elif type(idx_or_name) == int:
            idx = idx_or_name
        return idx
    
    def __idxToName(self, idx):
        return [name for name in self.list_name_rb.keys() if self.list_name_rb[name] == idx][0] 
            
    def __thread_listen(self):
        while self.run:
            audio = self.mic.getFrameToTensor()
            speech = self.remove_noise(audio)
            text = self.speech_to_text(speech)
            text = self.format_text(text)
            if text in self.ar_case_run:
                self.case_run = self.ar_case_run[text]
                
    def __thread_controlRB(self):
        while self.run:
            if self.case_run != None:
                for name, actions in self.case_run:
                    for link, angle in actions:
                        self.controlOneLink(name, link, angle)
        
    def __proccessText(self, string):
        special_chars_removed = re.sub(r"[^a-zA-Z0-9\s]", "", string)
        lowercase_string = special_chars_removed.lower()
        return lowercase_string
        
    def controlOneLink(self, idx_or_name, idx_link, angle):
        idx  = self.__nameToIdx(idx_or_name)
        return self.ar_mul_rb[idx].controlOneLink(idx_link, angle)

    
    def configActions(self):
        loop_mul_rb = True
        data_save_actions = {}
        
        while loop_mul_rb:
            os.system("cls")
            print("List all robot in multi:")
            for name, idx in self.list_name_rb:
                print(f"{idx}. Robot_{idx} - {name}")
            select = input("Please enter the name or index of the robot you want to select:")
            idx_rb = self.__nameToIdx(select)
            name_rb = self.__idxToName(idx_rb)
            
            loop_save_actions = True
            actions = []
            while loop_save_actions:
                os.system("cls")
                link = input("Please enter index of link:")
                angle = input("Please enter angle:")
                
                angle_after = self.ar_mul_rb[idx_rb].controlOneLink(link, angle)
                
                while True:
                    os.system("cls")
                    print(f"Robot_{idx_rb} name {name_rb} have input link_{link} with angle {angle} -> angle after {angle_after}")
                    select = input("Save (S) - Delete (D)")
                    if self.format_text(select) == 's':
                        actions.append([link, angle])
                        break
                    elif self.format_text(select) == 'd':
                        break
                    
                while True:
                    os.system("cls")
                    select = input("Continue save action (Y/N):")
                    if self.format_text(select) == 'y':
                        break
                    elif self.format_text(select) == 'n':
                        loop_save_actions = False
                        data_save_actions.update(name_rb, actions)
                        break
                
            while True:
                os.system("cls")
                select = input("Continue save action with robot other (Y/N):")
                if self.format_text(select) == 'y':
                    break
                elif self.format_text(select) == 'n':
                    loop_mul_rb = False
                    break
                
        return saveJson(self.path_folder_config + 'archive_case.json', data_save_actions)
    
    def runHandle(self):
        #? Start the flag
        self.run = True
        
        #? Start 2 theard
        self.status_listen.start()
        self.status_control.start()
        
        #? Wait
        print("Press ESC to terminate the program.")
        keyboard.wait('esc')

        #? End the flag
        self.run = False
        
        #? Wait 2 thread end task
        self.status_listen.join()
        self.status_control.join()
            
            
        
            
        
        
            