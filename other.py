import os
from Tools.CMD import clearCMD
from Structure.Robot import Robot_V1

#! CLEAN SYSTEM
os.system('pyclean .')
os.system('cls')
PATH_CONFIG_RB = './Config/config_RB_1.json'
rb = Robot_V1(PATH_CONFIG_RB)

while True:
  #print(rb.multi_switch.check_l(), rb.multi_switch.check_m(), rb.multi_switch.check_r())
  clearCMD()
  link = int(input("Input link:"))
  angle = float(input("Input Angle:"))
  print(rb.controlOneLink(link, angle))
  input()
  
  
  