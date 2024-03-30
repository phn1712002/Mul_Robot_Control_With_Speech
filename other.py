import os
from Tools.CMD import clearCMD
from Structure.Robot import Robot_V1

#! CLEAN SYSTEM
os.system('pyclean .')
os.system('cls')
PATH_CONFIG_RB = './Config/config_RB_2.json'
rb = Robot_V1(PATH_CONFIG_RB)

while True:
  clearCMD()
  link = int(input("Input link:"))
  angle = float(input("Input Angle:"))
  print(rb.controlOneLink(link, angle))
  input()
  
  
  