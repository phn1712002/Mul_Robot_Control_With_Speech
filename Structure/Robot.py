import pyfirmata, threading, re, math
from Device.Peripherals import Micro, Camera
from Tools.Json import loadJson, saveJson
from Tools.Folder import getFileWithPar
from pyfirmata import Arduino
from Device.Motor import Model_17HS3401, Model_MG90S
from .Arm import PickDropMechanism_V1
from .Base import Base_V1
from .Link import Link_V1
from .SystemSensor import MultiSwitch_V1
from Tools.Delay import delaySeconds, delayMicroseconds
from ModelAI.Wav2Vec2.Architecture.Model import Wav2Vec2_tflite
from ModelAI.WaveUnet.Architecture.Model import WaveUnet_tflite
from Tools import CMD

class  Robot_V1:
    def __init__(self, config_or_path):
        if type(config_or_path) == str:
            self.config = loadJson(config_or_path)
        else:
            self.config = config_or_path 
            
        ###  Get all config for device ###  
        self.config_board = self.config['board']
        self.config_name = self.config['name']
        self.angle_start = self.config['angle_start']
        self.skip_check = self.config['skip_check']
        
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
                                           config_switch_2mid=self.config_switch_a_2motor)
        
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
        if not self.skip_check: 
            if not self.checkStatusStart(): raise Exception("Please set the robot state to the starting position")
        if not(self.angle_start is None): self.statusStart(**self.angle_start, skip_check_sensor=self.skip_check)
        
    def statusStart(self, angle_1=50, angle_2=50, skip_check_sensor=False):
        return self.controlOneLink(1, angle_1, skip_check_sensor), self.controlOneLink(2, angle_2, skip_check_sensor)
        
    def checkStatusStart(self):
        if self.multi_switch.switch_right.checkClick() and self.multi_switch.switch_left.checkClick() and not (self.multi_switch.switch_mid.checkClick()): return True
        return False        
        
    def controlOneLink(self, index_link, angle_or_oc, skip_check_sensor=False):
        if index_link == 0:
            output = self.link_base.step(angle=angle_or_oc, skip_check_sensor=skip_check_sensor)
        elif index_link == 1:
            output = self.link_1.step(angle=angle_or_oc, skip_check_sensor=skip_check_sensor)
        elif index_link == 2:
            output = self.link_2.step(angle=angle_or_oc, skip_check_sensor=skip_check_sensor)
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

    def controlThreeLink(self, angle:tuple, skip_check_sensor=False):
        output_link_base = self.link_base.step(angle=angle[0], skip_check_sensor=skip_check_sensor)
        output_link1 = self.link_1.step(angle=angle[1], skip_check_sensor=skip_check_sensor)
        output_link2 = self.link_2.step(angle[2], skip_check_sensor=skip_check_sensor)
        return output_link_base, output_link1, output_link2
    
    def getConfig(self, path=None):
        if not path is None: return saveJson(path=path, data=self.config)
        return self.config
    

class Mul_RB:
    def __init__(self, path_folder_config='./Config/') -> None:
        self.path_folder_config = path_folder_config
        
        self.config_mrb = loadJson(getFileWithPar(path=path_folder_config, name_file='config_MRB.json')[0])
        self.config_model = self.config_mrb['model']
        self.config_mic = self.config_mrb['mic']
        self.config_cam =  self.config_mrb['cam']
        self.config_key =  self.config_mrb['key']
        self.count_robot_control = self.config_mrb['count_robot_control']
        self.delay_receiving_new_s = self.config_mrb['delay_receiving_new_s']
        
        self.cam = Camera(**self.config_cam, key_stop=self.config_key['key_stop'])
        self.mic = Micro(**self.config_mic, **self.config_key)

        self.remove_noise = WaveUnet_tflite(**self.config_model['WaveUnet']).build().predict
        self.speech_to_text = Wav2Vec2_tflite(**self.config_model['Wav2Vec2']).build().predict
        self.format_text = self.proccessText
        
        self.status_listen = threading.Thread(target=self.threadListen)
        self.status_control = threading.Thread(target=self.threadControlRB)
        self.status_monitor = threading.Thread(target=self.threadCam)
        self.delay_receiving_new_s_fn = lambda: delaySeconds(self.delay_receiving_new_s)
        
        self.run = False
        self.case_run = None
        self.case_current_name = None
        self.change_case = None
        self.ar_case_run = loadJson(getFileWithPar(path=path_folder_config, name_file='archive_case.json')[0])
        self.ar_mul_rb = self.settingMulRB(path_folder_config=path_folder_config)
        self.list_name_rb, self.check_control_mul = self.getNameAllRB()
        
        
    def settingMulRB(self, path_folder_config):
        ar_mul_rb = []
        all_path_config_rb = getFileWithPar(path=path_folder_config, name_file='config_RB_*.json')
        
        for path_config in all_path_config_rb:
            if self.count_robot_control == len(ar_mul_rb): break
            else: ar_mul_rb.append(Robot_V1(path_config))
        return ar_mul_rb
        
    def getNameAllRB(self):
        idx = 0
        dict_idx_name = {}
        check_control_mul = {}
        for rb in self.ar_mul_rb:
            dict_idx_name.update({idx:rb.config_name})
            check_control_mul.update({rb.config_name:False})
            idx += 1
        return dict_idx_name, check_control_mul
    
    def findRB(self, idx_or_name:str):
        idx_current = None
        name_current = None
        if idx_or_name in self.list_name_rb:
            idx_current = int(idx_or_name)
            name_current = self.list_name_rb[idx_current]
            return self.ar_mul_rb[idx_current], idx_current, name_current
        else:
            for idx, name in self.list_name_rb.items():
                if name == idx_or_name:
                    idx_current = idx
                    name_current = name
                    return self.ar_mul_rb[idx_current], idx_current, name_current
        return None, None, None
            
    def threadListen(self):
        while self.run:
            audio = self.mic.getFrameToTensor()
            self.change_case = False
            if not (audio is None):
                speech = self.remove_noise(audio)
                text = self.speech_to_text(speech)
                text = self.format_text(text)
                if text in self.ar_case_run:
                    self.case_run = self.ar_case_run[text]
                    self.case_current_name = text
                    self.change_case = True
    
    def funcControlMulRB(self, name, actions):
        self.check_control_mul[name] = True
        control = [self.controlOneLink(name, link, angle, time_delay, skip_check_sensor=True) for link, angle, time_delay in actions]
        self.check_control_mul[name] = False
    
    def threadControlRB(self):  
        list_thread_function_control = []
        while self.run:
            if self.case_run != None:
                is_not_empty = bool(self.case_run.items())
                if is_not_empty: 
                    for name, actions in self.case_run.items():
                        if name in list(self.list_name_rb.values()):  
                            #? System control all robot only time   
                            thread_function_control = threading.Thread(target=self.funcControlMulRB, args=(name, actions))
                            list_thread_function_control.append(thread_function_control)
                            thread_function_control.start()
                    #? Wait
                    wait_until_end_control = True    
                    while wait_until_end_control:
                        check = list(self.check_control_mul.values())
                        if not(True in check): 
                            for stop_thread in list_thread_function_control:
                                stop_thread.join()
                            wait_until_end_control = False
                        else: self.delay_receiving_new_s_fn() 
                else: self.delay_receiving_new_s_fn()  
            else: self.delay_receiving_new_s_fn()
        
    def threadCam(self):
        while self.run:
            if self.mic.rec_flag: text = f"Status current: {str(self.case_current_name)} - Recoding!"
            else: text = f"Status current: {str(self.case_current_name)}"
            frame = self.cam.getFrame() 
            frame = self.cam.writeText(frame=frame, 
                                       text=text,
                                       org=(100, 100))
            self.run = not(self.cam.liveView(frame))
        self.cam.close()
        
    def proccessText(self, string):
        trimmed_string = re.sub(r"\s+", " ", string)
        lowercase_string = trimmed_string.upper()
        return lowercase_string
        
    def controlOneLink(self, idx_or_name, idx_link, angle, time_delay, skip_check_sensor=False):
        delayMicroseconds(time_delay)
        rb_current, _, _ = self.findRB(idx_or_name) 
        if not (rb_current is None): return rb_current.controlOneLink(idx_link, angle, skip_check_sensor)
        else: return None

    def configActions(self):
        loop_mul_rb = True
        data_save_actions = {}
        
        while loop_mul_rb:
            CMD.clearCMD()
            print("List all robot in multi:")
            for idx, name in self.list_name_rb.items():
                print(f"{idx}. Robot_{idx} - {name}")
            select = self.format_text(input("Please enter the name or index of the robot you want to select:"))
            rb_current, idx_current, name_current = self.findRB(select)
            
            loop_save_actions = True
            actions = []
            while loop_save_actions:
                try:
                    CMD.clearCMD()
                    print("Link_0 - Base | Link_1 - Link right | Link_2 - Link left | Link_3 - Arm")
                    link = int(input("Please enter index of link (0 -> 3): "))
                    angle = float(input("Please enter angle (-:Left, +:Right): "))
                    angle_after, stop = rb_current.controlOneLink(link, angle)
                except KeyError: print(KeyError)
                
                while True:
                    CMD.clearCMD()
                    print(f"Robot_{idx_current} name {name_current} have input link_{link} with angle {angle} -> angle after {angle_after}")
                    time_stop = float(input("Please enter time stop of action current (Microseconds): "))
                    select = input("Save (S) - Delete (D) :")
                    if self.format_text(select) == 's':
                        if angle_after < 0 : angle_after = -math.floor(abs(angle_after))
                        else: angle_after = math.floor(angle_after)
                        actions.append([link, angle_after, time_stop])
                        break
                    elif self.format_text(select) == 'd':
                        break
                    
                while True:
                    CMD.clearCMD()
                    select = input(f"Continue save actions of robot_{idx_current} name {name_current} (Y/N):")
                    if self.format_text(select) == 'y':
                        break
                    elif self.format_text(select) == 'n':
                        loop_save_actions = False
                        data_save_actions.update({name_current: actions})
                        break
                
            while True:
                CMD.clearCMD()
                select = input("Continue save actions with robot other (Y/N): ")
                if self.format_text(select) == 'y':
                    break
                elif self.format_text(select) == 'n':
                    loop_mul_rb = False
                    break
                
        CMD.clearCMD()
        name_status = self.format_text(input("Name of status?: "))
        path_current = self.path_folder_config + 'archive_case.json'
        data_current = loadJson(path_current)     
        data_current.update({name_status: data_save_actions})
        
        return saveJson(path_current, data_current)
    
    def runHandle(self):
        #? Start the flag
        self.run = True
        
        #? Start 2 theard
        self.status_monitor.start()
        self.status_control.start()
        self.status_listen.start()
        
        #? Wait 2 thread end task
        self.status_monitor.join()
        self.status_control.join()
        self.status_listen.join()
        print("End task")
            
            
        
            
        
        
            