import numpy as np, keyboard as kb, time
from Tools.Excel import writeExcel
from Tools.CMD import clearCMD
from Tools.Image import saveImage, writeText
from Structure.Robot import Robot_V1

# Create all object
clearCMD()
PATH_CONFIG = 'config_driver.json'
PATH_DEBUG_IMAGE = './Dataset/Img_AngleBreak/'
PATH_EXCEL = './Dataset/Dataset_AngleBreak.xlsx'
rb = Robot_V1(PATH_CONFIG)
time_delay_steps = 0.5

# Loop
count = 0
while not kb.is_pressed('esc'):
    # Count id
    count +=1 
    
    # Create paramenter
    link = np.random.randint(low=1, high=3)
    angle_input = round(np.random.uniform(low=-180, high=180), 2)
    
    # Print info
    text_print = f"ID: {count} - Link: {link} - Angle Input: {angle_input} - Limit: {rb.multi_switch.limit_left} - {rb.multi_switch.limit_right}"
    text_print_image = f"Switch left:{rb.multi_switch.switch_left.checkClick()} - Switch mid:{rb.multi_switch.switch_mid.checkClick()} - Switch Right:{rb.multi_switch.switch_right.checkClick()}"
    print(text_print)
    
    # Save image
    image = rb.getFrameInCam()
    image = writeText(image=image, text=text_print, font_scale=0.5, position=(50 ,50), color='red')
    image = writeText(image=image, text=text_print_image, font_scale=0.5, position=(50 ,200), color='red')
    saveImage(directory=PATH_DEBUG_IMAGE, image=image)
    
    # q to continue
    #while not kb.is_pressed('q'): pass
    
    # Control RB
    angle_before_steps = rb.getAngleOneLink(index_link=link)
    angle_after_steps, in_progress_break = rb.controlOneLink(index_link=link, angle_or_oc=angle_input)
    
    # Save data to excel
    data_save = {
        'id': count,
        'link': link,
        'angle_before_steps': angle_before_steps,
        'angle_input': angle_input,
        'angle_after_steps': angle_after_steps,
        'in_progress_break': int(in_progress_break)
    }
    writeExcel(path=PATH_EXCEL, data=data_save)
    
    # Stop in time
    time.sleep(time_delay_steps)                